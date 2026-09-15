# -*- coding: utf-8 -*-
"""
请求上下文（contextvars）

middleware 在请求开始时调用 set_request_context() 把 request_id / user_id /
path / method 等塞进 contextvars，ES Handler 在 emit 时调用 get_request_context()
把它们读出来一起写进 ES 文档。

为什么用 contextvars：
  - 线程安全（每个请求线程一份）
  - 跨函数调用栈无需显式传参
  - async 任务也能拿到（celery worker 子进程里取不到——这是正常的）
"""

import contextvars
import uuid


# 默认空值：未走 middleware 的日志（celery / 启动期 / 外部脚本）也能安全取
_request_id_var = contextvars.ContextVar('request_id', default=None)
_user_id_var = contextvars.ContextVar('user_id', default=None)
_username_var = contextvars.ContextVar('username', default=None)
_path_var = contextvars.ContextVar('path', default=None)
_method_var = contextvars.ContextVar('method', default=None)
_remote_addr_var = contextvars.ContextVar('remote_addr', default=None)


def set_request_context(request=None, **overrides):
    """
    在请求开始时调用。

    :param request: Django HttpRequest（可选；不传则只取 overrides）
    :param overrides: 手动覆盖的字段
    :return: request_id 字符串（middleware 也可挂到 request 上方便后续取）
    """
    rid = overrides.get('request_id') or (getattr(request, 'request_id', None) if request else None) or uuid.uuid4().hex
    _request_id_var.set(rid)

    if request is not None:
        # user
        user = getattr(request, 'user', None)
        if user is not None and getattr(user, 'is_authenticated', False):
            _user_id_var.set(str(getattr(user, 'id', '')) or str(getattr(user, 'pk', '')))
            _username_var.set(getattr(user, 'username', None))
        # path / method / remote_addr
        _path_var.set(getattr(request, 'path', None))
        _method_var.set(getattr(request, 'method', None))
        # remote_addr: 优先 X-Forwarded-For
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            _remote_addr_var.set(xff.split(',')[0].strip())
        else:
            _remote_addr_var.set(request.META.get('REMOTE_ADDR'))

    # overrides 优先
    for k, v in overrides.items():
        if k == 'request_id':
            _request_id_var.set(v)
        elif k == 'user_id':
            _user_id_var.set(v)
        elif k == 'username':
            _username_var.set(v)
        elif k == 'path':
            _path_var.set(v)
        elif k == 'method':
            _method_var.set(v)
        elif k == 'remote_addr':
            _remote_addr_var.set(v)

    return rid


def clear_request_context():
    """请求结束时清理（避免长寿命线程 / worker 上下文污染）。"""
    _request_id_var.set(None)
    _user_id_var.set(None)
    _username_var.set(None)
    _path_var.set(None)
    _method_var.set(None)
    _remote_addr_var.set(None)


def get_request_context():
    """ES Handler 调用：取一份快照 dict。"""
    return {
        'request_id': _request_id_var.get(),
        'user_id': _user_id_var.get(),
        'username': _username_var.get(),
        'path': _path_var.get(),
        'method': _method_var.get(),
        'remote_addr': _remote_addr_var.get(),
    }
