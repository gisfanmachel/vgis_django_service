#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : WebSocket 服务器通用配置
#            所有配置均可通过同名环境变量覆盖，便于容器化部署（改配置不用改代码）
# @Software: PyCharm
import os


def _env(key, default, cast=str):
    """读环境变量并转换类型，未设置或转换失败时回落到默认值"""
    val = os.environ.get(key)
    if val is None or str(val).strip() == "":
        return default
    try:
        return cast(val)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# 服务监听
# ---------------------------------------------------------------------------
WEB_SOCKET_HOST = _env("WEB_SOCKET_HOST", "0.0.0.0")
WEB_SOCKET_PORT = _env("WEB_SOCKET_PORT", 8765, int)
# 单条消息大小上限（默认 8MB）
WEB_SOCKET_MAX_SIZE = _env("WEB_SOCKET_MAX_SIZE", 2 ** 23, int)
# 心跳：ping 间隔与超时（秒）
WEB_SOCKET_PING_INTERVAL = _env("WEB_SOCKET_PING_INTERVAL", 20, int)
WEB_SOCKET_PING_TIMEOUT = _env("WEB_SOCKET_PING_TIMEOUT", 60, int)

# 客户端数量上限，超过后拒绝新连接
MAX_DEVICE_NUM = _env("MAX_DEVICE_NUM", 1000, int)

# ---------------------------------------------------------------------------
# 数据推送
# ---------------------------------------------------------------------------
# 默认推送间隔（秒），客户端可在订阅时覆盖
WEB_SOCKET_BROADCAST_INTERVAL = _env("WEB_SOCKET_BROADCAST_INTERVAL", 1, float)
# 允许的最大推送间隔（秒），防止客户端上传超大值把服务拖垮
MAX_BROADCAST_INTERVAL = _env("MAX_BROADCAST_INTERVAL", 3600, float)
# 允许的最小推送间隔（秒），防止客户端上传 0 造成空转
MIN_BROADCAST_INTERVAL = _env("MIN_BROADCAST_INTERVAL", 0.05, float)

# ---------------------------------------------------------------------------
# 数据库（PostgreSQL 连接池）
# ---------------------------------------------------------------------------
DB_HOST = _env("DB_HOST", "127.0.0.1")
DB_PORT = _env("DB_PORT", 5432, int)
DB_NAME = _env("DB_NAME", "postgres")
DB_USER = _env("DB_USER", "postgres")
DB_PASSWORD = _env("DB_PASSWORD", "")
DB_CONNECT_TIMEOUT = _env("DB_CONNECT_TIMEOUT", 10, int)
DB_POOL_MIN_CONNECTIONS = _env("DB_POOL_MIN_CONNECTIONS", 1, int)
DB_POOL_MAX_CONNECTIONS = _env("DB_POOL_MAX_CONNECTIONS", 10, int)
# 是否启用数据库连接池（纯转发/内存数据场景置 False）
DB_ENABLED = _env("DB_ENABLED", "false").lower() in ("1", "true", "yes", "是")

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
LOG_DIR = _env("LOG_DIR", "logs")
LOG_MAIN_FILE = _env("LOG_MAIN_FILE", "web_socket_server.log")
LOG_ERROR_FILE = _env("LOG_ERROR_FILE", "error.log")
LOG_DEBUG_FILE = _env("LOG_DEBUG_FILE", "debug.log")
LOG_PACKET_FILE = _env("LOG_PACKET_FILE", "packets.log")
LOG_MAX_SIZE_MB = _env("LOG_MAX_SIZE_MB", 30, int)
LOG_BACKUP_COUNT = _env("LOG_BACKUP_COUNT", 10, int)
LOG_LEVEL = _env("LOG_LEVEL", "INFO")
LOG_TO_CONSOLE = _env("LOG_TO_CONSOLE", "true").lower() in ("1", "true", "yes", "是")

# ---------------------------------------------------------------------------
# 多语言
# ---------------------------------------------------------------------------
LOCAL_KEY = "Localization"  # JSON 消息里的语言标识字段名，取值为 CH / EN
