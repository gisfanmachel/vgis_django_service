# -*- coding: utf-8 -*-
# gis_service 模块的 Celery 异步任务
#
# 任务类型：
#   publish_pmtiles_task  — GeoJSON → PMTiles → MinIO + pgSTAC asset
#   publish_cog_task      — TIFF → COG → MinIO + pgSTAC item
#   ingest_stac_task      — ndjson → pypgstac load
#
# 设计：
#   1) payload 用 dict（与 write_sys_log 同风格；序列化由 Celery 自动做）
#   2) 每个 task 自带状态机：pending → running → success / failure
#   3) current_step 通过 GISOperator 内部 Step 回调写回 tt_gis_task
#   4) 失败重试用 Celery 内置 self.retry；失败 3 次以上落到 error 字段
#
# worker 必须在 40 服务器（或同等）上跑，因为：
#   - ssh_upload_to_minio 走 docker run mc + /mnt/data 挂载
#   - pypgstac 命令默认装在 /root/miniforge3/bin/
# 本机（Windows）仅做 HTTP 派发，不实际执行重活
from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task

logger = logging.getLogger("django")


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def publish_pmtiles_task(self, payload):
    """发布 PMTiles（GeoJSON → pmtiles → MinIO + pgSTAC asset）。

    payload schema：
        {
            "task_pk": int,           # tt_gis_task.id（用于 Step 回调回写 current_step）
            "src": str,               # GeoJSON 在 worker 本地或挂载点的路径
            "table": str,             # PostGIS 表名（可选；提供时优先 PostGIS 数据）
            "layer": str,
            "name": str,
            "minzoom": int,
            "maxzoom": int,
            "props": str,             # 逗号分隔；空 = 全丢
            "out": str,               # 输出 .pmtiles 路径
            "create_user_id": int,
            "stac_collection": str,
            "stac_item": str,
        }
    """
    # 局部 import 避免 Celery worker 启动时无谓加载 GISOperator 链
    from my_app.module.gis_service.manager import GISOperator

    try:
        op = GISOperator()
        return op.publish_pmtiles(self, payload)
    except Exception as exc:
        logger.exception("publish_pmtiles_task 失败: %s", exc)
        # 落到 tt_gis_task.error 字段
        try:
            GISOperator.mark_task_failed(payload, str(exc))
        except Exception:
            logger.exception("mark_task_failed 也失败了")
        # 让 Celery 自己计数重试
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1, default_retry_delay=15)
def publish_cog_task(self, payload):
    """发布 COG（TIFF → COG → MinIO + pgSTAC item）。

    payload schema：
        {
            "task_pk": int,
            "src": str,               # 源 TIFF 在 worker 本地路径
            "collection": str,        # STAC collection id
            "title": str,
            "dt": str | None,
            "platform": str,
            "dest_srs": str,          # auto / EPSG:3857 / 原样
            "compress": str,          # DEFLATE / ZSTD / LZW / JPEG
            "bands": str,             # 逗号分隔
            "already_cog": bool,
            "no_verify": bool,
            "create_user_id": int,
        }
    """
    from my_app.module.gis_service.manager import GISOperator

    try:
        op = GISOperator()
        return op.publish_cog(self, payload)
    except Exception as exc:
        logger.exception("publish_cog_task 失败: %s", exc)
        try:
            GISOperator.mark_task_failed(payload, str(exc))
        except Exception:
            logger.exception("mark_task_failed 也失败了")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1, default_retry_delay=10)
def ingest_stac_task(self, payload):
    """灌入 STAC（ndjson → pypgstac load）。

    payload schema：
        {
            "task_pk": int,
            "collections_ndjson": str,    # worker 本地路径（worker 自己负责落盘）
            "items_ndjson": str,
            "method": str,                # insert / upsert / delete
            "create_user_id": int,
        }
    """
    from my_app.module.gis_service.manager import GISOperator

    try:
        op = GISOperator()
        return op.ingest_stac(self, payload)
    except Exception as exc:
        logger.exception("ingest_stac_task 失败: %s", exc)
        try:
            GISOperator.mark_task_failed(payload, str(exc))
        except Exception:
            logger.exception("mark_task_failed 也失败了")
        raise self.retry(exc=exc)