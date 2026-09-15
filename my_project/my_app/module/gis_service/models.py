# -*- coding: utf-8 -*-
# gis_service 模块的模型：
#   - GISTask：Celery 异步任务的状态表（PMTiles / COG / STAC ingest）
#   - GISLayer：vector 表注册表（vector/load 灌入的 PostGIS 表元信息）
#
# 约定：managed = False + 显式 db_table（表由 database/GIS_TABLES_2026_09.sql 手工维护）
from django.db import models


class GISTask(models.Model):
    """Celery 异步任务状态表。
    task_id 与 celery.AsyncResult.task_id 同字符串；唯一约束用于去重。
    payload / result 用 JSONB 兼容 Dict/List。
    """
    id = models.BigAutoField(primary_key=True)
    task_id = models.CharField(max_length=64, unique=True)
    task_type = models.CharField(max_length=32)         # pmtiles / cog / stac
    status = models.CharField(max_length=16)            # pending / running / success / failure
    # PG 上是 JSONB；Django 这边用 JSONField 即可，PG 后端会自动用 JSONB
    payload = models.JSONField(blank=True, null=True)
    result = models.JSONField(blank=True, null=True)
    current_step = models.CharField(max_length=64, blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tt_gis_task'
        db_table_comment = 'gis_service 异步任务状态表'


class GISLayer(models.Model):
    """vector 表注册表。
    vector/load 灌完 PostGIS 后立即 upsert 一行；vector/tables/ 列表从这读。
    """
    table_name = models.CharField(max_length=64, primary_key=True)
    layer_name = models.CharField(max_length=64)
    geometry_type = models.CharField(max_length=32, blank=True, null=True)
    srid = models.IntegerField(blank=True, null=True, default=4326)
    feature_count = models.BigIntegerField(blank=True, null=True, default=0)
    bbox = models.CharField(max_length=128, blank=True, null=True)
    has_index = models.BooleanField(blank=True, null=True, default=False)
    create_time = models.DateTimeField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tt_gis_layer'
        db_table_comment = 'gis_service vector 表注册表'