#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 日志初始化（主日志/错误日志/控制台，按大小轮转 + 定期清理旧备份）
#            优先使用 concurrent-log-handler 以支持多进程/多线程并发写；
#            未安装时自动回落到标准库 RotatingFileHandler
# @Software: PyCharm
import logging
import os
import platform
import sys

import config

try:
    from cloghandler import ConcurrentRotatingFileHandler as RotatingFileHandler

    HAS_CONCURRENT_HANDLER = True
except ImportError:
    from logging.handlers import RotatingFileHandler

    HAS_CONCURRENT_HANDLER = False

LOG_DIR = config.LOG_DIR
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


class LogConfig:
    """日志相关配置（实际取值来自 config.py）"""
    MAIN_LOG_FILE = os.path.join(LOG_DIR, config.LOG_MAIN_FILE)
    ERROR_LOG_FILE = os.path.join(LOG_DIR, config.LOG_ERROR_FILE)
    DEBUG_LOG_FILE = os.path.join(LOG_DIR, config.LOG_DEBUG_FILE)
    PACKET_LOG_FILE = os.path.join(LOG_DIR, config.LOG_PACKET_FILE)

    MAX_LOG_SIZE = config.LOG_MAX_SIZE_MB * 1024 * 1024
    BACKUP_COUNT = config.LOG_BACKUP_COUNT
    ENCODING = "utf-8"

    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(filename)s:%(lineno)d - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def create_rotating_handler(filename, max_bytes=None, backup_count=None, level=logging.INFO):
    """创建按大小轮转的文件处理器，创建失败时回落到普通 FileHandler"""
    max_bytes = max_bytes or LogConfig.MAX_LOG_SIZE
    backup_count = backup_count or LogConfig.BACKUP_COUNT
    try:
        handler = RotatingFileHandler(
            filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=LogConfig.ENCODING,
        )
        handler.setLevel(level)
        return handler
    except Exception as e:
        print("创建日志处理器失败: {}，回落到 FileHandler".format(e))
        handler = logging.FileHandler(filename, encoding=LogConfig.ENCODING)
        handler.setLevel(level)
        return handler


def cleanup_old_logs(max_backup_count=None, log_dir=None, prefix=None):
    """清理超出备份数量的旧日志文件（按修改时间倒序保留最新的 N 个）"""
    max_backup_count = max_backup_count or LogConfig.BACKUP_COUNT
    log_dir = log_dir or LOG_DIR
    prefix = prefix or config.LOG_MAIN_FILE
    try:
        log_files = [
            os.path.join(log_dir, f)
            for f in os.listdir(log_dir)
            if f.startswith(prefix)
        ]
        log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        for old_log in log_files[max_backup_count:]:
            try:
                os.remove(old_log)
                logging.getLogger(__name__).info("清理旧日志文件: %s", old_log)
            except Exception as e:
                logging.getLogger(__name__).error("清理日志文件失败 %s: %s", old_log, e)
    except Exception as e:
        logging.getLogger(__name__).error("清理旧日志时出错: %s", e)


def log_system_info():
    """记录运行环境信息，便于排障"""
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("系统信息:")
    logger.info("Python版本: %s", sys.version.replace("\n", " "))
    logger.info("操作系统: %s - %s %s", os.name, platform.system(), platform.release())
    logger.info("CPU核心数: %s", os.cpu_count())
    logger.info("当前工作目录: %s", os.getcwd())
    logger.info("日志目录: %s", os.path.abspath(LOG_DIR))
    logger.info(
        "使用日志处理器: %s",
        "ConcurrentRotatingFileHandler" if HAS_CONCURRENT_HANDLER else "RotatingFileHandler",
    )
    logger.info("=" * 60)


def setup_logging():
    """初始化日志系统，返回 root logger"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 清除已有处理器，避免重复初始化时日志重复输出
    root_logger.handlers.clear()

    # 主日志（全部级别）
    main_handler = create_rotating_handler(LogConfig.MAIN_LOG_FILE, level=logging.DEBUG)
    # 错误日志（只收 ERROR 及以上）
    error_handler = create_rotating_handler(LogConfig.ERROR_LOG_FILE, level=logging.ERROR)

    formatter = logging.Formatter(LogConfig.LOG_FORMAT, LogConfig.DATE_FORMAT)
    handlers = [main_handler, error_handler]

    if config.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
        handlers.append(console_handler)

    for handler in handlers:
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    # 第三方库日志降噪
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)

    root_logger.info("日志系统初始化完成 - 主日志: %s", LogConfig.MAIN_LOG_FILE)
    return root_logger


# 模块导入即完成日志初始化；业务模块直接 logging.getLogger(__name__) 即可用
logger = setup_logging()
