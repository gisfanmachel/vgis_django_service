#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : WebSocket 推送服务启动入口（示例）
#
#            新项目接入步骤：
#              1. 写自己的 data_provider：async fn(websocket, session) -> dict | None
#                 session.subscription 里是客户端订阅时带的业务字段
#              2. 需要新消息类型时用 server.register_handler 注册
#              3. 需要查库时用 server.db_pool（推荐 with server.db_pool as conn:）
#              4. 配置全部走 config.py 的同名环境变量，不要写死在代码里
# @Software: PyCharm
import asyncio
import logging

# 先导入 logger_setup：模块导入即完成日志初始化，后续模块才能正常打日志
from logger_setup import log_system_info

import config
from commonUtility import CommonHelper
from server import WebSocketServer, register_handler

logger = logging.getLogger("main")


# ======================================================================
# 1) 推送数据源：subscribe 之后按 interval 周期被调用
# ======================================================================
async def my_data_provider(websocket, session):
    """
    :param websocket: 客户端连接
    :param session:   ClientSession，session.subscription 是订阅时带的业务字段
    :return: 要推送的 dict；返回 None 表示本轮不推（如暂无新数据）
    """
    # 示例：把订阅参数原样回推。真实项目改成查库/查缓存。
    return {
        "type": "data",
        "time": CommonHelper.get_curent_time_str(),
        "subscription": session.subscription,
        "push_count": session.push_count,
    }

    # 查库示例：
    # if server.db_pool is None:
    #     return None
    # device_ids = session.subscription.get("device_ids") or []
    # if not device_ids:
    #     return None
    # rows = []
    # with server.db_pool as conn:
    #     with conn.cursor() as cur:
    #         for batch in CommonHelper.batch_list(device_ids, 500):
    #             placeholders = ",".join(["%s"] * len(batch))
    #             cur.execute(
    #                 "SELECT device_id, longitude, latitude, create_time "
    #                 "FROM your_location_table WHERE device_id IN ({}) ".format(placeholders),
    #                 batch,
    #             )
    #             rows.extend(cur.fetchall())
    # return {"type": "data", "items": rows}


# ======================================================================
# 2) 生命周期回调
# ======================================================================
async def on_connect(server, session):
    logger.info("客户端上线: %s", session.client_id)


async def on_disconnect(server, session):
    logger.info("客户端下线: %s，共收到 %s 条消息、推送 %s 次",
                session.client_id, session.message_count, session.push_count)


# ======================================================================
# 3) 业务自定义消息类型（按需保留）
# ======================================================================
@register_handler("echo")
async def handle_echo(server, websocket, session, message):
    """示例：原样回显，便于联调"""
    await CommonHelper.safe_send(websocket, {
        "type": "echo",
        "message": message,
    })


@register_handler("clients")
async def handle_clients(server, websocket, session, message):
    """示例：返回当前所有客户端会话"""
    async with server._session_lock:
        data = [s.to_dict() for s in server.sessions.values()]
    await CommonHelper.safe_send(websocket, {
        "type": "clients",
        "total": len(data),
        "info": data,
    })


# ======================================================================
# 4) 启动
# ======================================================================
def main():
    log_system_info()
    logger.info("%s", "=" * 60)
    logger.info("通用WebSocket推送服务启动 - 监听 %s:%s", config.WEB_SOCKET_HOST, config.WEB_SOCKET_PORT)
    logger.info("默认推送间隔: %s 秒，最大连接数: %s",
                config.WEB_SOCKET_BROADCAST_INTERVAL, config.MAX_DEVICE_NUM)
    logger.info("数据库: %s", "已启用" if config.DB_ENABLED else "未启用（DB_ENABLED=false）")
    logger.info("%s", "=" * 60)

    server = WebSocketServer(
        data_provider=my_data_provider,
        on_connect=on_connect,
        on_disconnect=on_disconnect,
    )
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("收到中断信号，服务已停止")
    except Exception as e:
        logger.error("服务运行错误: %s", e, exc_info=True)


if __name__ == "__main__":
    main()
