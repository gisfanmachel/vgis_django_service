#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : PostgreSQL 连接池封装
#            带取连接重试 + 连接健康检查（SELECT 1）+ 连接池自动重建，
#            解决长跑服务里「连接被服务端/中间件掐断后一直拿到坏连接」的问题
# @Software: PyCharm
import logging
import threading
import time

import config

logger = logging.getLogger(__name__)

try:
    from psycopg2 import pool as pg_pool
except ImportError:  # 允许无 DB 依赖的服务在不装 psycopg2 的情况下导入本模块
    pg_pool = None


class PgConnectionPool:
    """线程安全的 PostgreSQL 连接池"""

    def __init__(self, minconn=None, maxconn=None,
                 host=None, port=None, dbname=None, user=None, password=None,
                 connect_timeout=None, enabled=None):
        self.enabled = config.DB_ENABLED if enabled is None else enabled
        self.host = host or config.DB_HOST
        self.port = port or config.DB_PORT
        self.dbname = dbname or config.DB_NAME
        self.user = user or config.DB_USER
        self.password = config.DB_PASSWORD if password is None else password
        self.connect_timeout = connect_timeout or config.DB_CONNECT_TIMEOUT

        self.minconn = minconn if minconn is not None else config.DB_POOL_MIN_CONNECTIONS
        self.maxconn = maxconn if maxconn is not None else config.DB_POOL_MAX_CONNECTIONS

        self._pool = None
        self._lock = threading.Lock()

        if self.enabled:
            self.init_pool()

    # ------------------------------------------------------------------
    # 初始化 / 重建
    # ------------------------------------------------------------------
    def init_pool(self):
        """初始化连接池，带 TCP 保活参数"""
        if pg_pool is None:
            raise RuntimeError("未安装 psycopg2，无法初始化数据库连接池")

        connection_kwargs = {
            "host": self.host,
            "port": self.port,
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
            # 保活：长时间无活动时主动探活，避免连接被中间设备静默断开
            "keepalives": 1,
            "keepalives_idle": 60,
            "keepalives_interval": 10,
            "keepalives_count": 3,
            "connect_timeout": self.connect_timeout,
        }
        try:
            self._pool = pg_pool.ThreadedConnectionPool(
                minconn=self.minconn,
                maxconn=self.maxconn,
                **connection_kwargs
            )
            logger.info("数据库连接池初始化成功 - %s:%s/%s，min=%s max=%s",
                        self.host, self.port, self.dbname, self.minconn, self.maxconn)
        except Exception as e:
            logger.error("数据库连接池初始化失败: %s", e)
            raise

    def reconnect_pool(self):
        """关闭并重建连接池"""
        with self._lock:
            try:
                logger.warning("正在重建数据库连接池...")
                if self._pool is not None:
                    self._pool.closeall()
                self.init_pool()
                logger.info("数据库连接池重建成功")
            except Exception as e:
                logger.error("重建数据库连接池失败: %s", e)

    # ------------------------------------------------------------------
    # 取连接 / 归还
    # ------------------------------------------------------------------
    def get_connection(self, max_retries=3):
        """取一个可用连接；连续拿到坏连接或异常时重建连接池"""
        if not self.enabled or self._pool is None:
            raise ConnectionError("数据库连接池未启用或未初始化")

        retry_count = 0
        while retry_count < max_retries:
            try:
                conn = self._pool.getconn()
                if self.is_connection_valid(conn):
                    return conn
                logger.warning("获取到无效连接，尝试重新获取 (重试 %s/%s)", retry_count + 1, max_retries)
                try:
                    conn.close()
                except Exception:
                    pass
                retry_count += 1
                time.sleep(0.5)
            except Exception as e:
                logger.error("获取数据库连接失败 (重试 %s/%s): %s", retry_count + 1, max_retries, e)
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(1)

        logger.error("获取数据库连接重试次数用尽，尝试重建连接池")
        self.reconnect_pool()
        raise ConnectionError("无法获取有效的数据库连接")

    def return_connection(self, conn):
        """归还连接；归还失败则直接关闭，避免泄漏"""
        if conn is None:
            return
        try:
            self._pool.putconn(conn)
        except Exception as e:
            logger.error("归还数据库连接失败: %s", e)
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def is_connection_valid(conn):
        """执行 SELECT 1 验证连接是否可用"""
        if conn is None:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                return bool(result and result[0] == 1)
        except Exception:
            return False

    def close_all(self):
        """关闭连接池"""
        if self._pool is not None:
            try:
                self._pool.closeall()
                logger.info("数据库连接池已关闭")
            except Exception as e:
                logger.error("关闭数据库连接池失败: %s", e)

    # ------------------------------------------------------------------
    # 便捷用法：with 语句自动归还
    # ------------------------------------------------------------------
    def __enter__(self):
        self._ctx_conn = self.get_connection()
        return self._ctx_conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        conn = getattr(self, "_ctx_conn", None)
        if conn is not None:
            # 出现异常时回滚，避免把带未提交事务的连接归还给池
            if exc_type is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            self.return_connection(conn)
            self._ctx_conn = None
        return False
