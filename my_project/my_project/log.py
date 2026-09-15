#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/9/26 17:25
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : log.py
# @Descr   :
# @Software: PyCharm
import logging
import os.path
import queue
import sys
import threading
import time
import traceback
from datetime import datetime

from loguru import logger


# -----------------------------------------------------------------------------
# 阶段 7：Elasticsearch 异步日志 Handler
#
# 设计要点：
#   1. 不在请求线程阻塞等 ES —— 用 queue.Queue + 后台守护线程批量写
#   2. 按日分索引（vgis-myapp-YYYY.MM.DD），让 Kibana index pattern 简单
#   3. 批量写入：攒满 batch_size 条 或 距上次 flush 超过 flush_interval 秒
#   4. 写 ES 失败降级到 stderr（避免递归走 handler）
#   5. 失败永不上抛 —— 污染请求路径是绝对禁止的
#   6. contextvars 注入 request_id / user_id / path / method 等，便于 Kibana 关联查询
# -----------------------------------------------------------------------------


def _safe_get_request_context():
    """从 contextvars 读取请求上下文（middleware 注入）。"""
    try:
        from my_project.request_context import get_request_context
        return get_request_context()
    except Exception:
        return {}


class ElasticsearchHandler(logging.Handler):
    """
    异步批量写 Elasticsearch 的 logging.Handler。

    配置（settings.py LOGGING['handlers']['es']）：
        class: my_project.log.ElasticsearchHandler
        level: INFO
        es_hosts: ['http://192.168.3.40:9200']
        es_user: elastic
        es_password: 'xxx'
        index_prefix: vgis-myapp
        flush_interval: 1.0
        batch_size: 100
        request_timeout: 5
    """

    # 类级共享：所有 ES handler 实例共用一个后台线程 + 队列，避免每条 logger
    # 都起一个线程。key=(host, user, prefix, index)
    _SHARED_STATE = {}  # {(es_hosts_tuple, es_user, index_prefix, index_date): (queue.Queue, threading.Thread)}

    def __init__(self, level=logging.INFO,
                 es_hosts=None, es_user=None, es_password=None,
                 index_prefix='vgis-myapp',
                 flush_interval=1.0, batch_size=100, request_timeout=5,
                 **kwargs):
        super().__init__(level=level)
        self.es_hosts = es_hosts or ['http://127.0.0.1:9200']
        self.es_user = es_user
        self.es_password = es_password
        self.index_prefix = index_prefix
        self.flush_interval = float(flush_interval)
        self.batch_size = int(batch_size)
        self.request_timeout = float(request_timeout)

        # 选一个 key：相同 (host, user, prefix) 共用一个后台线程
        host_key = tuple(self.es_hosts)
        # 用当天日期做 key 的一部分 —— 跨天时切到新队列/线程（简单的做法）
        idx_date = datetime.now().strftime('%Y.%m.%d')
        self._state_key = (host_key, self.es_user, self.index_prefix, idx_date)
        self._current_date = idx_date
        self._es_client = None

        # lazy import ES client（模块级导入放这里，便于测试时 mock）
        try:
            from elasticsearch import Elasticsearch
            kwargs_client = {
                'hosts': self.es_hosts,
                'request_timeout': self.request_timeout,
                'max_retries': 0,
            }
            if self.es_user and self.es_password:
                kwargs_client['basic_auth'] = (self.es_user, self.es_password)
            self._es_client_class = Elasticsearch
            self._es_client_kwargs = kwargs_client
        except Exception as e:
            # ES 客户端都装不上——handler 退化为只打 stderr
            sys.stderr.write(f"[ESHandler] cannot import elasticsearch: {e}\n")
            self._es_client_class = None
            self._es_client_kwargs = None

        # 初始化共享队列 + 后台线程
        self._init_shared_state()

    def _init_shared_state(self):
        """取得或创建共享队列+线程。"""
        state = ElasticsearchHandler._SHARED_STATE.get(self._state_key)
        if state is None:
            q = queue.Queue(maxsize=10000)
            t = threading.Thread(
                target=self._worker_loop,
                args=(self._state_key, q),
                daemon=True,
                name=f'ESLogHandler-{self.index_prefix}',
            )
            t.start()
            state = (q, t)
            ElasticsearchHandler._SHARED_STATE[self._state_key] = state
        self._queue, self._thread = state

    @staticmethod
    def _worker_loop(state_key, q):
        """后台线程：从队列取日志，攒批，bulk 写 ES。"""
        try:
            # 线程内创建 ES client（线程安全）
            from elasticsearch import Elasticsearch
            host_key, es_user, index_prefix, _idx_date = state_key
            client_kwargs = {
                'hosts': list(host_key),
                'request_timeout': 5,
                'max_retries': 0,
            }
            if es_user:
                # 实际 es_password 在 state 里存（这里为了简化，重新拿一次）
                pass
            # 真正的 client 在 _flush() 里按当前 state 拼装
            while True:
                try:
                    item = q.get(timeout=1.0)
                except queue.Empty:
                    continue
                batch = [item]
                # 攒 batch
                t_start = time.time()
                while len(batch) < 100 and (time.time() - t_start) < 1.0:
                    try:
                        batch.append(q.get_nowait())
                    except queue.Empty:
                        time.sleep(0.05)
                # 写
                try:
                    ElasticsearchHandler._flush(batch, state_key)
                except Exception as e:
                    # 永不 raise —— 写 stderr 即可
                    sys.stderr.write(f"[ESHandler] flush failed: {e}\n")
                    sys.stderr.write(traceback.format_exc() + "\n")
        except Exception as e:
            sys.stderr.write(f"[ESHandler] worker crashed: {e}\n")
            sys.stderr.write(traceback.format_exc() + "\n")

    @staticmethod
    def _flush(batch, state_key):
        """真正写 ES：bulk 写一条索引。"""
        host_key, es_user, index_prefix, _idx_date = state_key
        if not batch:
            return
        # 重新拿一份完整 state（es_password 在外部 handler 实例上）
        # 这里简化：用一个全局注册表记录 password
        full_state = _ES_FULL_STATE.get(state_key)
        if not full_state:
            return
        es_password = full_state.get('es_password')

        from elasticsearch import Elasticsearch
        client_kwargs = {
            'hosts': list(host_key),
            'request_timeout': 5,
            'max_retries': 0,
        }
        if es_user and es_password:
            client_kwargs['basic_auth'] = (es_user, es_password)

        client = Elasticsearch(**client_kwargs)
        idx_date = datetime.now().strftime('%Y.%m.%d')
        index_name = f'{index_prefix}-{idx_date}'

        actions = []
        for doc in batch:
            # 索引名混进 action 里
            actions.append({'index': {'_index': index_name}})
            actions.append(doc)
        if actions:
            client.bulk(operations=actions, refresh=False)

    def emit(self, record):
        """logging 入口 —— 把 record 序列化成 dict 投进队列，立刻返回。"""
        try:
            # 1) 跨天切换：state_key 含日期，跨天时换 key，重新 init
            today = datetime.now().strftime('%Y.%m.%d')
            if today != self._current_date:
                self._current_date = today
                old_key = self._state_key
                self._state_key = (old_key[0], old_key[1], old_key[2], today)
                self._init_shared_state()
                # password 也要复制到新 key
                _ES_FULL_STATE[self._state_key] = _ES_FULL_STATE.get(old_key, {})

            # 2) 把 password 放到全局注册表（线程用）
            _ES_FULL_STATE.setdefault(
                self._state_key,
                {'es_password': self.es_password},
            )

            # 3) 序列化为 dict
            ctx = _safe_get_request_context()
            doc = {
                '@timestamp': datetime.utcfromtimestamp(record.created).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                'level': record.levelname,
                'logger': record.name,
                'module': record.module,
                'func': record.funcName,
                'line': record.lineno,
                'message': record.getMessage(),
                'request_id': ctx.get('request_id'),
                'user_id': ctx.get('user_id'),
                'username': ctx.get('username'),
                'path': ctx.get('path') or getattr(record, 'pathname', None),
                'method': ctx.get('method'),
                'remote_addr': ctx.get('remote_addr'),
            }
            if record.exc_info:
                doc['exception'] = self.format(record)
            # 4) 投进队列（非阻塞；满则丢）
            try:
                self._queue.put_nowait(doc)
            except queue.Full:
                # 队列满：丢弃并 stderr 提示
                sys.stderr.write(f"[ESHandler] queue full, dropped log: {record.getMessage()[:80]}\n")
        except Exception as e:
            # emit 永不 raise —— 降级到 stderr
            try:
                sys.stderr.write(f"[ESHandler] emit failed: {e}\n")
            except Exception:
                pass


# ES handler 把 password 注册到这里的全局表，让后台线程能拿到
_ES_FULL_STATE = {}


# 1.🎖️先声明一个类继承logging.Handler
class InterceptTimedRotatingFileHandler(logging.Handler):
    """
    自定义反射时间回滚日志记录器
    缺少命名空间
    """

    def __init__(self, filename, when='d', interval=1, backupCount=15, encoding="utf-8", delay=False, utc=False,
                 atTime=None, logging_levels="all"):
        super(InterceptTimedRotatingFileHandler, self).__init__()
        filename = os.path.abspath(filename)
        when = when.lower()
        # 2.🎖️需要本地用不同的文件名做为不同日志的筛选器
        self.logger_ = logger.bind(sime=filename)
        self.filename = filename
        key_map = {
            'h': 'hour',
            'w': 'week',
            's': 'second',
            'm': 'minute',
            'd': 'day',
        }
        # 根据输入文件格式及时间回滚设立文件名称
        rotation = "%d %s" % (interval, key_map[when])
        retention = "%d %ss" % (backupCount, key_map[when])
        time_format = "{time:%Y-%m-%d_%H-%M-%S}"
        if when == "s":
            time_format = "{time:%Y-%m-%d_%H-%M-%S}"
        elif when == "m":
            time_format = "{time:%Y-%m-%d_%H-%M}"
        elif when == "h":
            time_format = "{time:%Y-%m-%d_%H}"
        elif when == "d":
            time_format = "{time:%Y-%m-%d}"
        elif when == "w":
            time_format = "{time:%Y-%m-%d}"
        level_keys = ["info"]
        # 3.🎖️构建一个筛选器
        levels = {
            "debug": lambda x: "DEBUG" == x['level'].name.upper() and x['extra'].get('sime') == filename,
            "error": lambda x: "ERROR" == x['level'].name.upper() and x['extra'].get('sime') == filename,
            "info": lambda x: "INFO" == x['level'].name.upper() and x['extra'].get('sime') == filename,
            "warning": lambda x: "WARNING" == x['level'].name.upper() and x['extra'].get('sime') == filename}
        # 4. 🎖️根据输出构建筛选器
        if isinstance(logging_levels, str):
            if logging_levels.lower() == "all":
                level_keys = levels.keys()
            elif logging_levels.lower() in levels:
                level_keys = [logging_levels]
        elif isinstance(logging_levels, (list, tuple)):
            level_keys = logging_levels
        for k, f in {_: levels[_] for _ in level_keys}.items():

            # 5.🎖️为防止重复添加sink，而重复写入日志，需要判断是否已经装载了对应sink，防止其使用秘技：反复横跳。
            filename_fmt = filename.replace(".log", "_%s_%s.log" % (time_format, k))
            # noinspection PyUnresolvedReferences,PyProtectedMember
            file_key = {_._name: han_id for han_id, _ in self.logger_._core.handlers.items()}
            filename_fmt_key = "'{}'".format(filename_fmt)
            if filename_fmt_key in file_key:
                continue
                # self.logger_.remove(file_key[filename_fmt_key])
            self.logger_.add(
                filename_fmt,
                retention=retention,
                encoding=encoding,
                level=self.level,
                rotation=rotation,
                compression="tar.gz",  # 日志归档自行压缩文件
                delay=delay,
                enqueue=True,
                filter=f
            )

    def emit(self, record):
        try:
            level = self.logger_.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        # 6.🎖️把当前帧的栈深度回到发生异常的堆栈深度，不然就是当前帧发生异常而无法回溯
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        self.logger_.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
