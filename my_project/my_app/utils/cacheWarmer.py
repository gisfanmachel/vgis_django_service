# -*- coding: utf-8 -*-
"""
Stage C：缓存预热 Celery 任务。

worker_ready 时自动触发一次（见 my_project/celery.py 末尾的 worker_ready.connect）。
失败重试有限（最多 3 次），避免启动期 Redis 不稳导致 worker 反复重启。
"""
from __future__ import unicode_literals

import logging

from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger("django")


@shared_task(name="my_app.cache.warm_all", bind=True, max_retries=3, default_retry_delay=30)
def warm_all_caches(self):
    """
    预热 5 张热表的全量缓存：
      sys_dict_catelog / sys_dict / sys_menu / tm_district / tm_region

    注意：
      - 直接走 connection.cursor() 而非 ORM，避开 CONN_MAX_AGE 影响，
        启动期一次性 SQL 也不会被缓存中间件拦。
      - 失败走 celery 自动重试；失败也不阻塞 worker 启动。
    """
    try:
        from django.db import connection

        warmed = []
        with connection.cursor() as cur:
            # 1) sys_dict_catelog（数据字典类别）
            cur.execute("SELECT id, dict_catelog_name FROM sys_dict_catelog")
            cache.set(
                "table:sys_dict_catelog:all",
                [{"id": r[0], "name": r[1]} for r in cur.fetchall()],
                3600,
            )
            warmed.append("sys_dict_catelog")

            # 2) sys_dict（数据字典项）
            cur.execute("SELECT id, dict_catelog_id, type_value, memo_value FROM sys_dict")
            cache.set(
                "table:sys_dict:all",
                [{"id": r[0], "catelog": r[1], "type": r[2], "memo": r[3]} for r in cur.fetchall()],
                3600,
            )
            warmed.append("sys_dict")

            # 3) sys_menu（菜单树）
            cur.execute(
                "SELECT menu_id, parent_id, name, url, type, icon, order_num, is_show FROM sys_menu"
            )
            cache.set(
                "table:sys_menu:all",
                [{
                    "id": r[0], "parent": r[1], "name": r[2], "url": r[3],
                    "type": r[4], "icon": r[5], "order": r[6], "show": r[7],
                } for r in cur.fetchall()],
                1800,
            )
            warmed.append("sys_menu")

            # 4) tm_district（行政区划—— 全国 3329 行，缓存 1 天）
            cur.execute("SELECT dis_code, dis_name, parent_code FROM tm_district")
            cache.set(
                "table:tm_district:all",
                [{"code": r[0], "name": r[1], "parent": r[2]} for r in cur.fetchall()],
                24 * 3600,
            )
            warmed.append("tm_district")

            # 5) tm_region（大区—— 7 行）
            cur.execute("SELECT DISTINCT region_name, region_code FROM tm_region")
            cache.set(
                "table:tm_region:all",
                [{"name": r[0], "code": r[1]} for r in cur.fetchall()],
                24 * 3600,
            )
            warmed.append("tm_region")

        logger.info("[cache_warmer] warmed: %s", warmed)
        return "warmed: {}".format(",".join(warmed))
    except Exception as exp:
        logger.warning("[cache_warmer] failed: %s, retrying", exp)
        raise self.retry(exc=exp)