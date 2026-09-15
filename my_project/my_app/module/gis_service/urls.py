# -*- coding: utf-8 -*-
# gis_service 模块的路由 —— 前缀 my_api/gis/
#
# 路由设计（注意：mvt/{table}/{z}/{x}/{y}.pbf 与 mvt/{table}/info/ 必须放在
# pmtiles/cog 等同名前缀之前，否则 mvt 的 {z} 会把 info 当成 z 值）。
from django.urls import path

from my_app.module.gis_service import views as v

# 简化前缀（避免重复粘贴）
P = "my_api/gis/"

urlpatterns = [
    # ---- Vector ----
    path(P + "vector/load/", v.VectorLoadView.as_view(), name="gis_vector_load"),
    path(P + "vector/tables/", v.vector_tables, name="gis_vector_tables"),
    path(P + "vector/tables/<str:table>/columns/", v.vector_table_columns,
         name="gis_vector_columns"),
    path(P + "vector/tables/<str:table>/", v.vector_drop_table, name="gis_vector_drop"),

    # ---- MVT（动态瓦片 + 表信息）----
    # 注意：MVT 路由在前，pmtiles/cog 路径冲突时不会被它们吞掉
    path(P + "mvt/<str:table>/info/", v.mvt_table_info, name="gis_mvt_info"),
    path(P + "mvt/<str:table>/<int:z>/<int:x>/<int:y>.pbf",
         v.mvt_tile, name="gis_mvt_tile"),

    # ---- PMTiles ----
    path(P + "pmtiles/list/", v.list_tasks, {"task_type": "pmtiles"}, name="gis_pmtiles_list"),
    path(P + "pmtiles/publish/", v.pmtiles_publish, name="gis_pmtiles_publish"),
    path(P + "pmtiles/tasks/<str:task_id>/", v.pmtiles_task_status,
         name="gis_pmtiles_task_status"),

    # ---- COG ----
    path(P + "cog/list/", v.list_tasks, {"task_type": "cog"}, name="gis_cog_list"),
    path(P + "cog/publish/", v.cog_publish, name="gis_cog_publish"),
    path(P + "cog/tasks/<str:task_id>/", v.cog_task_status, name="gis_cog_task_status"),
    path(P + "cog/tiles/<int:z>/<int:x>/<int:y>.png", v.cog_tile,
         name="gis_cog_tile"),

    # ---- STAC ----
    path(P + "stac/ingest/", v.stac_ingest, name="gis_stac_ingest"),

    # ---- 统一任务查询 ----
    # 注意：tasks/list/ 必须在 tasks/{task_id}/ 之前，否则会被 {task_id} 吞掉
    path(P + "tasks/list/", v.list_tasks, name="gis_task_list"),
    path(P + "tasks/<str:task_id>/", v.task_status_unified, name="gis_task_status"),

    # ---- 健康 / 信息 ----
    path(P + "health/", v.health, name="gis_health"),
    path(P + "info/", v.info, name="gis_info"),
]