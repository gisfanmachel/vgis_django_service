# -*- coding: utf-8 -*-
# gis_service 模块
#
# 内容：
#   - Vector 灌库（GeoJSON → PostGIS）
#   - 动态 MVT 瓦片（Django 直查 MYDB）
#   - PMTiles 发布（Celery 异步：GeoJSON → pmtiles → MinIO）
#   - COG 发布（Celery 异步：TIFF → COG → MinIO + pgSTAC）
#   - STAC ingest（Celery 异步：ndjson → pypgstac）
#
# 路由前缀：/my_api/gis/（在 urls.py 写死）