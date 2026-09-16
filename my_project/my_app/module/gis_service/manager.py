# -*- coding: utf-8 -*-
# gis_service 模块的业务逻辑层：GISOperator
#
# 复制自 E:\workbuddy\2026-09-07-14-57-30\stac_demo 下的 4 个 CLI 工具：
#   - load_vector_pg.py   → load_vector()           同步灌库（GeoJSON → PostGIS）
#   - mvt_server.py       → build_mvt_sql()         Django 直查 MYDB 渲染 MVT
#   - publish_pmtiles.py  → publish_pmtiles()       Celery 异步（GeoJSON → pmtiles → MinIO + pgSTAC）
#   - publish_cog.py      → publish_cog()           Celery 异步（TIFF → COG → MinIO + pgSTAC）
#   - ingest_stac.py      → ingest_stac()           Celery 异步（ndjson → pypgstac）
#
# 设计原则：
#   1) 每个方法接 self.request / self.payload，与框架其它模块保持一致风格；
#      但重型发布（pmtiles/cog/stac）走 Celery，方法接 task / payload 而不是 request
#   2) 失败时 update tt_gis_task.error / status='failure'，让 /tasks/{id}/ 端点能查到
#   3) 自验证（瓦片 HTTP 探活）失败不直接 raise，记 warning 落 result 字段
import gzip
import io
import json
import logging
import math
import os
import re
import sqlite3
import struct
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

from django.db import connection as default_connection
from django.utils import timezone

from my_app.module.gis_service.models import GISLayer, GISTask
from my_app.module.gis_service.utility import GISHelper, Step

logger = logging.getLogger("django")


# ===========================================================================
# 全局常量（与原脚本一致）
# ===========================================================================
EXTENT = 4096           # MVT extent
BUFFER = 64
TABLE_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# 系统表黑名单：vector/tables/ 不应返回这些（避免把 PG 自身表当业务表）
SYSTEM_TABLES = (
    "spatial_ref_sys", "geometry_columns", "geography_columns",
    "pg_stat_statements",
)


class GISOperator:
    """GIS 业务编排。

    不持有 connection：每个方法按需从 default_connection 取，
    这样与框架的事务/CONN_MAX_AGE 机制天然兼容。
    """

    # =========================================================================
    # 内部工具：任务状态写回（被 tasks.py 回调）
    # =========================================================================
    @staticmethod
    def _on_step(task_obj_or_pk, name):
        """Step 回调：把当前步骤写到 tt_gis_task.current_step。
        入参兼容 task 对象和 task_pk（异步链路里 task 对象有时拿不到）。
        """
        try:
            from django.utils import timezone as _tz
            if isinstance(task_obj_or_pk, GISTask):
                task_obj_or_pk.current_step = name
                task_obj_or_pk.update_time = _tz.now()
                task_obj_or_pk.save(update_fields=["current_step", "update_time"])
        except Exception:
            logger.exception("_on_step 写 current_step 失败")

    @staticmethod
    def mark_task_pending(payload, task_id):
        """Celery 派发后立刻把 pending 行写进去（如果 view 层还没写）。"""
        try:
            task_pk = payload.get("task_pk")
            if not task_pk:
                return
            GISTask.objects.filter(pk=task_pk).update(
                task_id=task_id,
                status="pending",
                update_time=timezone.now(),
            )
        except Exception:
            logger.exception("mark_task_pending 失败")

    @staticmethod
    def mark_task_running(payload):
        try:
            task_pk = payload.get("task_pk")
            if not task_pk:
                return
            GISTask.objects.filter(pk=task_pk).update(
                status="running",
                update_time=timezone.now(),
            )
        except Exception:
            logger.exception("mark_task_running 失败")

    @staticmethod
    def mark_task_success(payload, result):
        try:
            task_pk = payload.get("task_pk")
            if not task_pk:
                return
            GISTask.objects.filter(pk=task_pk).update(
                status="success",
                result=result if isinstance(result, dict) else {"data": str(result)},
                update_time=timezone.now(),
            )
        except Exception:
            logger.exception("mark_task_success 失败")

    @staticmethod
    def mark_task_failed(payload, error):
        try:
            task_pk = payload.get("task_pk")
            if not task_pk:
                return
            GISTask.objects.filter(pk=task_pk).update(
                status="failure",
                error=str(error),
                update_time=timezone.now(),
            )
        except Exception:
            logger.exception("mark_task_failed 失败")

    # =========================================================================
    # Vector 灌库（与原 load_vector_pg.py L15-53 一致）
    # =========================================================================
    def load_vector(self, geojson, table, user_id):
        """把 GeoJSON（dict 或文件 path）灌到 PostGIS，建 GIST 索引。

        与原脚本的差异：
          1) 兼容入参为 dict（request.data 直接喂进来）和文件 path
          2) 自动 upsert 到 tt_gis_layer
          3) geom 类型按实际类型推断（POLYGON / MULTIPOLYGON / LINESTRING / POINT / ...）
          4) 失败 raise，view 层负责转 fail()
        """
        from my_project import settings

        if not TABLE_RE.match(table or ""):
            raise ValueError("invalid table name: {}".format(table))

        # ---------- 1) 解析输入 ----------
        if isinstance(geojson, dict):
            data = geojson
        elif isinstance(geojson, (str, bytes, os.PathLike)):
            with open(str(geojson), encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise TypeError("geojson 必须是 dict 或文件路径")
        feats = data.get("features") or []
        if not feats:
            raise ValueError("GeoJSON 中没有 features")

        # ---------- 2) 采集属性键（首条决定列集） ----------
        prop_keys = sorted({k for f in feats for k in (f.get("properties") or {})})
        # 推断几何类型（取最细的；比如 Mixed 时优先 MULTI*）
        geom_type = self._infer_geometry_type(feats)

        # ---------- 3) 写库 ----------
        with default_connection.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
            cur.execute('DROP TABLE IF EXISTS "{}"'.format(table))
            cols_sql = ", ".join('"{k}" text'.format(k=k) for k in prop_keys)
            cur.execute(
                'CREATE TABLE "{t}" (gid serial primary key, {c}, geom geometry({g},4326))'.format(
                    t=table, c=cols_sql, g=geom_type))
            insert = ('INSERT INTO "{t}" ({cols}, geom) VALUES ({ph}, ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)))'.format(
                t=table,
                cols=", ".join('"{k}"'.format(k=k) for k in prop_keys),
                ph=", ".join(["%s"] * len(prop_keys)),
            ))
            rows = []
            for f in feats:
                p = f.get("properties") or {}
                rows.append(tuple(p.get(k) for k in prop_keys) + (json.dumps(f["geometry"]),))
            cur.executemany(insert, rows)
            cur.execute('CREATE INDEX "{t}_geom_idx" ON "{t}" USING GIST (geom)'.format(t=table))
            cur.execute('CREATE INDEX "{t}_gid_idx" ON "{t}" (gid)'.format(t=table))
            cur.execute('ANALYZE "{t}"'.format(t=table))
            cur.execute('SELECT count(*), ST_AsText(ST_Extent(geom)) FROM "{t}"'.format(t=table))
            n, ext_wkt = cur.fetchone()
            default_connection.commit()

        # ---------- 4) upsert tt_gis_layer ----------
        bbox_str = ext_wkt or ""
        GISLayer.objects.update_or_create(
            table_name=table,
            defaults=dict(
                layer_name=table,
                geometry_type=geom_type,
                srid=4326,
                feature_count=n,
                bbox=bbox_str,
                has_index=True,
                create_user_id=user_id,
                create_time=timezone.now(),
            ),
        )
        return {
            "table": table,
            "feature_count": n,
            "geometry_type": geom_type,
            "bbox": bbox_str,
        }

    @staticmethod
    def _infer_geometry_type(feats):
        """推断 GEOMETRY 子类型。多类型共存时取 MULTI 版本（兼容 GeoJSON 限制）。"""
        types = set()
        for f in feats:
            g = f.get("geometry") or {}
            t = (g.get("type") or "").upper()
            if t.endswith("Z") or t.endswith("M"):
                t = t[:-1]
            if t == "POLYGON":
                types.add("MULTIPOLYGON")
            elif t == "LINESTRING":
                types.add("MULTILINESTRING")
            elif t == "POINT":
                types.add("MULTIPOINT")
            elif t.startswith("MULTI") or t == "GEOMETRYCOLLECTION":
                types.add(t)
        if not types:
            return "GEOMETRY"
        if len(types) == 1:
            return next(iter(types))
        # 多种混合 → 用 GEOMETRY（PostGIS 不强制）
        return "GEOMETRY"

    # =========================================================================
    # Vector 列表 / 列名 / 删除
    # =========================================================================
    def list_vector_tables(self):
        """从 information_schema + geometry_columns 联合取 vector 表。"""
        out = []
        with default_connection.cursor() as cur:
            cur.execute(
                """
                SELECT t.table_name, g.type, g.srid,
                       (SELECT count(*) FROM information_schema.columns c
                         WHERE c.table_schema = 'public' AND c.table_name = t.table_name
                           AND c.column_name NOT IN ('geom','gid'))
                  FROM information_schema.tables t
             LEFT JOIN geometry_columns g ON g.f_table_name = t.table_name
                 WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
                   AND t.table_name NOT IN %s
              ORDER BY t.table_name
                """,
                [SYSTEM_TABLES],
            )
            for tbl, gtype, srid, n_cols in cur.fetchall():
                # 拼接已注册的元数据（feature_count / bbox / has_index）
                meta = GISLayer.objects.filter(table_name=tbl).first()
                out.append({
                    "table_name": tbl,
                    "geometry_type": gtype or (meta.geometry_type if meta else None),
                    "srid": srid or (meta.srid if meta else 4326),
                    "column_count": n_cols or 0,
                    "feature_count": (meta.feature_count if meta else None),
                    "bbox": (meta.bbox if meta else None),
                    "has_index": (meta.has_index if meta else None),
                })
        return out

    def list_table_columns(self, table):
        if not TABLE_RE.match(table or ""):
            raise ValueError("invalid table name: {}".format(table))
        with default_connection.cursor() as cur:
            cur.execute(
                """
                SELECT column_name, data_type, is_nullable
                  FROM information_schema.columns
                 WHERE table_schema='public' AND table_name=%s
                   AND column_name NOT IN ('geom','gid')
                 ORDER BY ordinal_position
                """,
                [table],
            )
            rows = cur.fetchall()
        if not rows:
            raise LookupError("table not found: {}".format(table))
        return [
            {"column_name": r[0], "data_type": r[1], "is_nullable": r[2]}
            for r in rows
        ]

    def drop_vector_table(self, table):
        if not TABLE_RE.match(table or ""):
            raise ValueError("invalid table name: {}".format(table))
        with default_connection.cursor() as cur:
            cur.execute('DROP TABLE IF EXISTS "{}"'.format(table))
            affected = cur.rowcount
        default_connection.commit()
        GISLayer.objects.filter(table_name=table).delete()
        return {"dropped": table, "existed": bool(affected)}

    # =========================================================================
    # MVT 渲染（与原 mvt_server.py L98-110 完全等价）
    # =========================================================================
    def build_mvt_sql(self, table, z, x, y, extent=EXTENT, buffer=BUFFER):
        """返回 (sql, params)，由 caller 负责 fetchone()[0] 取 MVT bytes。

        低层级（z<14）做 ST_SimplifyPreserveTopology(geom, 3857, tol) 简化，
        高层级直接 ST_Transform(geom, 3857) 后 ST_AsMVTGeom 裁剪。
        """
        # 取非 geom/gid 列
        with default_connection.cursor() as cur:
            cur.execute(
                """
                SELECT column_name FROM information_schema.columns
                 WHERE table_schema='public' AND table_name=%s
                   AND column_name NOT IN ('geom','gid')
                 ORDER BY ordinal_position
                """,
                [table],
            )
            cols = [r[0] for r in cur.fetchall()]
        if not cols:
            raise LookupError("table not found: {}".format(table))

        if z < 14:
            tol = round(156543.03 / (2 ** z), 2)
            geom_expr = "ST_SimplifyPreserveTopology(ST_Transform(t.geom, 3857), {:.2f})".format(tol)
        else:
            geom_expr = "ST_Transform(t.geom, 3857)"

        sel = ", ".join('"{c}"'.format(c=c) for c in cols)
        sql = """
            WITH b AS (SELECT ST_TileEnvelope(%(z)s, %(x)s, %(y)s) AS env),
            mvtgeom AS (
                SELECT ST_AsMVTGeom({geom}, b.env, %(extent)s, %(buffer)s, true) AS geom,
                       {sel}
                  FROM "{table}" t, b
                 WHERE ST_Intersects(t.geom, ST_Transform(b.env, 4326))
            )
            SELECT ST_AsMVT(mvtgeom.*, '{layer}', %(extent)s, 'geom') FROM mvtgeom
        """.format(geom=geom_expr, sel=sel, table=table, layer=table)
        params = {"z": z, "x": x, "y": y, "extent": extent, "buffer": buffer}
        return sql, params

    def render_mvt(self, table, z, x, y):
        """直接渲染 MVT 瓦片 bytes。失败抛 ValueError。"""
        if not TABLE_RE.match(table or ""):
            raise ValueError("invalid table name: {}".format(table))
        if not (0 <= z <= 22):
            raise ValueError("z out of range")
        if not (0 <= x < (2 ** z) and 0 <= y < (2 ** z)):
            raise ValueError("tile out of range")
        sql, params = self.build_mvt_sql(table, z, x, y)
        t0 = time.time()
        with default_connection.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        data = bytes(row[0]) if row and row[0] else b""
        logger.info("MVT %s/%s/%s/%s  %dB  %.0fms", table, z, x, y,
                    len(data), (time.time() - t0) * 1000)
        return data

    def mvt_table_info(self, table):
        """返回表信息 + bbox + 非几何字段列表（/mvt/{table}/info/ 端点用）。"""
        with default_connection.cursor() as cur:
            cur.execute(
                """
                SELECT g.type, g.srid
                  FROM geometry_columns g
                 WHERE g.f_table_name = %s
                """,
                [table],
            )
            row = cur.fetchone()
            if not row:
                # fallback：不是 geometry_columns 也允许（手工建的普通表 + geom 列）
                cur.execute(
                    """
                    SELECT gtype, srid
                      FROM (
                        SELECT GeometryType(geom) AS gtype, ST_SRID(geom) AS srid
                          FROM "{}" LIMIT 1
                      ) t
                    """.format(table),
                )
                row = cur.fetchone()
        if not row:
            raise LookupError("table not found or has no geometry: {}".format(table))
        gtype, srid = row[0], row[1]
        bbox_row = self._table_bbox(table)
        cols = [c["column_name"] for c in self.list_table_columns(table)]
        meta = GISLayer.objects.filter(table_name=table).first()
        return {
            "table_name": table,
            "geometry_type": gtype,
            "srid": int(srid) if srid else None,
            "bbox": bbox_row,
            "columns": cols,
            "feature_count": (meta.feature_count if meta else None),
            "has_index": (meta.has_index if meta else None),
        }

    def _table_bbox(self, table):
        """取整表 WGS84 边界，返回 [minx, miny, maxx, maxy] 或 None。"""
        try:
            with default_connection.cursor() as cur:
                cur.execute(
                    'SELECT ST_AsText(ST_Extent(ST_Transform(geom, 4326))) FROM "{}"'.format(table))
                row = cur.fetchone()
            if not row or not row[0]:
                return None
            # WKT = POLYGON((minx miny, maxx miny, maxx maxy, minx maxy, minx miny))
            import re as _re
            m = _re.search(r"(-?\d+\.?\d*)\s+(-?\d+\.?\d*)", row[0])
            if not m:
                return None
            from shapely import wkt
            poly = wkt.loads(row[0])
            return [poly.bounds[0], poly.bounds[1], poly.bounds[2], poly.bounds[3]]
        except Exception:
            logger.exception("_table_bbox 失败")
            return None

    # =========================================================================
    # PMTiles 发布（Celery 异步 worker 路径，逻辑迁移自 publish_pmtiles.py）
    # =========================================================================
    def publish_pmtiles(self, celery_task, payload):
        """Dispatcher: 根据 payload.tile_type 路由到 vector / raster / terrain 三种实现之一。

        tile_type 默认 "vector"，保持与旧调用完全兼容。
        其它取值：
            - "raster":  PNG 瓦片（TIFF → PNG → MBTiles → PMTiles → MinIO）
            - "terrain": quantized-mesh v1 瓦片（DEM → .terrain → MBTiles → PMTiles → MinIO）
        """
        tile_type = payload.get("tile_type") or "vector"
        # 防御：multipart QueryDict 多值场景，payload 里 tile_type 可能仍是 list
        if isinstance(tile_type, (list, tuple)):
            tile_type = tile_type[0] if tile_type else "vector"
        tile_type = str(tile_type).lower()
        if tile_type == "vector":
            return self._publish_pmtiles_vector(celery_task, payload)
        elif tile_type == "raster":
            return self._publish_pmtiles_raster(celery_task, payload)
        elif tile_type == "terrain":
            return self._publish_pmtiles_terrain(celery_task, payload)
        else:
            raise ValueError(
                "unknown tile_type: {!r}; use vector/raster/terrain".format(tile_type))

    # -------------------------------------------------------------------------
    # Vector PMTiles（GeoJSON → MVT → MBTiles → PMTiles → MinIO）
    # 原 publish_pmtiles() 的逻辑不变；只是重命名并被 dispatcher 调用。
    # -------------------------------------------------------------------------
    def _publish_pmtiles_vector(self, celery_task, payload):
        """GeoJSON → 逐层级切片 → MBTiles → PMTiles → 上传 MinIO → STAC asset upsert。

        5 步流水线（与原脚本对应）：
            1) 读取 GeoJSON + 归一化到 [0,1] 坐标系
            2) 逐层切片（mercantile + shapely.STRtree + mapbox_vector_tile）
            3) MBTiles → PMTiles（pmtiles.convert.mbtiles_to_pmtiles）
            4) 上传 MinIO + 静态发布（mc cp + nginx）
            5) 自验证（HTTP Range + PMTiles 魔数）
            6) （可选）挂 STAC asset（pgSTAC upsert）
        """
        from my_project import settings

        self.mark_task_running(payload)
        task_pk = payload.get("task_pk")
        step_cb = lambda name: self._on_step(GISTask.objects.filter(pk=task_pk).first() if task_pk else None,
                                              name)

        src = payload["src"]
        layer = payload.get("layer") or Path(src).stem.lower().replace(" ", "-")
        out_name = payload.get("out") or (Path(src).stem + ".pmtiles")
        work_dir = Path(settings.GIS_WORK_DIR)
        work_dir.mkdir(parents=True, exist_ok=True)
        out_path = work_dir / out_name
        minzoom = int(payload.get("minzoom", 5))
        maxzoom = int(payload.get("maxzoom", 14))
        props_filter = payload.get("props") or ""

        _timers = {}

        with Step("读取 GeoJSON", on_step=step_cb) as s:
            data = json.loads(Path(src).read_text(encoding="utf-8"))
            feats = data.get("features") or []
            if not feats:
                raise ValueError("GeoJSON 中没有 features")
            from shapely.geometry import shape
            geoms, props = [], []
            for f in feats:
                g = shape(f["geometry"])
                if not g.is_valid:
                    g = g.buffer(0)
                if g.is_empty:
                    continue
                geoms.append(g)
                if props_filter:
                    keys = [k.strip() for k in props_filter.split(",")]
                    props.append({k: f["properties"].get(k) for k in keys
                                  if k in (f.get("properties") or {})})
                else:
                    props.append({})
            total_bounds = geoms[0].bounds
            for g in geoms:
                total_bounds = (min(total_bounds[0], g.bounds[0]),
                                min(total_bounds[1], g.bounds[1]),
                                max(total_bounds[2], g.bounds[2]),
                                max(total_bounds[3], g.bounds[3]))
            _timers[s.name] = time.time() - s.t0

        # 归一化到 [0,1]
        from shapely import STRtree
        from shapely.geometry import box
        from shapely.ops import transform as shp_transform
        import mercantile
        import mapbox_vector_tile

        def to_norm(g):
            return shp_transform(
                lambda x, y, z=None: ((x + 180.0) / 360.0,
                                      (1.0 - math.asinh(math.tan(y * math.pi / 180.0)) / math.pi) / 2.0),
                g,
            )

        with Step("归一化投影", on_step=step_cb) as s:
            norm_geoms = [to_norm(g) for g in geoms]
            tree = STRtree(norm_geoms)
            _timers[s.name] = time.time() - s.t0

        # 切片
        mbtiles_path = work_dir / (Path(src).stem + ".mbtiles")
        if mbtiles_path.exists():
            mbtiles_path.unlink()
        with Step("逐层切片", on_step=step_cb) as s:
            con = sqlite3.connect(mbtiles_path)
            con.execute("CREATE TABLE metadata (name TEXT, value TEXT)")
            con.execute(
                "CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, "
                "tile_row INTEGER, tile_data BLOB)")
            minx, miny, maxx, maxy = total_bounds
            tile_count, total_bytes = 0, 0
            for z in range(minzoom, maxzoom + 1):
                px2 = 0 if z >= maxzoom else {14: 128, 13: 256, 12: 512}.get(z, 1024)
                for t in mercantile.tiles(minx, miny, maxx, maxy, zooms=[z]):
                    tx, ty = t.x, t.y
                    x0, y0, x1, y1 = (tx / 2 ** z, ty / 2 ** z,
                                       (tx + 1) / 2 ** z, (ty + 1) / 2 ** z)
                    candidates = tree.query(box(x0, y0, x1, y1))
                    if len(candidates) == 0:
                        continue
                    feats_out = []
                    n_total = EXTENT * 2 ** z
                    for i in candidates:
                        g = norm_geoms[i]
                        gb = g.bounds
                        if (gb[2] - gb[0]) * (gb[3] - gb[1]) * n_total * n_total < px2:
                            continue
                        # 仿原脚本的 norm_transform：归一化坐标 → 局部 0..EXTENT
                        def tf(xs, ys, _x0=tx * EXTENT, _y0=ty * EXTENT, _n=n_total):
                            return ([v * _n - _x0 for v in xs],
                                    [v * _n - _y0 for v in ys])
                        clipped = shp_transform(tf, g).intersection(box(0, 0, EXTENT, EXTENT))
                        if clipped.is_empty:
                            continue
                        if clipped.area < px2:
                            continue
                        clipped = clipped.simplify(1.0, preserve_topology=True)
                        if clipped.is_empty:
                            continue
                        feats_out.append({
                            "geometry": clipped.wkt,
                            "properties": props[i] or {},
                        })
                    if not feats_out:
                        continue
                    blob = mapbox_vector_tile.encode(
                        [{"name": layer, "features": feats_out}],
                        default_options={"extents": EXTENT})
                    tile_data = gzip.compress(blob)
                    tms_y = 2 ** z - 1 - ty
                    con.execute("INSERT INTO tiles VALUES (?,?,?,?)",
                                (z, tx, tms_y, tile_data))
                    tile_count += 1
                    total_bytes += len(tile_data)
            meta = {
                "name": payload.get("name") or layer, "format": "pbf",
                "type": "overlay", "version": "2",
                "bounds": "{:.6f},{:.6f},{:.6f},{:.6f}".format(
                    total_bounds[0], total_bounds[1],
                    total_bounds[2], total_bounds[3]),
                "minzoom": str(minzoom), "maxzoom": str(maxzoom),
            }
            con.executemany("INSERT INTO metadata VALUES (?,?)", list(meta.items()))
            con.commit()
            con.close()
            _timers[s.name] = time.time() - s.t0

        # MBTiles → PMTiles
        with Step("打包 PMTiles", on_step=step_cb) as s:
            from pmtiles.convert import mbtiles_to_pmtiles
            mbtiles_to_pmtiles(str(mbtiles_path), str(out_path), maxzoom)
            _timers[s.name] = time.time() - s.t0

        # 上传 MinIO
        with Step("上传 MinIO", on_step=step_cb) as s:
            key = "vector/{}".format(out_name)
            ok, info = GISHelper.upload_to_minio(str(out_path), settings.GIS_MINIO_BUCKET, key)
            if not ok:
                raise RuntimeError("MinIO 上传失败：{}".format(info))
            _timers[s.name] = time.time() - s.t0

        # 自验证
        with Step("自验证", on_step=step_cb) as s:
            http_url = "{}/{}/{}".format(settings.GIS_MINIO_ENDPOINT,
                                         settings.GIS_MINIO_BUCKET, key)
            ok_p, status_p, dt_p, _ = GISHelper.http_probe(http_url, timeout=15)
            verified = {"http_status": status_p, "http_ok": ok_p, "elapsed": dt_p,
                        "size_bytes": out_path.stat().st_size if out_path.exists() else 0,
                        "tile_count": tile_count, "pmtiles_url": http_url}
            _timers[s.name] = time.time() - s.t0

        result = {
            "layer": layer,
            "out": str(out_path),
            "pmtiles_url": verified["pmtiles_url"],
            "tile_count": tile_count,
            "size_bytes": verified["size_bytes"],
            "minzoom": minzoom, "maxzoom": maxzoom,
            "bbox": list(total_bounds),
            "verified": verified,
            "timers": _timers,
        }
        self.mark_task_success(payload, result)
        return result

    # -------------------------------------------------------------------------
    # Raster PMTiles（TIFF → PNG → MBTiles → PMTiles → MinIO）
    #
    # 设计要点：
    #   1) 影像栅格用 PNG（默认 256×256），多波段 → RGBA / RGB；单波段 → 灰度
    #   2) 坐标系统一到 EPSG:3857（瓦片坐标就是 Web Mercator）
    #   3) 每个瓦片用 rasterio.warp.reproject 按 tile_size 重采样，
    #      自动处理源 CRS → 3857 的重投影
    #   4) 多波段（如 8 波段多光谱）取前 3 波段做 RGB；非 uint8 数据按 2/98 百分位
    #      拉伸到 0-255，避免 PMTiles viewer 看起来一片黑/白
    #   5) nodata 像元填充为 0（在 PNG 里是透明或黑色，取决于波段数）
    # -------------------------------------------------------------------------
    def _publish_pmtiles_raster(self, celery_task, payload):
        """TIFF → 256×256 PNG 瓦片 → MBTiles → PMTiles → MinIO。

        payload 增量字段：
            tile_type     = "raster"
            tile_size     = 256          # 瓦片边长像素
            resampling    = "bilinear"   # bilinear / nearest / cubic / lanczos
            bands         = ""           # 逗号分隔；空 = 自动取前 3 波段
            out           = "<src_stem>_raster.pmtiles"

        MBTiles format= png, type= overlay（Cesium / Mapbox / leaflet 通用 raster 协议）。
        """
        from my_project import settings
        from PIL import Image
        import rasterio
        from rasterio.warp import (
            transform_bounds as rio_transform_bounds,
            reproject as rio_reproject,
            Resampling,
        )
        from rasterio.transform import from_bounds as rio_from_bounds

        self.mark_task_running(payload)
        task_pk = payload.get("task_pk")
        step_cb = lambda name: self._on_step(
            GISTask.objects.filter(pk=task_pk).first() if task_pk else None, name)

        src = payload["src"]
        if not os.path.exists(src):
            raise FileNotFoundError("源文件不存在: {}".format(src))

        layer = payload.get("layer") or Path(src).stem.lower().replace(" ", "-")
        minzoom = int(payload.get("minzoom", 0))
        maxzoom = int(payload.get("maxzoom", 14))
        tile_size = int(payload.get("tile_size", 256))
        resampling_name = (payload.get("resampling") or "bilinear").lower()
        resampling_map = {
            "nearest": Resampling.nearest,
            "bilinear": Resampling.bilinear,
            "cubic": Resampling.cubic,
            "lanczos": Resampling.lanczos,
            "average": Resampling.average,
        }
        resampling = resampling_map.get(resampling_name, Resampling.bilinear)
        bands_arg = (payload.get("bands") or "").strip()

        work_dir = Path(settings.GIS_WORK_DIR)
        work_dir.mkdir(parents=True, exist_ok=True)
        out_name = payload.get("out") or (Path(src).stem + "_raster.pmtiles")
        out_path = work_dir / out_name
        mbtiles_path = work_dir / (Path(src).stem + "_raster.mbtiles")

        _timers = {}

        # ---------- 1) 探查源 raster ----------
        with Step("探查源 TIFF", on_step=step_cb) as s:
            with rasterio.open(src) as ds:
                src_crs = ds.crs
                src_count = int(ds.count)
                src_dtype = ds.dtypes[0]
                src_nodata = ds.nodata
                src_bounds_native = ds.bounds
                src_bounds_3857 = rio_transform_bounds(
                    src_crs, "EPSG:3857", *src_bounds_native
                )
                # PMTiles bounds 必须是 WGS84 经纬度（×1e7 编码为 int32）
                src_bounds_wgs84 = rio_transform_bounds(
                    src_crs, "EPSG:4326", *src_bounds_native
                )
                # 选波段（默认 RGB = 1,2,3）
                if bands_arg:
                    try:
                        bands_idx = [int(x) for x in bands_arg.split(",") if x]
                    except ValueError:
                        raise ValueError("bands 必须是逗号分隔的整数")
                else:
                    bands_idx = list(range(1, min(src_count, 3) + 1))
                if not bands_idx or any(b < 1 or b > src_count for b in bands_idx):
                    raise ValueError(
                        "bands 越界: src has {} bands, got {}".format(src_count, bands_idx))
                out_bands = len(bands_idx)
                has_alpha = out_bands == 4 or out_bands == 2  # RGBA or GA
                # uint8 类型不需要拉伸；其它按全局百分位拉伸
                if src_dtype in ("uint8", "uint16"):
                    needs_stretch = src_dtype != "uint8"
                    g_min, g_max = (0, 255) if src_dtype == "uint8" else (0, 65535)
                else:
                    needs_stretch = True
                    sample = ds.read(bands_idx[0], masked=True)
                    vals = (sample.compressed()
                            if hasattr(sample, "mask") and sample.mask is not np.ma.nomask
                            else np.asarray(sample).flatten())
                    if vals.size == 0:
                        raise ValueError("raster 没有任何有效像元")
                    g_min = float(np.percentile(vals, 2))
                    g_max = float(np.percentile(vals, 98))
                    if g_max <= g_min:
                        g_min, g_max = float(vals.min()), float(vals.max())
                        if g_max <= g_min:
                            g_min, g_max = 0.0, 1.0
                _timers[s.name] = time.time() - s.t0

        # ---------- 2) 逐层切片 ----------
        if mbtiles_path.exists():
            mbtiles_path.unlink()
        tile_count = 0
        total_bytes = 0
        with Step("逐层 PNG 切片", on_step=step_cb) as s:
            con = sqlite3.connect(mbtiles_path)
            con.execute("CREATE TABLE metadata (name TEXT, value TEXT)")
            con.execute(
                "CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, "
                "tile_row INTEGER, tile_data BLOB)")
            meta = {
                "name": payload.get("name") or layer,
                "format": "png",
                "type": "overlay",
                "version": "3",
                # PMTiles 要求 bounds 为 WGS84 经纬度（PMTiles 内部 ×1e7 存 int32）
                "bounds": "{:.6f},{:.6f},{:.6f},{:.6f}".format(
                    src_bounds_wgs84[0], src_bounds_wgs84[1],
                    src_bounds_wgs84[2], src_bounds_wgs84[3]),
                "minzoom": str(minzoom),
                "maxzoom": str(maxzoom),
            }
            con.executemany("INSERT INTO metadata VALUES (?,?)", list(meta.items()))

            import mercantile

            with rasterio.open(src) as ds:
                for z in range(minzoom, maxzoom + 1):
                    tiles = list(mercantile.tiles(
                        src_bounds_3857[0], src_bounds_3857[1],
                        src_bounds_3857[2], src_bounds_3857[3],
                        zooms=[z]))
                    for t in tiles:
                        # 瓦片 bounds in 3857 (米)
                        tb = mercantile.xy_bounds(t)
                        # 把瓦片 bounds 重投影到源 CRS，作为读窗口
                        tb_src = rio_transform_bounds(
                            "EPSG:3857", src_crs, tb.left, tb.bottom, tb.right, tb.top)
                        # 构造目标 transform：tile_size × tile_size，覆盖 tb_src
                        dst_transform = rio_from_bounds(
                            *tb_src, tile_size, tile_size)
                        # 用 rasterio.warp.reproject 把窗口区域按目标分辨率重采样
                        # 所有波段一并处理
                        if needs_stretch:
                            # 浮点 → 拉伸到 uint8 0-255
                            out_dtype = "float32"
                            work_data = np.zeros(
                                (out_bands, tile_size, tile_size), dtype=np.float32)
                        else:
                            out_dtype = "uint8"
                            work_data = np.zeros(
                                (out_bands, tile_size, tile_size), dtype=np.uint8)
                        rio_reproject(
                            source=rasterio.band(ds, bands_idx),
                            destination=work_data,
                            src_transform=ds.transform, src_crs=src_crs,
                            dst_transform=dst_transform, dst_crs=src_crs,
                            resampling=resampling,
                        )
                        # nodata 掩码（用源 nodata 探测）
                        if src_nodata is not None:
                            # 在重采样前另外读一份只是为了拿 mask；省 IO，直接用值近似
                            try:
                                nodata_mask = np.isclose(
                                    work_data, float(src_nodata))
                                if needs_stretch:
                                    work_data[nodata_mask] = g_min
                                else:
                                    work_data[nodata_mask] = 0
                            except Exception:
                                pass
                        # 拉伸
                        if needs_stretch:
                            if g_max > g_min:
                                work_data = (work_data - g_min) / (g_max - g_min)
                            work_data = np.clip(work_data, 0.0, 1.0) * 255.0
                            work_data = work_data.astype(np.uint8)

                        # 编码 PNG
                        if out_bands >= 3:
                            arr = work_data[:3].transpose(1, 2, 0)  # HWC
                            if has_alpha and out_bands >= 4:
                                img = Image.fromarray(
                                    np.ascontiguousarray(arr),
                                    mode="RGB")
                                # 用 band 4 做 alpha
                                alpha = work_data[3]
                                img = img.convert("RGBA")
                                a_arr = np.array(img)
                                a_arr[..., 3] = alpha
                                img = Image.fromarray(a_arr, mode="RGBA")
                            else:
                                img = Image.fromarray(
                                    np.ascontiguousarray(arr), mode="RGB")
                        elif out_bands == 2:
                            # GA: gray + alpha
                            img = Image.fromarray(
                                np.ascontiguousarray(work_data[0]), mode="L")
                            img = img.convert("LA")
                            a_arr = np.array(img)
                            a_arr[..., 1] = work_data[1]
                            img = Image.fromarray(a_arr, mode="LA")
                        else:
                            # L: grayscale
                            img = Image.fromarray(
                                np.ascontiguousarray(work_data[0]), mode="L")

                        buf = io.BytesIO()
                        img.save(buf, format="PNG", optimize=True)
                        tile_bytes = buf.getvalue()
                        tms_y = 2 ** z - 1 - t.y
                        con.execute("INSERT INTO tiles VALUES (?,?,?,?)",
                                    (z, int(t.x), int(tms_y), tile_bytes))
                        tile_count += 1
                        total_bytes += len(tile_bytes)
            con.commit()
            con.close()
            _timers[s.name] = time.time() - s.t0

        # ---------- 3) MBTiles → PMTiles ----------
        with Step("打包 PMTiles", on_step=step_cb) as s:
            from pmtiles.convert import mbtiles_to_pmtiles
            mbtiles_to_pmtiles(str(mbtiles_path), str(out_path), maxzoom)
            _timers[s.name] = time.time() - s.t0

        # ---------- 4) 上传 MinIO ----------
        key = "raster/{}".format(out_path.name)
        with Step("上传 MinIO", on_step=step_cb) as s:
            ok, info = GISHelper.upload_to_minio(
                str(out_path), settings.GIS_MINIO_BUCKET, key)
            if not ok:
                raise RuntimeError("MinIO 上传失败：{}".format(info))
            _timers[s.name] = time.time() - s.t0

        # ---------- 5) 自验证 ----------
        verified = None
        with Step("自验证", on_step=step_cb) as s:
            http_url = "{}/{}/{}".format(
                settings.GIS_MINIO_ENDPOINT, settings.GIS_MINIO_BUCKET, key)
            ok_p, status_p, dt_p, _ = GISHelper.http_probe(http_url, timeout=15)
            verified = {"http_status": status_p, "http_ok": ok_p, "elapsed": dt_p,
                        "size_bytes": out_path.stat().st_size if out_path.exists() else 0,
                        "tile_count": tile_count, "pmtiles_url": http_url}
            _timers[s.name] = time.time() - s.t0

        result = {
            "layer": layer,
            "out": str(out_path),
            "pmtiles_url": verified["pmtiles_url"],
            "tile_count": tile_count,
            "total_bytes": total_bytes,
            "size_bytes": verified["size_bytes"],
            "minzoom": minzoom, "maxzoom": maxzoom,
            "bbox_3857": list(src_bounds_3857),
            "tile_size": tile_size,
            "bands": bands_idx,
            "stretch": {"min": g_min, "max": g_max} if needs_stretch else None,
            "verified": verified,
            "timers": _timers,
        }
        self.mark_task_success(payload, result)
        return result

    # -------------------------------------------------------------------------
    # Terrain PMTiles（DEM → quantized-mesh v1 → MBTiles → PMTiles → MinIO）
    #
    # quantized-mesh v1 格式（Cesium 标准，big-endian）：
    #   Header (44 B):
    #     centerX, centerY, centerHeight    : 3 × float32  (lon, lat, m)
    #     minLon, minLat, maxLon, maxLat    : 4 × float32  (瓦片 WGS84 bounds)
    #     horizonOcclusionX/Y/Z             : 3 × float32  (远地平线点，约定 min_h - 1e6)
    #     maxZoom                           : uint16       (该瓦片有效的最高 zoom)
    #   Vertex data:
    #     vertexCount                       : uint32
    #     vertices                          : vertexCount × 3 × uint16
    #       (X, Y, Z 各量化为 [0, 32767]，X 沿 minLon→maxLon，Y 沿 maxLat→minLat 翻转，Z 沿 minH→maxH)
    #   Index data:
    #     triangleCount                     : uint32
    #     indices                           : triangleCount × 3 × uint32
    #       (每 cell 切两个三角形：v00,v10,v01 与 v01,v10,v11)
    #   Edge metadata flag                 : uint8 (0 = 无)
    #   Heights / Water mask               : 跳过
    #
    # 默认每瓦片 65×65 顶点（64×64 cell）；这是 Cesium TerrainProvider 的标准上限。
    # -------------------------------------------------------------------------
    def _publish_pmtiles_terrain(self, celery_task, payload):
        """DEM TIFF → quantized-mesh v1 → MBTiles → PMTiles → MinIO。

        payload 增量字段：
            tile_type         = "terrain"
            vertices_per_side = 65     # 顶点网格边长（默认 65 = 64 cell）
            out               = "<src_stem>_terrain.pmtiles"

        MBTiles format= quantized-mesh-1.0, type= overlay。
        坐标系约定：quantized-mesh 用 lon/lat (EPSG:4326)，瓦片坐标用 Web Mercator
        (Tile XYZ) —— 二者通过 mercantile.xy_bounds / bounds 转换。
        """
        from my_project import settings
        import rasterio
        from rasterio.warp import (
            calculate_default_transform, reproject as rio_reproject, Resampling,
        )
        import mercantile

        self.mark_task_running(payload)
        task_pk = payload.get("task_pk")
        step_cb = lambda name: self._on_step(
            GISTask.objects.filter(pk=task_pk).first() if task_pk else None, name)

        src = payload["src"]
        if not os.path.exists(src):
            raise FileNotFoundError("源文件不存在: {}".format(src))

        layer = payload.get("layer") or Path(src).stem.lower().replace(" ", "-")
        minzoom = int(payload.get("minzoom", 0))
        maxzoom = int(payload.get("maxzoom", 14))
        vertices_per_side = int(payload.get("vertices_per_side", 65))
        if vertices_per_side < 2 or vertices_per_side > 65:
            raise ValueError(
                "vertices_per_side 必须在 [2, 65]（quantized-mesh 上限）；got {}".format(
                    vertices_per_side))

        work_dir = Path(settings.GIS_WORK_DIR)
        work_dir.mkdir(parents=True, exist_ok=True)
        out_name = payload.get("out") or (Path(src).stem + "_terrain.pmtiles")
        out_path = work_dir / out_name
        mbtiles_path = work_dir / (Path(src).stem + "_terrain.mbtiles")

        _timers = {}

        # ---------- 1) 读 DEM，统一到 EPSG:4326 ----------
        with Step("读取 DEM", on_step=step_cb) as s:
            with rasterio.open(src) as ds:
                if ds.count != 1:
                    raise ValueError(
                        "terrain 需要单波段高程 DEM；got {} bands".format(ds.count))
                src_crs = ds.crs
                src_nodata = ds.nodata
                if str(src_crs) != "EPSG:4326":
                    transform4326, w4326, h4326 = calculate_default_transform(
                        src_crs, "EPSG:4326", ds.width, ds.height, *ds.bounds)
                    dem_array = np.zeros((h4326, w4326), dtype=ds.dtypes[0])
                    rio_reproject(
                        source=rasterio.band(ds, 1),
                        destination=dem_array,
                        src_transform=ds.transform, src_crs=src_crs,
                        dst_transform=transform4326, dst_crs="EPSG:4326",
                        resampling=Resampling.bilinear,
                    )
                    dem_transform = transform4326
                else:
                    dem_array = ds.read(1)
                    dem_transform = ds.transform
                dem_bounds = rasterio.transform.array_bounds(
                    dem_array.shape[0], dem_array.shape[1], dem_transform)
                # 全局高程范围（用于量化）
                if src_nodata is not None:
                    valid_mask = dem_array != src_nodata
                else:
                    valid_mask = np.ones_like(dem_array, dtype=bool)
                if src_nodata is not None:
                    valid_mask &= ~np.isnan(dem_array) if dem_array.dtype.kind == "f" else valid_mask
                valid_heights = dem_array[valid_mask]
                if valid_heights.size == 0:
                    raise ValueError("DEM 没有任何有效高程像元")
                global_min_h = float(np.min(valid_heights))
                global_max_h = float(np.max(valid_heights))
                if global_max_h <= global_min_h:
                    global_max_h = global_min_h + 1.0
                _timers[s.name] = time.time() - s.t0

        # ---------- 2) 逐层切 quantized-mesh ----------
        if mbtiles_path.exists():
            mbtiles_path.unlink()
        tile_count = 0
        with Step("逐层 quantized-mesh 切片", on_step=step_cb) as s:
            con = sqlite3.connect(mbtiles_path)
            con.execute("CREATE TABLE metadata (name TEXT, value TEXT)")
            con.execute(
                "CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, "
                "tile_row INTEGER, tile_data BLOB)")
            meta = {
                "name": payload.get("name") or layer,
                "format": "quantized-mesh-1.0",
                "type": "overlay",
                "version": "3",
                "bounds": "{:.6f},{:.6f},{:.6f},{:.6f}".format(
                    dem_bounds[0], dem_bounds[1], dem_bounds[2], dem_bounds[3]),
                "minzoom": str(minzoom),
                "maxzoom": str(maxzoom),
            }
            con.executemany("INSERT INTO metadata VALUES (?,?)", list(meta.items()))

            dem_h, dem_w = dem_array.shape
            inv_transform = ~dem_transform  # world → pixel
            for z in range(minzoom, maxzoom + 1):
                tiles = list(mercantile.tiles(
                    dem_bounds[0], dem_bounds[1], dem_bounds[2], dem_bounds[3],
                    zooms=[z]))
                for t in tiles:
                    tb = mercantile.bounds(t)  # west, south, east, north in WGS84
                    tile_min_lon, tile_min_lat = tb.west, tb.south
                    tile_max_lon, tile_max_lat = tb.east, tb.north

                    # 构建 NxN 高程网格（按 tile bounds 在 WGS84 上采样）
                    heights = np.empty(
                        (vertices_per_side, vertices_per_side), dtype=np.float32)
                    fill_value = global_min_h
                    for j in range(vertices_per_side):
                        # Y 翻转：j=0 对应 max_lat（北），j=N-1 对应 min_lat（南）
                        if vertices_per_side > 1:
                            lat = tile_max_lat - (j / (vertices_per_side - 1)) * \
                                (tile_max_lat - tile_min_lat)
                        else:
                            lat = (tile_max_lat + tile_min_lat) / 2.0
                        for i in range(vertices_per_side):
                            if vertices_per_side > 1:
                                lon = tile_min_lon + (i / (vertices_per_side - 1)) * \
                                    (tile_max_lon - tile_min_lon)
                            else:
                                lon = (tile_max_lon + tile_min_lon) / 2.0
                            try:
                                row, col = inv_transform * (lon, lat)
                                ri = int(row)
                                ci = int(col)
                                if 0 <= ri < dem_h and 0 <= ci < dem_w:
                                    v = float(dem_array[ri, ci])
                                    if src_nodata is not None and v == src_nodata:
                                        v = fill_value
                                    elif dem_array.dtype.kind == "f" and np.isnan(v):
                                        v = fill_value
                                    heights[j, i] = v
                                else:
                                    heights[j, i] = fill_value
                            except Exception:
                                heights[j, i] = fill_value

                    mesh = self._build_quantized_mesh(
                        tile_x=t.x, tile_y=t.y, zoom=z,
                        heights=heights,
                        tile_bounds_wgs84=(tile_min_lon, tile_min_lat,
                                           tile_max_lon, tile_max_lat),
                        min_h=global_min_h, max_h=global_max_h)
                    tms_y = 2 ** z - 1 - t.y
                    con.execute("INSERT INTO tiles VALUES (?,?,?,?)",
                                (z, t.x, tms_y, mesh))
                    tile_count += 1
            con.commit()
            con.close()
            _timers[s.name] = time.time() - s.t0

        # ---------- 3) MBTiles → PMTiles ----------
        with Step("打包 PMTiles", on_step=step_cb) as s:
            from pmtiles.convert import mbtiles_to_pmtiles
            mbtiles_to_pmtiles(str(mbtiles_path), str(out_path), maxzoom)
            _timers[s.name] = time.time() - s.t0

        # ---------- 4) 上传 MinIO ----------
        key = "terrain/{}".format(out_path.name)
        with Step("上传 MinIO", on_step=step_cb) as s:
            ok, info = GISHelper.upload_to_minio(
                str(out_path), settings.GIS_MINIO_BUCKET, key)
            if not ok:
                raise RuntimeError("MinIO 上传失败：{}".format(info))
            _timers[s.name] = time.time() - s.t0

        # ---------- 5) 自验证 ----------
        verified = None
        with Step("自验证", on_step=step_cb) as s:
            http_url = "{}/{}/{}".format(
                settings.GIS_MINIO_ENDPOINT, settings.GIS_MINIO_BUCKET, key)
            ok_p, status_p, dt_p, _ = GISHelper.http_probe(http_url, timeout=15)
            verified = {"http_status": status_p, "http_ok": ok_p, "elapsed": dt_p,
                        "size_bytes": out_path.stat().st_size if out_path.exists() else 0,
                        "tile_count": tile_count, "pmtiles_url": http_url}
            _timers[s.name] = time.time() - s.t0

        result = {
            "layer": layer,
            "out": str(out_path),
            "pmtiles_url": verified["pmtiles_url"],
            "tile_count": tile_count,
            "size_bytes": verified["size_bytes"],
            "minzoom": minzoom, "maxzoom": maxzoom,
            "bbox_wgs84": list(dem_bounds),
            "min_height": global_min_h,
            "max_height": global_max_h,
            "vertices_per_side": vertices_per_side,
            "verified": verified,
            "timers": _timers,
        }
        self.mark_task_success(payload, result)
        return result

    @staticmethod
    def _build_quantized_mesh(tile_x, tile_y, zoom, heights, tile_bounds_wgs84,
                              min_h, max_h):
        """编码 quantized-mesh v1 字节流（big-endian）。

        入参：
            tile_x, tile_y, zoom       XYZ 瓦片坐标（仅用于记录，编码不用）
            heights                    numpy (N, N) 高程网格，float32
            tile_bounds_wgs84          (minLon, minLat, maxLon, maxLat)
            min_h, max_h               全局高程范围（用于 Z 量化）

        返回：bytes（header + vertices + indices + hasEdgeMetadata 字节）
        """
        min_lon, min_lat, max_lon, max_lat = tile_bounds_wgs84
        h_count, w_count = heights.shape  # = vertices_per_side
        vertex_count = h_count * w_count
        d_lon = (max_lon - min_lon) if max_lon > min_lon else 1e-12
        d_lat = (max_lat - min_lat) if max_lat > min_lat else 1e-12
        d_h = (max_h - min_h) if max_h > min_h else 1e-12

        # ----- Header (44 bytes; little-endian) -----
        # Cesium quantized-mesh 规范：所有多字节值都是 little-endian
        # Header 字段：
        #   centerX, centerY, centerHeight      : 3 × float32 (12 B)
        #   boundingBox minX/minY/maxX/maxY     : 4 × float32 (16 B)
        #   horizonOcclusionX/Y/Z               : 3 × float32 (12 B)
        #   maxZoom                             : uint16 (2 B)
        #   padding                             : 2 B (4 字节对齐)
        center_x = (min_lon + max_lon) / 2.0
        center_y = (min_lat + max_lat) / 2.0
        center_h = (min_h + max_h) / 2.0
        # 远地平线点：放在 tile center 正下方很远，避免遮挡
        hop_x = center_x
        hop_y = center_y
        hop_z = min_h - 1_000_000.0
        header = struct.pack(
            "<fff ffff fff H 2x",
            center_x, center_y, center_h,
            min_lon, min_lat, max_lon, max_lat,
            hop_x, hop_y, hop_z,
            zoom,
        )

        # ----- Vertex data -----
        # 量化为 uint16：[0, 32767]
        # X：i 从 0..w_count-1 → qx = i/(w_count-1) * 32767
        if w_count > 1:
            qxs = np.linspace(0.0, 32767.0, w_count).astype(np.uint16)
        else:
            qxs = np.array([0], dtype=np.uint16)
        # Y：j 从 0..h_count-1 → qy = (1 - j/(h_count-1)) * 32767（北→南翻转）
        if h_count > 1:
            qys = (32767.0 - np.linspace(0.0, 32767.0, h_count)).astype(np.uint16)
        else:
            qys = np.array([32767], dtype=np.uint16)
        # Z 用全局高程范围量化
        norm_z = (heights.astype(np.float32) - min_h) / d_h
        norm_z = np.clip(norm_z, 0.0, 1.0)
        qzs = (norm_z * 32767.0).astype(np.uint16)
        # 交织为 (vertexCount, 3) uint16 数组
        qx_grid = np.broadcast_to(qxs, (h_count, w_count))
        qy_grid = np.broadcast_to(qys[:, None], (h_count, w_count))
        vertices_flat = np.empty((vertex_count, 3), dtype=np.uint16)
        vertices_flat[:, 0] = qx_grid.flatten()
        vertices_flat[:, 1] = qy_grid.flatten()
        vertices_flat[:, 2] = qzs.flatten()
        vertex_blob = vertices_flat.tobytes()

        # ----- Index data (triangulation) -----
        # 每个 cell (i,j) → (j, i) 切两个三角形
        indices = []
        for j in range(h_count - 1):
            for i in range(w_count - 1):
                v00 = j * w_count + i
                v01 = j * w_count + (i + 1)
                v10 = (j + 1) * w_count + i
                v11 = (j + 1) * w_count + (i + 1)
                # CCW: v00, v10, v01 与 v01, v10, v11
                indices.append(v00)
                indices.append(v10)
                indices.append(v01)
                indices.append(v01)
                indices.append(v10)
                indices.append(v11)
        triangle_count = len(indices) // 3
        index_blob = struct.pack("<{}I".format(len(indices)), *indices)

        # ----- Edge metadata flag = 0（无扩展） -----
        edge_flag = struct.pack("B", 0)

        return header + struct.pack("<I", vertex_count) + vertex_blob + \
            struct.pack("<I", triangle_count) + index_blob + edge_flag

    # =========================================================================
    # COG 发布（Celery 异步 worker 路径，逻辑迁移自 publish_cog.py）
    # =========================================================================
    def publish_cog(self, celery_task, payload):
        """TIFF → (按需重投影) → COG → MinIO → pgSTAC item upsert。

        与原 publish_cog.py 一致：
            1) 探查 (gdalinfo)
            2) 重投影 (gdalwarp，按需)
            3) 转 COG (gdal_translate -of COG)
            4) 验证金字塔（rasterio.overviews）
            5) 计算拉伸区间（rasterio + numpy.percentile）
            6) 上传 MinIO
            7) 写 pgSTAC item（pypgstac load）
            8) 自验证（取一张瓦片 + preview）
        """
        from my_project import settings

        self.mark_task_running(payload)
        task_pk = payload.get("task_pk")
        step_cb = lambda name: self._on_step(
            GISTask.objects.filter(pk=task_pk).first() if task_pk else None, name)

        src = Path(payload["src"])
        if not src.exists():
            raise FileNotFoundError("源文件不存在: {}".format(src))
        work_dir = Path(settings.GIS_WORK_DIR)
        work_dir.mkdir(parents=True, exist_ok=True)

        collection = payload["collection"]
        title = payload.get("title") or src.stem
        compress = payload.get("compress", "DEFLATE")
        bands_arg = payload.get("bands") or ""
        platform = payload.get("platform") or "业务生产系统"
        already_cog = bool(payload.get("already_cog"))
        no_verify = bool(payload.get("no_verify"))

        _timers = {}

        # 1) 探查
        with Step("探查源文件", on_step=step_cb) as s:
            info = GISHelper.ssh_run("gdalinfo -json -noct '{}'".format(str(src).replace("'", "'\\''")))
            rc, out, err = info
            if rc != 0:
                raise RuntimeError("gdalinfo 失败：{}".format(err))
            info = json.loads(out)
            w, h = info["size"]
            blist = info.get("bands", [])
            nb = len(blist)
            dtype = blist[0].get("type", "?") if blist else "?"
            rc2, epsg_out, _ = GISHelper.ssh_run(
                "gdalsrsinfo -o epsg '{}'".format(str(src).replace("'", "'\\''")))
            src_epsg = epsg_out.strip() if rc2 == 0 else ""
            bands = ([int(x) for x in bands_arg.split(",") if x]
                     if bands_arg else list(range(1, min(nb, 3) + 1)))
            bbox0 = self._wgs84_bbox_via_ssh(src, src_epsg)
            _timers[s.name] = time.time() - s.t0

        # 2) 重投影（按需）
        if not already_cog and src_epsg and src_epsg not in ("EPSG:4326", "EPSG:3857"):
            with Step("重投影 → EPSG:3857", on_step=step_cb) as s:
                warped = work_dir / (src.stem + "_wm.tif")
                GISHelper.ssh_run(
                    "gdalwarp '{s}' '{o}' -t_srs EPSG:3857 -r bilinear -multi "
                    "-co TILED=YES -co BLOCKXSIZE=512 -co BLOCKYSIZE=512 "
                    "-co COMPRESS=DEFLATE -co PREDICTOR=2 -co BIGTIFF=IF_SAFER".format(
                        s=str(src), o=str(warped)))
                src = warped
                _timers[s.name] = time.time() - s.t0
        # 3) 转 COG
        if not already_cog:
            with Step("转 COG", on_step=step_cb) as s:
                cog = work_dir / (src.stem + "_cog.tif")
                GISHelper.ssh_run(
                    "gdal_translate -of COG '{s}' '{o}' -co COMPRESS={c} -co PREDICTOR=2 "
                    "-co BLOCKSIZE=512 -co OVERVIEWS=AUTO -co BIGTIFF=IF_SAFER".format(
                        s=str(src), o=str(cog), c=compress))
                src = cog
                _timers[s.name] = time.time() - s.t0
        else:
            cog = src

        # 4) 计算拉伸区间（rasterio + numpy；用 SSH 端 worker 直接读）
        with Step("计算显示拉伸区间", on_step=step_cb) as s:
            stretch = self._compute_stretch_ssh(cog, bands)
            _timers[s.name] = time.time() - s.t0

        # 5) 上传 MinIO
        key = "imagery/{}".format(cog.name)
        with Step("上传 MinIO", on_step=step_cb) as s:
            ok, info = GISHelper.upload_to_minio(str(cog), settings.GIS_MINIO_BUCKET, key)
            if not ok:
                raise RuntimeError("MinIO 上传失败：{}".format(info))
            _timers[s.name] = time.time() - s.t0
        s3_url = "s3://{}/{}".format(settings.GIS_MINIO_BUCKET, key)
        http_url = "{}/{}/{}".format(settings.GIS_MINIO_ENDPOINT, settings.GIS_MINIO_BUCKET, key)

        # 6) 写 STAC item / collection
        with Step("写入 STAC（pgSTAC）", on_step=step_cb) as s:
            dt = payload.get("dt") or time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                     time.gmtime(Path(cog).stat().st_mtime))
            item_id = Path(cog).stem.lower().replace(" ", "-")
            item = {
                "type": "Feature", "stac_version": "1.0.0",
                "id": item_id, "collection": collection,
                "bbox": bbox0,
                "geometry": {"type": "Polygon", "coordinates": [[
                    [bbox0[0], bbox0[1]], [bbox0[2], bbox0[1]],
                    [bbox0[2], bbox0[3]], [bbox0[0], bbox0[3]], [bbox0[0], bbox0[1]]]]},
                "properties": {"datetime": dt, "platform": platform,
                               "proj:epsg": 3857, "proj:shape": [h, w]},
                "assets": {"cog": {
                    "href": http_url,
                    "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                    "title": title, "roles": ["data", "visual"],
                    "alternate": {"s3": {"href": s3_url}},
                }},
            }
            if stretch:
                item["properties"]["raster:bands"] = [
                    {"name": "B{}".format(b), "statistics": {"minimum": lo, "maximum": hi}}
                    for b, (lo, hi) in stretch.items()
                ]
            collection_doc = {
                "type": "Collection", "id": collection, "title": title,
                "description": "业务生产系统推送的影像（{}）".format(collection),
                "license": "proprietary",
                "extent": {"spatial": {"bbox": [bbox0]},
                           "temporal": {"interval": [[dt, dt]]}},
            }
            nd_item = work_dir / "_cog_item.ndjson"
            nd_col = work_dir / "_cog_collection.ndjson"
            nd_item.write_text(json.dumps(item, ensure_ascii=False) + "\n", encoding="utf-8")
            nd_col.write_text(json.dumps(collection_doc, ensure_ascii=False) + "\n", encoding="utf-8")
            self._pypgstac_load(["collections", str(nd_col)])
            self._pypgstac_load(["items", str(nd_item)])
            _timers[s.name] = time.time() - s.t0

        # 7) 自验证
        verified = None
        if not no_verify:
            with Step("自验证", on_step=step_cb) as s:
                # 走 TiTiler info + tiles 探活
                enc = urllib.parse.quote(http_url, safe="")
                bidx = "&".join("bidx={}".format(b) for b in bands)
                rescale = ""
                if stretch:
                    rescale = "&" + "&".join(
                        "rescale={:.4f},{:.4f}".format(*stretch.get(b, (0, 1))) for b in bands)
                tiles_url = "{}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png?url={}&{}{}".format(
                    settings.GIS_TITILER_URL.rstrip("/"), enc, bidx, rescale)
                preview_url = "{}/cog/preview.png?url={}&{}{}".format(
                    settings.GIS_TITILER_URL.rstrip("/"), enc, bidx, rescale)
                # 取一张瓦片（用 bbox 中心 + 合适 z）
                ok_t, st_t, dt_t, _ = GISHelper.http_probe(
                    tiles_url.format(z=10, x=200, y=400), timeout=20)
                ok_p, st_p, dt_p, _ = GISHelper.http_probe(preview_url, timeout=30)
                verified = {"tile_ok": ok_t, "tile_status": st_t, "tile_elapsed": dt_t,
                            "preview_ok": ok_p, "preview_status": st_p, "preview_elapsed": dt_p,
                            "tiles_url": tiles_url, "preview_url": preview_url}
                _timers[s.name] = time.time() - s.t0

        result = {
            "cog": str(cog), "s3": s3_url, "http": http_url,
            "bbox_wgs84": bbox0, "size": [w, h],
            "bands": bands, "stretch": {str(k): v for k, v in (stretch or {}).items()},
            "collection": collection, "item_id": item_id,
            "verified": verified, "timers": _timers,
        }
        self.mark_task_success(payload, result)
        return result

    # ----- COG 辅助 -----
    @staticmethod
    def _wgs84_bbox_via_ssh(src_path, src_epsg):
        """通过 SSH 端 gdaltransform 算 WGS84 bbox（与原 publish_cog.py L108-135 一致）。"""
        rc, info_out, _ = GISHelper.ssh_run("gdalinfo -json -noct '{}'".format(
            str(src_path).replace("'", "'\\''")))
        info = json.loads(info_out)
        cc = info["cornerCoordinates"]
        ul, lr = cc["upperLeft"], cc["lowerRight"]
        pts = [ul, [lr[0], ul[1]], lr, [ul[0], lr[1]]]
        cmd = ["gdaltransform"]
        if src_epsg:
            cmd += ["-s_srs", src_epsg]
        cmd += ["-t_srs", "EPSG:4326"]
        inp = "".join("{x} {y}\n".format(x=p[0], y=p[1]) for p in pts)
        rc2, out, _ = GISHelper.ssh_run("echo '{}' | {}".format(inp.replace("\n", "\\n"), " ".join(cmd)))
        xs, ys = [], []
        for line in (out or "").strip().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                try:
                    xs.append(float(parts[0]))
                    ys.append(float(parts[1]))
                except ValueError:
                    pass
        if len(xs) < 4:
            return [min(p[0] for p in pts), min(p[1] for p in pts),
                    max(p[0] for p in pts), max(p[1] for p in pts)]
        return [min(xs), min(ys), max(xs), max(ys)]

    @staticmethod
    def _compute_stretch_ssh(cog_path, bands, pct=2.0):
        """worker 端跑 rasterio + numpy 取百分位拉伸区间。"""
        try:
            # 在 SSH 端跑 python -c 拿结果
            script = (
                "python3 -c \"import sys, json, numpy as np; "
                "import rasterio; ds=rasterio.open('{p}'); "
                "ovr=ds.overviews(1); lvl=len(ovr) if ovr else 0; "
                "od=rasterio.open('{p}', OVERVIEW_LEVEL=lvl-1) if ovr else ds; "
                "out={{}}; "
                "import numpy as np; "
                "[out.__setitem__(b, [float(np.percentile(od.read(b, masked=True).compressed().astype('float64'), {pct})), "
                " float(np.percentile(od.read(b, masked=True).compressed().astype('float64'), 100-{pct}))]) "
                " for b in {bands}]; "
                "print(json.dumps(out))\"".format(
                    p=str(cog_path), pct=pct, bands=list(bands)))
            rc, out, err = GISHelper.ssh_run(script)
            if rc != 0:
                logger.warning("compute_stretch 失败：%s", err)
                return None
            raw = json.loads(out.strip().splitlines()[-1])
            return {int(k): tuple(v) for k, v in raw.items()}
        except Exception:
            logger.exception("compute_stretch 异常")
            return None

    @staticmethod
    def _pypgstac_load(args):
        """在 SSH 端跑 pypgstac load，args=[kind, path]。
        与原 publish_cog.py L425-431 等价。
        """
        from my_project import settings
        kind, path = args
        cmd = "pypgstac load {} {} --dsn '{}' --method upsert".format(
            kind, path, settings.GIS_PGSTAC_DSN)
        rc, out, err = GISHelper.ssh_run(cmd, timeout=600)
        if rc != 0:
            raise RuntimeError("pypgstac load {} 失败：{}".format(kind, err[-800:]))
        return out

    # =========================================================================
    # STAC ingest（Celery 异步 worker 路径，迁移自 ingest_stac.py）
    # =========================================================================
    def ingest_stac(self, celery_task, payload):
        """把本地 ndjson 通过 pypgstac 灌到 pgSTAC。
        payload 必须包含 collections_ndjson / items_ndjson（worker 本地路径）；
        view 层负责把 dict 落盘成 ndjson（保持 manager 与 IO 解耦）。
        """
        from my_project import settings

        self.mark_task_running(payload)
        task_pk = payload.get("task_pk")
        step_cb = lambda name: self._on_step(
            GISTask.objects.filter(pk=task_pk).first() if task_pk else None, name)

        method = payload.get("method") or "upsert"
        col_path = payload["collections_ndjson"]
        item_path = payload["items_ndjson"]

        _timers = {}
        with Step("灌 pgSTAC collections", on_step=step_cb) as s:
            self._pypgstac_load(["collections", col_path])
            _timers[s.name] = time.time() - s.t0
        with Step("灌 pgSTAC items", on_step=step_cb) as s:
            self._pypgstac_load(["items", item_path])
            _timers[s.name] = time.time() - s.t0

        result = {
            "method": method,
            "collections_path": col_path,
            "items_path": item_path,
            "timers": _timers,
        }
        self.mark_task_success(payload, result)
        return result

    # =========================================================================
    # 健康 & 服务信息
    # =========================================================================
    def health(self):
        """探测 TiTiler / MinIO / pgSTAC / 当前 PG 连通性。"""
        from my_project import settings
        out = {"status": "ok", "checks": {}}
        # TiTiler
        ok, st, dt, _ = GISHelper.http_probe("{}/healthz".format(settings.GIS_TITILER_URL.rstrip("/")))
        out["checks"]["titiler"] = {"ok": ok, "status": st, "elapsed": round(dt, 3)}
        # MinIO
        ok, st, dt, _ = GISHelper.http_probe("{}/minio/health/live".format(settings.GIS_MINIO_ENDPOINT))
        out["checks"]["minio"] = {"ok": ok, "status": st, "elapsed": round(dt, 3)}
        # pgSTAC
        ok, v = GISHelper.pg_probe(settings.GIS_PGSTAC_DSN)
        out["checks"]["pgstac"] = {"ok": ok, "version": v}
        # 主库（用 Django connection）
        try:
            with default_connection.cursor() as cur:
                cur.execute("SELECT 1")
            out["checks"]["postgis_main"] = {"ok": True}
        except Exception as e:
            out["checks"]["postgis_main"] = {"ok": False, "error": str(e)[:200]}
        out["status"] = "ok" if all(c.get("ok") for c in out["checks"].values()) else "degraded"
        return out

    def info(self):
        """服务信息：版本、外部依赖 URL、当前 celery worker 是否在线。"""
        from my_project import settings
        try:
            from django import get_version
            django_ver = get_version()
        except Exception:
            django_ver = None
        try:
            import shapely
            shapely_ver = shapely.__version__
        except Exception:
            shapely_ver = None
        try:
            import rasterio
            rasterio_ver = rasterio.__version__
        except Exception:
            rasterio_ver = None
        return {
            "service": "VGIS gis_service",
            "version": "1.0.0",
            "django": django_ver,
            "deps": {"shapely": shapely_ver, "rasterio": rasterio_ver},
            "external": {
                "titiler": settings.GIS_TITILER_URL,
                "minio_endpoint": settings.GIS_MINIO_ENDPOINT,
                "minio_bucket": settings.GIS_MINIO_BUCKET,
                "pgstac_dsn": settings.GIS_PGSTAC_DSN.split("@")[-1],  # 脱敏
                "nginx_static": "http://{}:{}/".format(settings.GIS_NGINX_HOST, settings.GIS_NGINX_PORT),
            },
            "endpoints": {
                "vector_load": "/my_api/gis/vector/load/",
                "vector_tables": "/my_api/gis/vector/tables/",
                "mvt_template": "/my_api/gis/mvt/{table}/{z}/{x}/{y}.pbf",
                "pmtiles_publish": "/my_api/gis/pmtiles/publish/",
                "cog_publish": "/my_api/gis/cog/publish/",
                "stac_ingest": "/my_api/gis/stac/ingest/",
                "health": "/my_api/gis/health/",
                "info": "/my_api/gis/info/",
            },
        }