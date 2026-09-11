# 通用 TCP 长连接服务器框架

从「无人机陆基项目 / 北斗 TCP 服务」抽取的通用骨架。框架只负责连接与调度，
报文协议由使用方实现，配置全部走环境变量。

## 1. 文件说明

| 文件 | 职责 |
|---|---|
| `config.py` | 全部配置项，均可用同名环境变量覆盖 |
| `logger_setup.py` | 日志初始化（主日志/错误日志/控制台，按大小轮转 + 定期清理备份） |
| `db_pool.py` | PostgreSQL 连接池：取连接重试 + 健康检查（`SELECT 1`）+ 池自动重建 |
| `connection.py` | `ConnectionStatus` / `ConnectionInfo`（连接信息与统计）/ `Packet`（已解析报文） |
| `protocol.py` | **协议抽象层**：`ProtocolHandler` 基类 + 通用拆包 + `LengthPrefixedProtocol` + `DemoProtocol` 示例 |
| `server.py` | `TCPServer` 骨架：accept / 每连接收包线程 / 拆包入队 / 线程池消费 / 连接监控 / 重连 / 优雅关停 |
| `web_api.py` | Flask 控制/监控接口 + 业务指令注册表 |
| `commonUtility.py` | 多语言取词、文件、时间等通用工具 |
| `localization_enum.py` | 中英文提示语字典（每条必须是 `<KEY>_CH` / `<KEY>_EN` 成对） |
| `snowflake_id_util.py` | 雪花ID |
| `main.py` | 启动入口 + 业务回调示例 + 指令注册示例 |
| `test_client.py` | 测试客户端（含**半包**与**粘包**用例） |
| `check_localization_keys.py` | 多语言自检脚本 |

## 2. 快速开始

```bash
pip install -r requirements.txt

# 启动服务（默认 0.0.0.0:3869，Web 控制接口 5001）
python main.py

# 另开一个终端跑测试客户端
python test_client.py 127.0.0.1 3869
```

## 3. 如何接入自己的协议

框架已实现粘包/半包处理，你只需要描述**包头布局**。

### 3.1 最常见的「帧头 + 长度字段」

```python
from protocol import FrameSpec, LengthPrefixedProtocol

# 包头 = 帧头(2) | 载荷长度(2,大端) | 设备ID(4) | 报文ID(1)
spec = FrameSpec(
    header=b"\xa0\xa1",
    header_len=9,
    length_offset=2, length_size=2,      # 载荷长度（不含包头）
    device_id_offset=4, device_id_size=4,
    msg_id_offset=8, msg_id_size=1,
)
protocol = LengthPrefixedProtocol(spec)
```

### 3.2 需要 BCC 校验和自定义解析

继承后重写 `verify()` / `parse()` / `build()` 三个钩子（拆包不用管）：

```python
from protocol import LengthPrefixedProtocol

class MyProtocol(LengthPrefixedProtocol):
    def verify(self, packet: bytes) -> bool:
        ...   # 返回 False 的报文会被丢弃并计入 total_parse_failed

    def parse(self, packet: bytes):
        ...   # 返回值会放进 Packet.parsed，业务回调里取用

    def build(self, msg_id, payload=b"", **kwargs) -> bytes:
        ...   # 组下行报文
```

`DemoProtocol` 就是一个完整可跑的参考实现，照它改即可。

## 4. 业务怎么接进来

```python
server = TCPServer(
    protocol=MyProtocol(),
    on_packet=on_packet,                        # 收到完整报文
    on_client_connected=on_client_connected,    # 连接建立
    on_client_disconnected=on_client_disconnected,  # 连接断开
)
server.start()   # 阻塞运行
```

- `on_packet(packet, conn_info, server)`：`packet` 有 `device_id` / `device_type` / `msg_id` / `parsed` / `raw`
- 要用数据库：`server.db_pool`，推荐 `with server.db_pool as conn:`（自动归还，异常自动回滚）
- 下发数据：`server.send_to_client(client_id, raw)` / `server.send_to_device(device_id, raw)` / `server.broadcast_to_all(raw)`

## 5. Web 控制/监控接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/server_status` | 运行状态、统计、队列长度 |
| GET | `/connections` | 当前连接明细 |
| GET | `/protocol/msg_types` | 协议支持的报文类型 |
| GET | `/log_info` | 日志文件列表 |
| GET | `/download_log/<filename>` | 下载日志（限制在日志目录内） |
| POST | `/upload` | 上传文件（默认只允许 `.bin`） |
| POST | `/send` | 向指定连接/设备发数据 `{"client_id"|"device_id", "hex"}` |
| POST | `/broadcast` | 广播 `{"hex"}` |
| GET | `/commands` | 列出已注册的业务指令 |
| POST | `/command/<name>` | 执行业务指令，请求体原样传给 handler |

注册业务指令（如参数查询/系统复位/固件升级）：

```python
from web_api import register_command

@register_command("system_reset")
def handle_system_reset(server, payload):
    raw = server.protocol.build(msg_id=0x21, payload=b"", device_id=payload["device_id"])
    server.send_to_device(payload["device_id"], raw)
    return {"success": True, "info": "复位指令已下发"}
```

## 6. 配置（环境变量）

| 变量 | 默认 | 说明 |
|---|---|---|
| `TCP_SERVER_HOST` / `TCP_SERVER_PORT` | `0.0.0.0` / `3869` | 监听地址端口 |
| `TCP_CLIENT_MAX_NUMBERS` | `1000` | listen backlog |
| `REC_MAX_BYTES` / `RECV_TIMEOUT_SECONDS` | `65535` / `30` | 单次 recv 上限 / 超时（超时不代表断开） |
| `MAX_CONNECTION_HOURS` / `MAX_IDLE_SECONDS` | `3` / `300` | 强制断开阈值 |
| `MONITOR_INTERVAL_SECONDS` | `60` | 监控轮询间隔 |
| `MAX_RECONNECT_ATTEMPTS` / `RECONNECT_TIMEOUT` | `3` / `5` | 重连策略 |
| `DATA_PROCESSOR_THREADS` / `THREAD_POOL_SIZE` | `4` / `50` | 队列消费线程 / 处理线程池 |
| `DB_ENABLED` | `false` | 是否启用数据库连接池 |
| `DB_HOST` / `DB_PORT` / `DB_NAME` / `DB_USER` / `DB_PASSWORD` | — | 数据库连接 |
| `DB_POOL_MIN_CONNECTIONS` / `DB_POOL_MAX_CONNECTIONS` | `1` / `10` | 连接池大小 |
| `LOG_DIR` / `LOG_LEVEL` / `LOG_MAX_SIZE_MB` / `LOG_BACKUP_COUNT` / `LOG_TO_CONSOLE` | `logs` / `INFO` / `30` / `10` / `true` | 日志 |
| `WEB_API_ENABLED` / `WEB_API_HOST` / `WEB_API_PORT` | `true` / `0.0.0.0` / `5001` | Web 控制接口 |
| `UPLOAD_FOLDER` / `MAX_CONTENT_LENGTH` | `static/upload` / 500KB | 上传 |

> 配置文件里不写任何真实密码，部署时通过环境变量注入。

## 7. 多语言

请求头 `Localization: CH / EN`（JSON 接口也可用 body 里的 `localization` 字段）。

- `CommonHelper.get_local_str("KEY", request)` —— 从请求头
- `CommonHelper.get_local_str3("KEY", request)` —— 从 JSON body
- `CommonHelper.get_local_str4("KEY", request)` —— 从表单
- `CommonHelper.get_local_str2("KEY", local)` —— 已知语言标识

新增提示语必须 `<KEY>_CH` / `<KEY>_EN` 成对，然后自检：

```bash
python check_localization_keys.py   # 退出码 0 表示通过
```

## 8. 部署

```bash
sudo docker build -t vgis_tcpserver_img:v1.0 .
docker save -o vgis_tcpserver_img_v1.0.tar vgis_tcpserver_img:v1.0

docker run -d --name tcp_server \
  -p 3869:3869 -p 5001:5001 \
  -e TCP_SERVER_PORT=3869 \
  -e DB_ENABLED=true -e DB_HOST=your.db.host -e DB_PASSWORD=xxx \
  -v /data/logs:/var/backend/tcp_server/logs \
  vgis_tcpserver_img:v1.0
```

## 9. 已知注意事项

- `RECV_TIMEOUT_SECONDS` 触发只表示「这段时间没收到数据」，框架会继续等待，**不会**断开连接；
  真正判定掉线靠 TCP 保活 + 监控线程的 `MAX_IDLE_SECONDS`。
- 队列满（`MAX_PACKET_QUEUE_SIZE`）时**丢弃**新到报文并打 ERROR 日志，不会阻塞收包线程。
- 校验失败（`verify()` 返回 False）或解析抛异常的报文会被丢弃并计入 `stats.total_parse_failed`。
- 异常断开的连接会进入重连流程，超过 `MAX_RECONNECT_ATTEMPTS` 才彻底清理；正常断开直接清理。
