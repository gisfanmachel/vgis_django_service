# -*- coding: utf-8 -*-
# demo 模块的视图层
#
# 约定：ViewSet 只做两件事 —— 声明四件套（queryset/serializer/permission/authentication）、
#       把请求转给 manager。业务逻辑一律不写在这里。
# 日志：统一用 LoggerHelper 的 set_start_log_info / set_end_log_info_in_exception 包壳。
import logging

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from vgis_log.logTools import LoggerHelper

from my_app.models import SysLog
from my_app.module.demo.manager import Operator
from my_app.module.demo.models import TtDemoItem
from my_app.module.demo.serializers import TtDemoItemSerializer
from my_app.views.response.baseRespone import Result
from my_project.token import ExpiringTokenAuthentication

logger = logging.getLogger("django")


class TtDemoItemViewSet(viewsets.ModelViewSet):
    """
    演示数据：SQL CRUD + 裸 SQL 分页 + 多表联合查询 + Excel 导入导出 的完整模板。

    复制到新模块时，把 TtDemoItem / demo / 表名 换成自己的即可。
    """
    queryset = TtDemoItem.objects.all().order_by("id")
    serializer_class = TtDemoItemSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # ---------------- 增删改 ----------------
    @action(detail=False, methods=["POST"], url_path="add")
    def add(self, request, *args, **kwargs):
        function_title = "新增演示数据"
        start = LoggerHelper.set_start_log_info(logger)
        api_path = request.path
        try:
            return Response(Operator(connection).create_data(request))
        except Exception as exp:
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, api_path,
                                                       request.auth.user, request,
                                                       function_title, str(exp), None)
            return Result.fail("{}失败".format(function_title), str(exp))

    @action(detail=False, methods=["POST"], url_path="update")
    def update_data(self, request, *args, **kwargs):
        function_title = "修改演示数据"
        start = LoggerHelper.set_start_log_info(logger)
        api_path = request.path
        try:
            return Response(Operator(connection).update_data(request))
        except Exception as exp:
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, api_path,
                                                       request.auth.user, request,
                                                       function_title, str(exp), None)
            return Result.fail("{}失败".format(function_title), str(exp))

    @action(detail=False, methods=["POST"], url_path="delete")
    def delete_data(self, request, *args, **kwargs):
        function_title = "删除演示数据"
        start = LoggerHelper.set_start_log_info(logger)
        api_path = request.path
        try:
            return Response(Operator(connection).delete_data(request))
        except Exception as exp:
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, api_path,
                                                       request.auth.user, request,
                                                       function_title, str(exp), None)
            return Result.fail("{}失败".format(function_title), str(exp))

    # ---------------- 多表联合查询 + 分页 ----------------
    @action(detail=False, methods=["POST"], url_path="query_list")
    def query_list(self, request, *args, **kwargs):
        function_title = "查询演示数据"
        start = LoggerHelper.set_start_log_info(logger)
        api_path = request.path
        try:
            return Response(Operator(connection).query_data(request))
        except Exception as exp:
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, api_path,
                                                       request.auth.user, request,
                                                       function_title, str(exp), None)
            return Result.fail("{}失败".format(function_title), str(exp))

    # ---------------- Excel 导出 ----------------
    @action(detail=False, methods=["POST"], url_path="export_excel")
    def export_excel(self, request, *args, **kwargs):
        function_title = "导出演示数据"
        start = LoggerHelper.set_start_log_info(logger)
        api_path = request.path
        try:
            return Response(Operator(connection).export_excel(request))
        except Exception as exp:
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, api_path,
                                                       request.auth.user, request,
                                                       function_title, str(exp), None)
            return Result.fail("{}失败".format(function_title), str(exp))

    # ---------------- Excel 导入模板下载 ----------------
    @action(detail=False, methods=["GET"], url_path="download_template")
    def download_template(self, request, *args, **kwargs):
        function_title = "下载导入模板"
        start = LoggerHelper.set_start_log_info(logger)
        api_path = request.path
        try:
            return Response(Operator(connection).download_template(request))
        except Exception as exp:
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, api_path,
                                                       request.auth.user, request,
                                                       function_title, str(exp), None)
            return Result.fail("{}失败".format(function_title), str(exp))

    # ---------------- Excel 导入（upsert） ----------------
    # 支持 multipart 直接传文件，或传已上传文件的 file_id，故加 csrf_exempt
    @action(detail=False, methods=["POST"], url_path="import_excel")
    @csrf_exempt
    def import_excel(self, request, *args, **kwargs):
        function_title = "导入演示数据"
        start = LoggerHelper.set_start_log_info(logger)
        api_path = request.path
        try:
            return Response(Operator(connection).import_excel(request))
        except Exception as exp:
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, api_path,
                                                       request.auth.user, request,
                                                       function_title, str(exp), None)
            return Result.fail("{}失败".format(function_title), str(exp))
