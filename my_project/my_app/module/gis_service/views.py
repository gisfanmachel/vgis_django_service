# -*- coding: utf-8 -*-
# gis_service 模块的视图层
#
# 约定（与其它模块一致）：
#   - ViewSet / @api_view 只做四件套声明 + 转调 manager
#   - 重型工作通过 Celery 异步派发，HTTP 路径只返回 task_id
#   - 日志走 insert_log_info_async 异步写 sys_log
#
# URL 一览（全部在 /my_api/gis/ 前缀下）：
#   POST  /vector/load/                       — GeoJSON 灌库 + 建 GIST 索引（同步）
#   GET   /vector/tables/                     — 列 vector 表（要素数 + bbox）
#   DELETE /vector/tables/{table}/            — 删表（需 X-Confirm: true header）
#   GET   /vector/tables/{table}/columns/     — 非几何列
#   GET   /mvt/{table}/{z}/{x}/{y}.pbf        — MVT 瓦片（Django 直查）
#   GET   /mvt/{table}/info/                  — 表信息
#   POST  /pmtiles/publish/                   — 异步（task_id）
#   GET   /pmtiles/tasks/{task_id}/           — 任务状态
#   GET   /pmtiles/list/                      — 已发布列表（按 task_type 过滤）
#   POST  /cog/publish/                       — 异步（task_id）
#   GET   /cog/tasks/{task_id}/               — 任务状态
#   GET   /cog/list/                          — 已发布列表
#   GET   /cog/tiles/{z}/{x}/{y}.png          — 反代 TiTiler
#   POST  /stac/ingest/                       — 异步（task_id）
#   GET   /tasks/{task_id}/                   — 统一任务查询
#   GET   /health/                            — 探活
#   GET   /info/                              — 服务信息
import json
import logging
import os
import time
import uuid

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from my_app.module.gis_service.manager import GISOperator
from my_app.module.gis_service.models import GISTask
from my_app.module.gis_service.utility import GISHelper
from my_app.tasks import insert_log_info_async
from my_app.utils.commonUtility import CommonHelper
from my_app.views.response.baseRespone import Result
from my_project.token import ExpiringTokenAuthentication

logger = logging.getLogger("django")
MODULE = "gis_service"


def _t(request, key):
    """取本模块词条"""
    return CommonHelper.get_local_str_from_module(MODULE, key, request)


def _user_id(request):
    """兼容 token 鉴权（request.auth.user_id）和 DRF AnonymousUser。"""
    auth = getattr(request, "auth", None)
    if auth is None:
        return None
    return getattr(auth, "user_id", None)


def _log(operation, request, t_cost):
    """异步写一条操作日志。"""
    auth = getattr(request, "auth", None)
    user = getattr(auth, "user", None) if auth else None
    insert_log_info_async(
        "my_app.module.sys_manage.models.SysLog",
        user, operation, request.path,
        str(getattr(request, "data", None))[:1000],
        t_cost, request.META.get("REMOTE_ADDR", ""),
    )


# ===========================================================================
# Vector 灌库
# ===========================================================================
class VectorLoadView(APIView):
    """POST /vector/load/

    支持两种入参：
      1) multipart 上传 GeoJSON 文件（字段名 src）
      2) JSON body 直接喂 {"src": {...}} 或 {"src": "<文件路径>"}
    必填：table
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [ExpiringTokenAuthentication]

    def post(self, request):
        function_title = _t(request, "VECTOR_LOAD_SUCCESS")
        start = time.perf_counter()
        try:
            # request.data 在 multipart 时是 dict（已不含 file），form 字段全在这
            data = request.data if isinstance(request.data, dict) else {}
            # QueryDict → dict
            if not isinstance(data, dict):
                data = dict(data)
            table = data.get("table")
            if not CommonHelper.is_valid_str(table):
                return Result.fail(_t(request, "PARAM_REQUIRED").format("table"))

            geojson = None
            # 1) multipart 文件：字段名 src 在 request.FILES
            upload = getattr(request, "FILES", None)
            if upload and upload.get("src"):
                f = upload["src"]
                tmp_path = self._save_uploaded(f)
                try:
                    with open(tmp_path, encoding="utf-8") as fh:
                        geojson = json.load(fh)
                finally:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
            else:
                # 2) JSON body：data["src"] 是 dict 或 str 路径
                src = data.get("src")
                if isinstance(src, dict):
                    geojson = src
                elif isinstance(src, str) and src and os.path.exists(src):
                    with open(src, encoding="utf-8") as fh:
                        geojson = json.load(fh)
                else:
                    return Result.fail(_t(request, "PARAM_REQUIRED").format("src"))

            op = GISOperator()
            res = op.load_vector(geojson, table, _user_id(request))
            _log(function_title, request, time.perf_counter() - start)
            return Result.sucess_obj(res)
        except Exception as exp:
            logger.exception("vector load 失败: %s", exp)
            return Result.fail(_t(request, "FAIL"), str(exp))

    @staticmethod
    def _save_uploaded(f):
        import tempfile
        suffix = os.path.splitext(f.name)[1] or ".geojson"
        fd, path = tempfile.mkstemp(suffix=suffix, prefix="vgis_vec_")
        os.close(fd)
        with open(path, "wb") as out:
            for chunk in f.chunks():
                out.write(chunk)
        return path


# ===========================================================================
# Vector 列表 / 删除 / 列
# ===========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def vector_tables(request):
    """GET /vector/tables/"""
    start = time.perf_counter()
    try:
        op = GISOperator()
        data = op.list_vector_tables()
        _log("list vector tables", request, time.perf_counter() - start)
        return Result.sucess_obj(data)
    except Exception as exp:
        return Result.fail(_t(request, "FAIL"), str(exp))


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def vector_drop_table(request, table):
    """DELETE /vector/tables/{table}/ — 必须带 X-Confirm: true header（防止误删）"""
    start = time.perf_counter()
    try:
        if request.META.get("HTTP_X_CONFIRM", "").lower() != "true":
            return Result.fail(_t(request, "VECTOR_DELETE_CONFIRM_MISSING"))
        op = GISOperator()
        res = op.drop_vector_table(table)
        _log("drop vector table {}".format(table), request, time.perf_counter() - start)
        return Result.sucess_obj(res)
    except Exception as exp:
        return Result.fail(_t(request, "FAIL"), str(exp))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def vector_table_columns(request, table):
    """GET /vector/tables/{table}/columns/"""
    start = time.perf_counter()
    try:
        op = GISOperator()
        cols = op.list_table_columns(table)
        _log("list columns of {}".format(table), request, time.perf_counter() - start)
        return Result.sucess_obj(cols)
    except Exception as exp:
        return Result.fail(_t(request, "FAIL"), str(exp))


# ===========================================================================
# MVT 瓦片 + 表信息
# ===========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def mvt_tile(request, table, z, x, y):
    """GET /mvt/{table}/{z}/{x}/{y}.pbf — 直接渲染 MVT 字节流。

    失败：返回 400 + JSON；空瓦片：返回 204（前端无需渲染）。
    """
    start = time.perf_counter()
    try:
        op = GISOperator()
        data = op.render_mvt(table, int(z), int(x), int(y))
        if not data:
            _log("mvt empty {} z{}/{}/{}".format(table, z, x, y), request, time.perf_counter() - start)
            return HttpResponse(status=204)
        _log("mvt {} z{}/{}/{}".format(table, z, x, y), request, time.perf_counter() - start)
        return HttpResponse(
            data, content_type="application/vnd.mapbox-vector-tile",
        )
    except Exception as exp:
        logger.warning("mvt_tile 失败: %s", exp)
        return Result.fail(_t(request, "FAIL"), str(exp))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def mvt_table_info(request, table):
    """GET /mvt/{table}/info/ — 表信息 + bbox + 字段清单。"""
    start = time.perf_counter()
    try:
        op = GISOperator()
        info = op.mvt_table_info(table)
        _log("mvt info {}".format(table), request, time.perf_counter() - start)
        return Result.sucess_obj(info)
    except Exception as exp:
        return Result.fail(_t(request, "FAIL"), str(exp))


# ===========================================================================
# PMTiles 发布（Celery 异步）
# ===========================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def pmtiles_publish(request):
    """POST /pmtiles/publish/

    入参（multipart / json 都行）：
        src            源文件（GeoJSON / TIFF / DEM TIFF） 或 已上传 file_id
        tile_type      vector（默认） / raster / terrain
        layer          图层名
        name           显示名
        minzoom / maxzoom
        tile_size      raster 时瓦片边长（默认 256）
        resampling     raster 时重采样：nearest/bilinear/cubic/lanczos
        bands          raster 时逗号分隔波段号（空 = 取前 3）
        vertices_per_side  terrain 时顶点网格边长（默认 65）
        props          vector 时逗号分隔属性键
        out            输出文件名（不指定则按规则生成）
        stac_collection / stac_item  （可选；挂 STAC asset）
        run_inline     bool；True 时跳过 Celery，本机同步执行（仅本机测试用）

    返回：{"task_id": "<celery uuid>", "task_pk": <int>}
    """
    start = time.perf_counter()
    try:
        data = request.data if not isinstance(request.data, dict) else dict(request.data)
        src = data.get("src")
        # multipart QueryDict 里 src 是单个 UploadedFile 对象；这里只校验文件名存在
        if src is None:
            return Result.fail(_t(request, "PARAM_REQUIRED").format("src"))
        # tile_type 在 multipart 时可能是 list（QueryDict 多值），规范化
        raw_tile_type = data.get("tile_type") or "vector"
        if isinstance(raw_tile_type, (list, tuple)):
            raw_tile_type = raw_tile_type[0] if raw_tile_type else "vector"
        tile_type = str(raw_tile_type).lower()
        if tile_type not in ("vector", "raster", "terrain"):
            return Result.fail("invalid tile_type: {}; use vector/raster/terrain".format(tile_type))

        payload, src_path = _resolve_uploaded_or_filepath(
            data, request,
            extra_keys=("tile_type", "layer", "name", "minzoom", "maxzoom", "props", "out",
                        "stac_collection", "stac_item",
                        "tile_size", "resampling", "bands", "vertices_per_side"),
            int_keys={"minzoom": 5, "maxzoom": 14,
                      "tile_size": 256, "vertices_per_side": 65},
        )
        payload["tile_type"] = tile_type
        payload["create_user_id"] = _user_id(request)

        # 落库拿到 task_pk
        task = GISTask.objects.create(
            task_id="pending-{}".format(uuid.uuid4().hex[:12]),
            task_type="pmtiles",
            status="pending",
            payload=payload,
            current_step="dispatched",
            create_user_id=_user_id(request),
            create_time=timezone.now(),
        )

        # run_inline：本机测试跳过 Celery，直接同步跑（manager 会自动 mark_task_*）
        raw_run_inline = data.get("run_inline", "")
        if isinstance(raw_run_inline, (list, tuple)):
            raw_run_inline = raw_run_inline[0] if raw_run_inline else ""
        run_inline = str(raw_run_inline).lower() in ("1", "true", "yes")
        if run_inline:
            try:
                op = GISOperator()
                result = op.publish_pmtiles(None, payload)
                _log("publish pmtiles (inline) {}".format(src_path), request,
                     time.perf_counter() - start)
                return Result.sucess_obj({
                    "task_pk": task.pk,
                    "task_id": "inline-{}".format(uuid.uuid4().hex[:8]),
                    "status": "success",
                    "result": result,
                    "inline": True,
                })
            except Exception as inline_err:
                logger.exception("pmtiles_publish inline 失败: %s", inline_err)
                task.status = "failure"
                task.error = str(inline_err)
                task.update_time = timezone.now()
                task.save(update_fields=["status", "error", "update_time"])
                return Result.fail(_t(request, "FAIL"), str(inline_err))

        # 派发 Celery
        from my_app.module.gis_service.tasks import publish_pmtiles_task
        async_res = publish_pmtiles_task.delay(payload)
        task.task_id = async_res.task_id
        task.save(update_fields=["task_id"])

        _log("publish pmtiles {}".format(src_path), request, time.perf_counter() - start)
        return Result.sucess_obj({
            "task_pk": task.pk,
            "task_id": async_res.task_id,
            "status": "pending",
        })
    except Exception as exp:
        logger.exception("pmtiles_publish 失败: %s", exp)
        return Result.fail(_t(request, "FAIL"), str(exp))


def _resolve_uploaded_or_filepath(data, request, extra_keys=(), int_keys=None):
    """把 src 解析成 worker 路径，并组装 payload。

    入参支持：
        1) multipart 文件（request.FILES['src']）—— 落盘到临时文件
        2) 已上传的 file_id（数字字符串）—— 从 tt_upload_file_data 找
        3) 普通文件路径 —— 原样返回

    返回 (payload_dict, src_path)
    """
    src = data.get("src")
    src_path = src
    if hasattr(request, "FILES") and request.FILES.get("src"):
        f = request.FILES["src"]
        src_path = VectorLoadView._save_uploaded(f)
    elif src and not os.path.exists(src):
        try:
            from django.db import connection as _conn
            with _conn.cursor() as cur:
                cur.execute(
                    "SELECT file_suffix FROM tt_upload_file_data WHERE file_id = %s",
                    [src],
                )
                row = cur.fetchone()
            if row and row[0]:
                from my_project import settings
                candidate = os.path.join(settings.UPLOAD_ROOT,
                                          "{}.{}".format(src, row[0]))
                if os.path.exists(candidate):
                    src_path = candidate
        except Exception:
            pass

    payload = {"src": src_path}
    for k in extra_keys:
        v = data.get(k)
        # multipart QueryDict 多值场景：取第一个（与 views 入口的 tile_type 处理一致）
        if isinstance(v, (list, tuple)):
            v = v[0] if v else None
        payload[k] = v
    for k, default in (int_keys or {}).items():
        v = data.get(k)
        if isinstance(v, (list, tuple)):
            v = v[0] if v else default
        try:
            payload[k] = int(v or default)
        except Exception:
            payload[k] = default
    return payload, src_path


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def pmtiles_task_status(request, task_id):
    """GET /pmtiles/tasks/{task_id}/"""
    start = time.perf_counter()
    try:
        task = GISTask.objects.filter(task_id=task_id, task_type="pmtiles").first()
        if not task:
            return Result.fail(_t(request, "TASK_NOT_FOUND").format(task_id))
        _log("query pmtiles task {}".format(task_id), request, time.perf_counter() - start)
        return Result.sucess_obj({
            "task_id": task.task_id,
            "status": task.status,
            "current_step": task.current_step,
            "result": task.result,
            "error": task.error,
            "create_time": task.create_time,
            "update_time": task.update_time,
        })
    except Exception as exp:
        return Result.fail(_t(request, "FAIL"), str(exp))


# ===========================================================================
# COG 发布 + 瓦片反代
# ===========================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def cog_publish(request):
    """POST /cog/publish/

    入参：
        src          TIFF 文件 / 文件路径 / file_id
        collection   STAC collection id（必填）
        title / dt / platform / dest_srs / compress / bands / already_cog
    """
    start = time.perf_counter()
    try:
        data = request.data if not isinstance(request.data, dict) else dict(request.data)
        src = data.get("src")
        collection = data.get("collection")
        if not CommonHelper.is_valid_str(src):
            return Result.fail(_t(request, "PARAM_REQUIRED").format("src"))
        if not CommonHelper.is_valid_str(collection):
            return Result.fail(_t(request, "PARAM_REQUIRED").format("collection"))

        payload, src_path = _resolve_uploaded_or_filepath(
            data, request,
            extra_keys=("collection", "title", "dt", "platform", "dest_srs",
                        "compress", "bands"),
            int_keys={},
        )
        payload["already_cog"] = bool(data.get("already_cog"))
        payload["no_verify"] = bool(data.get("no_verify"))
        payload["create_user_id"] = _user_id(request)

        task = GISTask.objects.create(
            task_id="pending-{}".format(uuid.uuid4().hex[:12]),
            task_type="cog",
            status="pending",
            payload=payload,
            current_step="dispatched",
            create_user_id=_user_id(request),
            create_time=timezone.now(),
        )

        from my_app.module.gis_service.tasks import publish_cog_task
        async_res = publish_cog_task.delay(payload)
        task.task_id = async_res.task_id
        task.save(update_fields=["task_id"])

        _log("publish cog {}".format(src_path), request, time.perf_counter() - start)
        return Result.sucess_obj({
            "task_pk": task.pk,
            "task_id": async_res.task_id,
            "status": "pending",
        })
    except Exception as exp:
        logger.exception("cog_publish 失败: %s", exp)
        return Result.fail(_t(request, "FAIL"), str(exp))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def cog_task_status(request, task_id):
    """GET /cog/tasks/{task_id}/"""
    start = time.perf_counter()
    try:
        task = GISTask.objects.filter(task_id=task_id, task_type="cog").first()
        if not task:
            return Result.fail(_t(request, "TASK_NOT_FOUND").format(task_id))
        _log("query cog task {}".format(task_id), request, time.perf_counter() - start)
        return Result.sucess_obj({
            "task_id": task.task_id,
            "status": task.status,
            "current_step": task.current_step,
            "result": task.result,
            "error": task.error,
            "create_time": task.create_time,
            "update_time": task.update_time,
        })
    except Exception as exp:
        return Result.fail(_t(request, "FAIL"), str(exp))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def cog_tile(request, z, x, y):
    """GET /cog/tiles/{z}/{x}/{y}.png

    反代 TiTiler：URL 里带 asset / bidx / rescale（来自最近一次成功 publish 的 cog）。
    """
    start = time.perf_counter()
    try:
        # 默认从最近一次 success 的 cog 取 URL + bands + stretch
        from my_project import settings
        # 简化策略：取最近 success 的 cog task，把 result.http 作为 url
        latest = GISTask.objects.filter(
            task_type="cog", status="success",
        ).exclude(result__isnull=True).order_by("-update_time").first()
        if not latest or not (latest.result or {}).get("http"):
            return Result.fail("no published COG asset available")

        result = latest.result
        asset_url = result["http"]
        bands = result.get("bands") or [1, 2, 3]
        stretch = {int(k): tuple(v) for k, v in (result.get("stretch") or {}).items()}

        st, ct, body = GISHelper.call_titiler(
            int(z), int(x), int(y), asset_url,
            bands=bands, stretch=stretch,
        )
        if st != 200 or not body:
            return Result.fail("TiTiler responded {}: {}".format(st, body[:200] if body else ""))
        _log("cog tile {}/{}/{}".format(z, x, y), request, time.perf_counter() - start)
        return HttpResponse(body, content_type=ct or "image/png",
                            status=st)
    except Exception as exp:
        return Result.fail(_t(request, "FAIL"), str(exp))


# ===========================================================================
# STAC ingest
# ===========================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def stac_ingest(request):
    """POST /stac/ingest/

    入参：
        collections     list[dict]  或 collections_ndjson path
        items           list[dict]  或 items_ndjson path
        method          insert / upsert（默认 upsert）
    """
    start = time.perf_counter()
    try:
        data = request.data if not isinstance(request.data, dict) else dict(request.data)
        method = data.get("method") or "upsert"
        import tempfile
        work = tempfile.mkdtemp(prefix="vgis_stac_")
        # 写 collections ndjson
        if isinstance(data.get("collections"), list):
            col_path = os.path.join(work, "collections.ndjson")
            with open(col_path, "w", encoding="utf-8") as f:
                for c in data["collections"]:
                    f.write(json.dumps(c, ensure_ascii=False) + "\n")
        elif isinstance(data.get("collections_ndjson"), str):
            col_path = data["collections_ndjson"]
        else:
            return Result.fail(_t(request, "PARAM_REQUIRED").format("collections"))

        if isinstance(data.get("items"), list):
            item_path = os.path.join(work, "items.ndjson")
            with open(item_path, "w", encoding="utf-8") as f:
                for it in data["items"]:
                    f.write(json.dumps(it, ensure_ascii=False) + "\n")
        elif isinstance(data.get("items_ndjson"), str):
            item_path = data["items_ndjson"]
        else:
            return Result.fail(_t(request, "PARAM_REQUIRED").format("items"))

        payload = {
            "collections_ndjson": col_path,
            "items_ndjson": item_path,
            "method": method,
            "create_user_id": _user_id(request),
        }

        task = GISTask.objects.create(
            task_id="pending-{}".format(uuid.uuid4().hex[:12]),
            task_type="stac",
            status="pending",
            payload=payload,
            current_step="dispatched",
            create_user_id=_user_id(request),
            create_time=timezone.now(),
        )

        from my_app.module.gis_service.tasks import ingest_stac_task
        async_res = ingest_stac_task.delay(payload)
        task.task_id = async_res.task_id
        task.save(update_fields=["task_id"])

        _log("ingest stac", request, time.perf_counter() - start)
        return Result.sucess_obj({
            "task_pk": task.pk,
            "task_id": async_res.task_id,
            "status": "pending",
        })
    except Exception as exp:
        logger.exception("stac_ingest 失败: %s", exp)
        return Result.fail(_t(request, "FAIL"), str(exp))


# ===========================================================================
# 统一任务查询 + 列表
# ===========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def task_status_unified(request, task_id):
    """GET /tasks/{task_id}/ — 任意 task_type 的统一查询"""
    start = time.perf_counter()
    try:
        task = GISTask.objects.filter(task_id=task_id).first()
        if not task:
            return Result.fail(_t(request, "TASK_NOT_FOUND").format(task_id))
        _log("query task {}".format(task_id), request, time.perf_counter() - start)
        return Result.sucess_obj({
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status,
            "current_step": task.current_step,
            "result": task.result,
            "error": task.error,
            "create_time": task.create_time,
            "update_time": task.update_time,
        })
    except Exception as exp:
        return Result.fail(_t(request, "FAIL"), str(exp))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def list_tasks(request, task_type=None):
    """GET /tasks/list/?status=running&limit=20
    GET /pmtiles/list/?status=running&limit=20
    GET /cog/list/?status=running&limit=20

    接受 task_type 形参（pmtiles/cog/stac）；如果从 path 推不出来，则取 query params 'type'。
    """
    start = time.perf_counter()
    try:
        qs = GISTask.objects.all().order_by("-create_time")
        t = task_type or request.query_params.get("type")
        s = request.query_params.get("status")
        if t:
            qs = qs.filter(task_type=t)
        if s:
            qs = qs.filter(status=s)
        try:
            limit = min(int(request.query_params.get("limit", 50)), 200)
        except Exception:
            limit = 50
        rows = qs[:limit]
        data = [
            {
                "task_id": r.task_id,
                "task_type": r.task_type,
                "status": r.status,
                "current_step": r.current_step,
                "create_time": r.create_time,
                "update_time": r.update_time,
            }
            for r in rows
        ]
        _log("list tasks {}".format(t or "*"), request, time.perf_counter() - start)
        return Result.sucess_obj(data)
    except Exception as exp:
        return Result.fail(_t(request, "FAIL"), str(exp))


# ===========================================================================
# 健康 / 信息
# ===========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def health(request):
    """GET /health/ — TiTiler / MinIO / pgSTAC / 主库连通性"""
    start = time.perf_counter()
    try:
        op = GISOperator()
        data = op.health()
        _log("health", request, time.perf_counter() - start)
        return Result.sucess_obj(data)
    except Exception as exp:
        return Result.fail(_t(request, "FAIL"), str(exp))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([ExpiringTokenAuthentication])
def info(request):
    """GET /info/ — 服务信息 + 外部依赖 URL"""
    start = time.perf_counter()
    try:
        op = GISOperator()
        data = op.info()
        _log("info", request, time.perf_counter() - start)
        return Result.sucess_obj(data)
    except Exception as exp:
        return Result.fail(_t(request, "FAIL"), str(exp))