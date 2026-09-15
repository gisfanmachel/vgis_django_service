# celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.signals import worker_ready

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')

app = Celery('my_project')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()


@worker_ready.connect
def _warm_caches_on_worker_ready(sender=None, **kwargs):
    """Stage C：worker 启动 5 秒后跑一次缓存预热任务（sys_dict/sys_menu/tm_district/tm_region）"""
    try:
        from my_app.utils.cacheWarmer import warm_all_caches
        warm_all_caches.apply_async(countdown=5)
    except Exception as exp:
        # 启动期 Redis 未就绪也不应阻塞 worker；warning 留日志即可
        import logging
        logging.getLogger("django").warning("[celery] warm_all_caches enqueue failed: %s", exp)