# tasks.py

from __future__ import absolute_import, unicode_literals

import logging
import time

from celery import shared_task


# 阶段 6.2：异步写 sys_log 任务。
# 把 sys_log 的 INSERT 移到 celery worker 异步执行，请求路径不再被日志写入阻塞。
# payload 是已序列化的 dict（避免直接传 Django model 对象触发 ORM 延迟加载问题）。
@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def write_sys_log(self, payload):
    """
    payload schema:
        {
            "log_class_path": "my_app.module.sys_manage.models.SysLog",
            "user_id": int | None,
            "username": str | None,
            "operation": str,
            "method": str,
            "params": str,
            "time": float,
            "ip": str,
        }
    """
    try:
        # 动态 import log class（避免循环引用）
        mod_path, cls_name = payload["log_class_path"].rsplit(".", 1)
        import importlib
        mod = importlib.import_module(mod_path)
        log_cls = getattr(mod, cls_name)
        from django.utils import timezone
        # 注意：SysLog 表里没有 user_id 列，username 才是关联字段，
        # 因此只传 SysLog 模型实际存在的字段。
        log_cls.objects.create(
            username=payload.get("username"),
            operation=payload.get("operation"),
            method=payload.get("method"),
            params=payload.get("params"),
            time=payload.get("time"),
            ip=payload.get("ip"),
            create_date=timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        )
    except Exception as exc:
        # 失败重试（指数退避由 default_retry_delay 控制）
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logging.getLogger(__name__).exception("write_sys_log dropped after retries: %s", exc)


# 阶段 6.2：插入日志的便捷包装 — 优先用 Celery 异步，失败时回退同步。
# 这样改动面小，老的 LoggerHelper.insert_log_info 调用全部替换为这一行即可。
def insert_log_info_async(log_class_path, user, operation, method, params, time_cost, ip):
    """
    :param log_class_path: 日志 model 类的可解析路径，如 'my_app.module.sys_manage.models.SysLog'
    :param user: Django User 对象 / username str / None
    :param operation / method / params / time_cost / ip: 同 LoggerHelper.insert_log_info
    """
    user_id = getattr(user, "id", None) if user is not None else None
    username = getattr(user, "username", None) if user is not None and not isinstance(user, str) else user
    payload = {
        "log_class_path": log_class_path,
        "user_id": user_id,
        "username": username,
        "operation": operation,
        "method": method,
        "params": params,
        "time": time_cost,
        "ip": ip,
    }
    try:
        # 异步派发；broker 不可用时立即抛 OperationalError，回退到同步
        write_sys_log.delay(payload)
    except Exception:
        # 兜底：直接同步写库（与原行为一致）
        from django.utils import timezone
        mod_path, cls_name = log_class_path.rsplit(".", 1)
        import importlib
        mod = importlib.import_module(mod_path)
        log_cls = getattr(mod, cls_name)
        log_cls.objects.create(
            username=username,
            operation=operation,
            method=method,
            params=params,
            time=time_cost,
            ip=ip,
            create_date=timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        )


# # 使用Celery的例子
from my_project.celery import app

@app.task
def add(x, y):
    print("start excute task")
    time.sleep(200)  # 模拟任务处理
    print("finish excute task")
    return x + y