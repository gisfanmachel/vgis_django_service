# 通用 WebSocket 推送服务器框架

从「无人机陆基项目 / WebSocket 推送服务」抽取的通用骨架。框架只负责连接管理、
消息分发与定时推送，数据来源与业务消息由使用方实现，配置全部走环境变量。

## 1. 文件说明

| 文件 | 职责 |
|---|---|
| `config.py` | 全部配置项，均可用同名环境变量覆盖 |
| `logger_setup.py` | 日志初始化（主日志/错误日志/控制台，按大小轮转 + 定期清理备份） |
| `db_pool.py` | PostgreSQL 连接池：取连接重试 + 健康检查（`SELECT 1`）+ 池自动重建 |
| `broadcast.py` | `ClientBroadcastTask`：单客户端定时推送任务（启动/停止/改频率） |
| `server.py` | `WebSocketServer` 骨架 + `ClientSession` + 消息处理函数注册表 + 内置 handler |
| `commonUtility.py` | 多语言取词、数值收敛、分批、安全发送等通用工具 |
| `localization_enum.py` | 中英文提示语字典（每条必须是 `<KEY>_CH` / `<KEY>_EN` 成对） |
| `snowflake_id_util.py` | 雪花ID |
| `main.py` | 启动入口 + data_provider 示例 + 自定义消息类型示例 |
| `test_client.py` | 测试客户端（订阅/收推送/改频率/取消订阅/心跳/未知类型） |
| `check_localization_keys.py` | 多语言自检脚本 |

## 2. 快速开始

```bash
pip install -r requirements.txt

# 启动服务（默认 0.0.0.0:8765）
python main.py

# 另开一个终端跑测试客户端
python test_client.py ws://127.0.0.1:8765
```

## 3. 客户端协议

所有消息都是 JSON 对象，用 `type` 字段区分（也兼容 `action`）。

### 3.1 框架内置消息类型

| type | 请求体 | 响应 |
|---|---|---|
| `ping` | `{}` | `{"type":"pong","time":...}` |
| `status` | `{}` | `{"type":"status","info":{运行状态}}` |
| `subscribe` | `{"interval":1, ...业务字段}` | `{"type":"subscribed","interval":1}` |
| `unsubscribe` | `{}` | `{"type":"unsubscribed"}` |
| `set_interval` | `{"interval":2}` | `{"type":"interval_updated","interval":2}` |

- `subscribe` 里的**业务字段会整体存进 `session.subscription`**，`data_provider` 直接取用，
  例如 `{"type":"subscribe","interval":1,"device_ids":[1,2,3],"service":"realPosition"}`。
- `interval` 会被收敛到 `[MIN_BROADCAST_INTERVAL, MAX_BROADCAST_INTERVAL]`，非法值直接报错。
- 未知 `type` 会回 `{"type":"error","info":"未知的消息类型","detail":"..."}`。
- 多语言：消息体里带 `"localization": "EN"` 即可让提示语变英文，缺省 CH。

### 3.2 服务端推送格式

由你的 `data_provider` 决定。约定返回一个 dict，框架原样 JSON 序列化后推送；
返回 `None` 或空 dict 表示本轮不推。

## 4. 业务怎么接进来

```python
async def my_provider(websocket, session):
    """按 interval 周期被调用；返回 None 表示本轮不推"""
    device_ids = session.subscription.get("device_ids") or []
    if not device_ids:
        return None
    return {"type": "data", "items": query_from_db(device_ids)}

server = WebSocketServer(
    data_provider=my_provider,
    on_connect=on_connect,        # async fn(server, session)
    on_disconnect=on_disconnect,  # async fn(server, session)
)
asyncio.run(server.start())
```

- 查库：`server.db_pool`，推荐 `with server.db_pool as conn:`（自动归还，异常自动回滚）
- 主动推给某个客户端：`await server.send(websocket, payload)`
- 广播：`await server.broadcast(payload)`
- 手动控制推送：`await server.start_push(websocket, session, interval)` / `await server.stop_push(...)`

### 新增消息类型

```python
from server import register_handler

@register_handler("query_history")
async def handle_query_history(server, websocket, session, message):
    start_time = message.get("start_time")
    # ... 查库
    await server.send(websocket, {"type": "history", "items": rows})
```

## 5. 配置（环境变量）

| 变量 | 默认 | 说明 |
|---|---|---|
| `WEB_SOCKET_HOST` / `WEB_SOCKET_PORT` | `0.0.0.0` / `8765` | 监听地址端口 |
| `WEB_SOCKET_MAX_SIZE` | `8388608` | 单条消息大小上限（字节） |
| `WEB_SOCKET_PING_INTERVAL` / `WEB_SOCKET_PING_TIMEOUT` | `20` / `60` | 心跳间隔与超时（秒） |
| `MAX_DEVICE_NUM` | `1000` | 客户端数量上限，超过拒绝新连接 |
| `WEB_SOCKET_BROADCAST_INTERVAL` | `1` | 默认推送间隔（秒） |
| `MIN_BROADCAST_INTERVAL` / `MAX_BROADCAST_INTERVAL` | `0.05` / `3600` | 间隔收敛范围，防客户端传 0 或超大值 |
| `DB_ENABLED` | `false` | 是否启用数据库连接池 |
| `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | — | 数据库连接 |
| `DB_POOL_MIN_CONNECTIONS` / `DB_POOL_MAX_CONNECTIONS` | `1` / `10` | 连接池大小 |
| `LOG_DIR` / `LOG_LEVEL` / `LOG_MAX_SIZE_MB` / `LOG_BACKUP_COUNT` / `LOG_TO_CONSOLE` | `logs` / `INFO` / `30` / `10` / `true` | 日志 |

> 配置文件里不写任何真实密码，部署时通过环境变量注入。

## 6. 多语言

语言标识来自消息体的 `localization` 字段（WebSocket 没有 HTTP header）。

- `CommonHelper.get_local_str("KEY", message)` —— 取提示语
- `CommonHelper.get_local_flag(message)` —— 只取语言标识
- `CommonHelper.get_local_str2("KEY", local)` —— 已知语言标识

新增提示语必须 `<KEY>_CH` / `<KEY>_EN` 成对，然后自检：

```bash
python check_localization_keys.py   # 退出码 0 表示通过
```

## 7. 部署

```bash
sudo docker build -t vgis_websocket_img:v1.0 .
docker save -o vgis_websocket_img_v1.0.tar vgis_websocket_img:v1.0

docker run -d --name web_socket \
  -p 8765:8765 \
  -e WEB_SOCKET_PORT=8765 \
  -e DB_ENABLED=true -e DB_HOST=your.db.host -e DB_PASSWORD=xxx \
  -v /data/logs:/var/backend/web_socket_server/logs \
  vgis_websocket_img:v1.0
```

> 生产环境建议在前面挂 nginx 做 TLS 终止与转发（`proxy_set_header Upgrade $http_upgrade;`）。

## 8. 已知注意事项

- 推送任务与客户端连接一一对应，连接断开时 `unregister_client` 会先停任务再移除会话，
  不会留下孤儿 asyncio 任务。
- `set_interval` 通过 `asyncio.Event` 唤醒正在 sleep 的推送循环，**新间隔立即生效**，
  不需要等当前这一轮睡完。
- `data_provider` 里抛异常不会终止推送任务，框架会记 ERROR 日志并短暂等待后继续；
  但**连续抛异常会造成日志刷屏**，业务侧建议自己 catch 并做降级。
- 客户端数量超过 `MAX_DEVICE_NUM` 时新连接会被拒（回一条 error 后 close）。
