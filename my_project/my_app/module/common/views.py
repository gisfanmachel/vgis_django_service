# -*- coding: utf-8 -*-
# common 模块的视图层
#
# 内容：行政区划（tmDdistrict）与文件上传（ttUploadFileData）
# 约定：ViewSet 只做四件套声明 + 转调 manager，业务逻辑在 manager.py
import logging

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from my_app.module.common.manager import CommonOperator
from my_app.module.common.models import TmDdistrict, TtUploadFileData
from my_app.module.common.serializers import TmDdistrictSerializer, TtUploadFileDataSerializer
from my_app.utils.commonUtility import CommonHelper
from my_project.token import ExpiringTokenAuthentication

logger = logging.getLogger('django')


# 上传文件
class TtUploadFileDataViewSet(viewsets.ModelViewSet):
    queryset = TtUploadFileData.objects.all().order_by('id')
    serializer_class = TtUploadFileDataSerializer
    permission_classes = (IsAuthenticated,)
    # token认证
    # authentication_classes = (TokenAuthentication,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)

    # 上传单个文件
    @action(detail=False, methods=['POST'], url_path='uploadFile')
    @csrf_exempt
    def upload_file(self, request):
        uploadOperator = CommonOperator(connection)
        res = uploadOperator.upload_single_file(request)
        return Response(res)

    # 上传多个文件
    @action(detail=False, methods=['POST'], url_path='uploadFiles')
    @csrf_exempt
    def upload_files(self, request):
        uploadOperator = CommonOperator(connection)
        res = uploadOperator.upload_multi_files(request)
        return Response(res)


# 分省数据
class TmDdistrictViewSet(viewsets.ModelViewSet):
    queryset = TmDdistrict.objects.all().order_by('id')
    serializer_class = TmDdistrictSerializer
    permission_classes = (IsAuthenticated,)
    # authentication_classes = (TokenAuthentication,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)

    # 获取全国的分地区分省数据
    @action(detail=False, methods=['GET'], url_path='getRegionAndProvince')
    def get_region_and_province(self, request, *args, **kwargsst):
        # function_title = "获取全国的分地区分省数据"
        function_title = CommonHelper.get_local_str("GET_REGION_PROVINCE_DATA", request)
        suceess_flag = CommonHelper.get_local_str("SUCCESS", request)
        fail_flag = CommonHelper.get_local_str("FAIL", request)
        try:
            query = CommonOperator(connection)
            res = query.get_region_and_province(request)

        except Exception as exp:
            res = {
                'success': False,
                'info': "{}{}:{}".format(function_title, fail_flag,str(exp))
            }
            pass
        return Response(res)

    # 通过省份获取地市数据
    @action(detail=False, methods=['GET'], url_path='getCityByProvince')
    def get_city_by_province(self, request, *args, **kwargsst):
        try:
            query = CommonOperator(connection)
            province_code = self.request.query_params.get('province_code', '')
            res = query.get_city_by_province(province_code, request)

        except Exception as exp:
            res = {
                'success': False,
                'info': "通过省份获取地市数据失败:{}".format(str(exp))
            }
            pass
        return Response(res)

    # 通过地市获取区县数据
    @action(detail=False, methods=['GET'], url_path='getCountyByCity')
    def get_county_by_city(self, request, *args, **kwargsst):
        try:
            query = CommonOperator(connection)
            city_code = self.request.query_params.get('city_code', '')
            res = query.get_county_by_city(city_code, request)

        except Exception as exp:
            res = {
                'success': False,
                'info': "通过地市获取区县数据失败:{}".format(str(exp))
            }
            pass
        return Response(res)
