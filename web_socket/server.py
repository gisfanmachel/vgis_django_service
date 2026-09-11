#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 通用 WebSocket 推送服务器骨架
#
#            框架负责：连接注册与清理、消息 JSON 解析、按 type 分发到处理函数、
#                     每个客户端独立的定时推送任务、优雅关停、运行状态查询。
#            业务只需：写自己的推送数据源（data_provider）+ 按需注册消息处理函数。
#
#            示例：
#                async def my_provider(websocket, session):
#                    return {"type": "data", "items": [...]}   # 返回 None 表示本轮不推
#
#                server = WebSocketServer(data_provider=my_provider)
#                asyncio.run(server.start())
# @Software: PyCharm
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

import websockets

import config
from broadcast import ClientBroadcastTask
from commonUtility import CommonHelper
from db_pool import PgConnectionPool

logger = logging.getLogger(__name__)

# 消息处理函数注册表：msg_type -> async handler(server, websocket, session, message)
HANDLER_REGISTRY = {}


def register_handler(msg_type):
    """消息处理函数注册装饰器（业务用这个扩展协议）"""
    def decorator(func):
        HANDLER_REGISTRY[msg_type] = func
        return func
    return decorator


@dataclass
class ClientSession:
    """单个客户端的会话信息"""
    websocket: object
    client_id: str
    address: str = None
    connected_at: datetime = field(default_factory=datetime.now)
    last_message_at: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    push_count: int = 0
    user_id: object = None
    subscription: dict = field(default_factory=dict)  # 业务自定义的订阅信息
    broadcast_task: ClientBroadcastTask = None

    def touch(self):
        self.last_message_at = datetime.now()

    def to_dict(self):
        return {
            "client_id": self.client_id,
            "address": self.address,
            "user_id": self.user_id,
            "connected_at": self.connected_at.strftime("%Y-%m-%d %H:%M:%S"),
            "last_message_at": self.last_message_at.strftime("%Y-%m-%d %H:%M:%S"),
            "message_count": self.message_count,
            "push_count": self.push_count,
            "interval": self.broadcast_task.interval if self.broadcast_task else None,
            "pushing": bool(self.broadcast_task and self.broadcast_task.is_running),
            "subscription": self.subscription,
        }


class WebSocketServer:
    """通用 WebSocket 推送服务器"""

    def __init__(self, host=None, port=None, data_provider=None,
                 on_connect=None, on_disconnect=None, enable_db=None):
        """
        :param host: 监听地址，默认 config.WEB_SOCKET_HOST
        :param port: 监听端口，默认 config.WEB_SOCKET_PORT
        :param data_provider: 推送数据源 async fn(websocket, session) -> dict | None
                              subscribe 之后按 interval 周期调用；返回 None 表示本轮不推
        :param on_connect:    连接建立回调 async fn(server, session)
        :param on_disconnect: 连接断开回调 async fn(server, session)
        :param enable_db:     是否启用数据库连接池，默认取 config.DB_ENABLED
        """
        self.host = host or config.WEB_SOCKET_HOST
        self.port = port or config.WEB_SOCKET_PORT
        self.data_provider = data_provider
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect

        # websocket -> ClientSession
        self.sessions = {}
        self._session_lock = asyncio.Lock()

        self.started_at = None
        self.server = None
        self.stats = {
            "total_connections": 0,   # 累计接入的连接数
            "total_messages": 0,      # 累计收到的客户端消息数
            "total_pushes": 0,        # 累计推送次数
            "total_push_failed": 0,   # 累计推送失败次数
            "total_unknown_type": 0,  # 累计未知消息类型数
        }

        # 数据库连接池
        self.db_pool = None
        if enable_db is None:
            enable_db = config.DB_ENABLED
        if enable_db:
            self.db_pool = PgConnectionPool()

        logger.info("WebSocketServer 初始化 - 监听 %s:%s，数据库 %s",
                    self.host, self.port, "已启用" if self.db_pool else "未启用")

    # ==================================================================
    # 生命周期
    # ==================================================================
    async def start(self):
        """启动服务（阻塞直到连接关闭）"""
        self.started_at = datetime.now()
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            max_size=config.WEB_SOCKET_MAX_SIZE,
            ping_interval=config.WEB_SOCKET_PING_INTERVAL,
            ping_timeout=config.WEB_SOCKET_PING_TIMEOUT,
        )
        logger.info("WebSocket 服务已启动 ws://%s:%s", self.host, self.port)
        try:
            await self.server.wait_closed()
        finally:
            await self.cleanup_all_clients()

    async def cleanup_all_clients(self):
        """停止所有客户端推送任务并清空会话"""
        logger.info("正在清理所有客户端资源...")
        async with self._session_lock:
            tasks = [s.broadcast_task.stop() for s in self.sessions.values() if s.broadcast_task]
            self.sessions.clear()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        if self.db_pool:
            self.db_pool.close_all()
        logger.info("所有客户端资源已清理")

    # ==================================================================
    # 连接处理
    # ==================================================================
    async def handle_client(self, websocket):
        """单个客户端的生命周期：注册 → 收消息循环 → 清理"""
        if len(self.sessions) >= config.MAX_DEVICE_NUM:
            logger.warning("连接数已达上限 %s，拒绝新连接", config.MAX_DEVICE_NUM)
            await CommonHelper.safe_send(websocket, {
                "type": "error",
                "info": CommonHelper.get_local_str2("CLIENT_LIMIT_EXCEEDED", "CH"),
            })
            await websocket.close()
            return

        session = await self.register_client(websocket)
        try:
            async for raw_message in websocket:
                session.touch()
                session.message_count += 1
                self.stats["total_messages"] += 1

                message = self.parse_message(raw_message, session)
                if message is None:
                    continue

                await self.dispatch(websocket, session, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("客户端 %s 连接已关闭", session.client_id)
        except Exception as e:
            logger.error("处理客户端 %s 消息时出错: %s", session.client_id, e, exc_info=True)
        finally:
            await self.unregister_client(websocket)

    async def register_client(self, websocket):
        client_id = "{}#{}".format(websocket.remote_address[0], id(websocket)) \
            if websocket.remote_address else str(id(websocket))
        session = ClientSession(
            websocket=websocket,
            client_id=client_id,
            address="{}:{}".format(*websocket.remote_address) if websocket.remote_address else None,
        )
        async with self._session_lock:
            self.sessions[websocket] = session
        self.stats["total_connections"] += 1
        logger.info("客户端已连接: %s，当前在线 %s", session.client_id, len(self.sessions))

        if self.on_connect:
            try:
                await self.on_connect(self, session)
            except Exception as e:
                logger.error("on_connect 回调异常: %s", e, exc_info=True)
        return session

    async def unregister_client(self, websocket):
        session = self.sessions.get(websocket)
        if session is None:
            return
        # 先停推送任务再移除会话
        if session.broadcast_task:
            try:
                await session.broadcast_task.stop()
            except Exception as e:
                logger.error("停止客户端 %s 推送任务失败: %s", session.client_id, e)
        async with self._session_lock:
            self.sessions.pop(websocket, None)
        logger.info("客户端已断开: %s，当前在线 %s", session.client_id, len(self.sessions))

        if self.on_disconnect:
            try:
                await self.on_disconnect(self, session)
            except Exception as e:
                logger.error("on_disconnect 回调异常: %s", e, exc_info=True)

    # ==================================================================
    # 消息解析与分发
    # ==================================================================
    def parse_message(self, raw_message, session):
        """
        把收到的原始消息解析成 dict；解析失败返回 None（调用方直接跳过本条）。

        注意：这里是同步方法，不能 await 回消息；非法消息只记日志并计数，
        需要给客户端回执的话在调用处（handle_client）补。
        """
        try:
            if isinstance(raw_message, bytes):
                raw_message = raw_message.decode("utf-8")
            message = json.loads(raw_message)
            if not isinstance(message, dict):
                raise ValueError("消息必须是 JSON 对象")
            return message
        except Exception as e:
            logger.warning("客户端 %s 发来非法消息: %s", session.client_id, e)
            self.stats["total_unknown_type"] += 1
            return None

    async def dispatch(self, websocket, session, message):
        """按消息 type 分发；type 缺省时回落到 config 里的默认值（不设默认则报未知类型）"""
        msg_type = message.get("type") or message.get("action")
        if not msg_type:
            await CommonHelper.safe_send(websocket, {
                "type": "error",
                "info": CommonHelper.get_local_str("MISSING_REQUIRED_FIELD", message),
                "detail": "type",
            })
            return

        handler = HANDLER_REGISTRY.get(msg_type)
        if handler is None:
            self.stats["total_unknown_type"] += 1
            logger.warning("客户端 %s 发来未知消息类型: %s", session.client_id, msg_type)
            await CommonHelper.safe_send(websocket, {
                "type": "error",
                "info": CommonHelper.get_local_str("UNKNOWN_MESSAGE_TYPE", message),
                "detail": msg_type,
            })
            return

        try:
            await handler(self, websocket, session, message)
        except Exception as e:
            logger.error("处理消息 type=%s 失败 - 客户端 %s: %s",
                         msg_type, session.client_id, e, exc_info=True)
            await CommonHelper.safe_send(websocket, {
                "type": "error",
                "info": CommonHelper.get_local_str("HANDLE_CLIENT_MESSAGE_FAIL", message),
                "detail": str(e),
            })

    # ==================================================================
    # 推送
    # ==================================================================
    async def start_push(self, websocket, session, interval=None, task_type="realtime"):
        """为客户端启动周期推送任务（幂等：已在跑则只更新间隔）"""
        interval = CommonHelper.clamp_number(
            interval, config.MIN_BROADCAST_INTERVAL, config.MAX_BROADCAST_INTERVAL,
            config.WEB_SOCKET_BROADCAST_INTERVAL)

        if session.broadcast_task and session.broadcast_task.is_running:
            await session.broadcast_task.update_interval(interval)
            return session.broadcast_task

        if self.data_provider is None:
            raise RuntimeError("未配置 data_provider，无法启动推送")

        async def _provider(_websocket):
            payload = await self.data_provider(_websocket, session)
            if payload:
                session.push_count += 1
                self.stats["total_pushes"] += 1
            return payload

        session.broadcast_task = ClientBroadcastTask(
            websocket, interval=interval, callback=_provider, task_type=task_type)
        await session.broadcast_task.start()
        return session.broadcast_task

    async def stop_push(self, websocket, session):
        """停止客户端推送任务"""
        if session.broadcast_task:
            await session.broadcast_task.stop()
            session.broadcast_task = None

    async def send(self, websocket, payload):
        """向指定客户端发送 JSON"""
        return await CommonHelper.safe_send(websocket, payload)

    async def broadcast(self, payload):
        """向所有已连接客户端广播，返回成功数"""
        targets = list(self.sessions.keys())
        results = await asyncio.gather(
            *[CommonHelper.safe_send(ws, payload) for ws in targets],
            return_exceptions=True)
        return sum(1 for r in results if r is True)

    # ==================================================================
    # 状态
    # ==================================================================
    def get_status(self):
        return {
            "host": self.host,
            "port": self.port,
            "started_at": self.started_at.strftime("%Y-%m-%d %H:%M:%S") if self.started_at else None,
            "uptime_seconds": round((datetime.now() - self.started_at).total_seconds(), 1)
            if self.started_at else 0,
            "client_count": len(self.sessions),
            "max_device_num": config.MAX_DEVICE_NUM,
            "db_enabled": self.db_pool is not None,
            "stats": dict(self.stats),
            "registered_handlers": sorted(HANDLER_REGISTRY.keys()),
        }


# ======================================================================
# 框架内置消息处理函数
# ======================================================================
@register_handler("ping")
async def handle_ping(server, websocket, session, message):
    """心跳：客户端发 {"type":"ping"}，服务端回 pong"""
    await CommonHelper.safe_send(websocket, {
        "type": "pong",
        "time": CommonHelper.get_curent_time_str(),
    })


@register_handler("status")
async def handle_status(server, websocket, session, message):
    """客户端主动查询服务端状态"""
    await CommonHelper.safe_send(websocket, {
        "type": "status",
        "info": server.get_status(),
    })


@register_handler("subscribe")
async def handle_subscribe(server, websocket, session, message):
    """
    订阅推送。消息体：
        {"type": "subscribe", "interval": 1, "localization": "CH", ...业务字段}
    业务字段会整体存进 session.subscription，供 data_provider 取用
    """
    interval = message.get("interval", config.WEB_SOCKET_BROADCAST_INTERVAL)
    session.subscription = message

    try:
        await server.start_push(websocket, session, interval=interval)
    except Exception as e:
        logger.error("启动推送失败 - 客户端 %s: %s", session.client_id, e, exc_info=True)
        await CommonHelper.safe_send(websocket, {
            "type": "error",
            "info": CommonHelper.get_local_str("SUBSCRIBE_FAIL", message),
            "detail": str(e),
        })
        return

    await CommonHelper.safe_send(websocket, {
        "type": "subscribed",
        "info": CommonHelper.get_local_str("SUBSCRIBE_SUCCESS", message),
        "interval": session.broadcast_task.interval,
    })


@register_handler("unsubscribe")
async def handle_unsubscribe(server, websocket, session, message):
    """取消订阅"""
    await server.stop_push(websocket, session)
    session.subscription = {}
    await CommonHelper.safe_send(websocket, {
        "type": "unsubscribed",
        "info": CommonHelper.get_local_str("UNSUBSCRIBE_SUCCESS", message),
    })


@register_handler("set_interval")
async def handle_set_interval(server, websocket, session, message):
    """修改推送间隔。消息体：{"type":"set_interval", "interval": 2}"""
    raw_interval = message.get("interval")
    if raw_interval is None:
        await CommonHelper.safe_send(websocket, {
            "type": "error",
            "info": CommonHelper.get_local_str("MISSING_REQUIRED_FIELD", message),
            "detail": "interval",
        })
        return

    interval = CommonHelper.clamp_number(
        raw_interval, config.MIN_BROADCAST_INTERVAL, config.MAX_BROADCAST_INTERVAL, None)
    if interval is None:
        await CommonHelper.safe_send(websocket, {
            "type": "error",
            "info": CommonHelper.get_local_str("BROADCAST_INTERVAL_INVALID", message),
            "detail": raw_interval,
        })
        return

    if session.broadcast_task:
        await session.broadcast_task.update_interval(interval)

    await CommonHelper.safe_send(websocket, {
        "type": "interval_updated",
        "info": CommonHelper.get_local_str("BROADCAST_INTERVAL_UPDATED", message),
        "interval": interval,
    })
