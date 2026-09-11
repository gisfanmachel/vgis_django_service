#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : TCP 服务器通用配置
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
TCP_SERVER_HOST = _env("TCP_SERVER_HOST", "0.0.0.0")
TCP_SERVER_PORT = _env("TCP_SERVER_PORT", 3869, int)
# 最大等待连接数（listen backlog）
TCP_CLIENT_MAX_NUMBERS = _env("TCP_CLIENT_MAX_NUMBERS", 1000, int)

# ---------------------------------------------------------------------------
# socket 收发
# ---------------------------------------------------------------------------
# 单次 recv 最大字节数。串口透传/4G 模块场景报文可能被拼成超长串，按需调大
REC_MAX_BYTES = _env("REC_MAX_BYTES", 65535, int)
# 单次 recv 超时（秒），超时后继续循环等待，不视为断开
RECV_TIMEOUT_SECONDS = _env("RECV_TIMEOUT_SECONDS", 30, int)
# 服务端 socket 接收缓冲区大小
RECV_BUFFER_SIZE = _env("RECV_BUFFER_SIZE", 65536, int)
# TCP 保活参数（秒）
SOCKET_KEEPIDLE = _env("SOCKET_KEEPIDLE", 60, int)
SOCKET_KEEPINTVL = _env("SOCKET_KEEPINTVL", 10, int)
SOCKET_KEEPCNT = _env("SOCKET_KEEPCNT", 3, int)

# ---------------------------------------------------------------------------
# 连接管理
# ---------------------------------------------------------------------------
MAX_CONNECTION_HOURS = _env("MAX_CONNECTION_HOURS", 3, int)  # 单连接最长存活时间
MAX_IDLE_SECONDS = _env("MAX_IDLE_SECONDS", 300, int)  # 最大空闲时间
MONITOR_INTERVAL_SECONDS = _env("MONITOR_INTERVAL_SECONDS", 60, int)  # 监控线程轮询间隔
MAX_RECONNECT_ATTEMPTS = _env("MAX_RECONNECT_ATTEMPTS", 3, int)  # 最大重连尝试次数
RECONNECT_TIMEOUT = _env("RECONNECT_TIMEOUT", 5, int)  # 重连超时（秒）

# ---------------------------------------------------------------------------
# 数据包处理
# ---------------------------------------------------------------------------
MAX_PACKET_QUEUE_SIZE = _env("MAX_PACKET_QUEUE_SIZE", 10000, int)  # 数据包队列上限
DATA_PROCESSOR_THREADS = _env("DATA_PROCESSOR_THREADS", 4, int)  # 队列消费线程数
THREAD_POOL_SIZE = _env("THREAD_POOL_SIZE", 50, int)  # 实际处理数据包的线程池大小

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
# 是否启用数据库连接池（无 DB 依赖的服务置 False）
DB_ENABLED = _env("DB_ENABLED", "false").lower() in ("1", "true", "yes", "是")

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
LOG_DIR = _env("LOG_DIR", "logs")
LOG_MAIN_FILE = _env("LOG_MAIN_FILE", "tcp_server.log")
LOG_ERROR_FILE = _env("LOG_ERROR_FILE", "error.log")
LOG_DEBUG_FILE = _env("LOG_DEBUG_FILE", "debug.log")
LOG_PACKET_FILE = _env("LOG_PACKET_FILE", "packets.log")
LOG_MAX_SIZE_MB = _env("LOG_MAX_SIZE_MB", 30, int)
LOG_BACKUP_COUNT = _env("LOG_BACKUP_COUNT", 10, int)
LOG_LEVEL = _env("LOG_LEVEL", "INFO")
LOG_TO_CONSOLE = _env("LOG_TO_CONSOLE", "true").lower() in ("1", "true", "yes", "是")

# ---------------------------------------------------------------------------
# Web 控制/监控接口（Flask）
# ---------------------------------------------------------------------------
WEB_API_ENABLED = _env("WEB_API_ENABLED", "true").lower() in ("1", "true", "yes", "是")
WEB_API_HOST = _env("WEB_API_HOST", "0.0.0.0")
WEB_API_PORT = _env("WEB_API_PORT", 5001, int)
WEB_API_DEBUG = _env("WEB_API_DEBUG", "false").lower() in ("1", "true", "yes", "是")

# 文件上传
UPLOAD_FOLDER = _env("UPLOAD_FOLDER", "static/upload")
ALLOWED_EXTENSIONS = {"bin"}  # 允许上传的文件扩展名
MAX_CONTENT_LENGTH = _env("MAX_CONTENT_LENGTH", 500 * 1024, int)  # 500KB

# ---------------------------------------------------------------------------
# 多语言
# ---------------------------------------------------------------------------
LOCAL_KEY = "Localization"  # 请求头/表单里的语言标识字段名，取值为 CH / EN
