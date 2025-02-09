#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2023/3/13 13:53
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : businessViews.py
# @Descr   : 业务操作视图
# @Software: PyCharm
import json
import logging
import os
import time
import datetime
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from vgis_log.logTools import LoggerHelper
from vgis_utils.vgis_http.httpTools import HttpHelper

from my_app import models
from my_app.manage.businessManager import BuisnessOperator
from my_app.manage.commonManager import CommonOperator

from my_app.models import TtUploadFileData, TmDdistrict, TtAnnotationSysmbolData, TtAnnotationType, \
    TtFeatureAnnotationData, TtFriendFoeInfo, TtIntelligenceSource, TtPoiData, TtTaskDirectionBookmarkData, SysLog, \
    TtAnnotationPointType, \
    TmBingtuan, TtFieldType, TtFeatureAnnotationeNewFields, TtSupermapServiceInterfaceType, TtKeyPointAreaData, \
    TtAnnotationHotData, TtBdxq, TtFwmb, TtFwmbTableRelation, TtJbfj, TtMapBookmarkData, TtOursideData, TtRoadData, \
    TtWorkspaceData, TtThememapData, TmShituanPt, TmDistrictPt, TtPeopleFlowMonitorArea
from my_app.serializers import TtUploadFileDataSerializer, TmDdistrictSerializer, TtAnnotationSysmbolDataSerializer, \
    TtAnnotationTypeSerializer, TtFeatureAnnotationDataSerializer, TtFriendFoeInfoSerializer, \
    TtIntelligenceSourceSerializer, TtPoiDataSerializer, TtViewBookmarkDataSerializer, TtPointTypeSerializer, \
    TmBingtuanSerializer, TtFieldTypeSerializer, TtServiceInterfaceTypeSerializer, TtKeyPointAreaDataSerializer, \
    TtAnnotationHotDataSerializer, TtBdxqSerializer, TtFwmbSerializer, TtFwmbTableRelationSerializer, TtJbfjSerializer, \
    TtMapBookmarkDataSerializer, TtOursideDataSerializer, TtRoadDataSerializer, TtWorkspaceDataSerializer, \
    TtPeopleFlowMonitorAreaSerializer
from my_app.utils.businessUtility import businessHelper

from my_app.utils.commonUtility import CommonHelper
from my_app.utils.snowflake_id_util import SnowflakeIDUtil
from my_app.views.response.baseRespone import Result
from my_project import settings
from my_project.settings import BASE_DIR, APP_NAME, STATIC_NAME
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
        CommonHelper.logger_json_key_value(request, logger)
        res = uploadOperator.upload_single_file(request)
        return Response(res)

    # 上传自定义图标
    @action(detail=False, methods=['POST'], url_path='uploadCustomImage')
    @csrf_exempt
    def uploadCustomImage(self, request):
        uploadOperator = CommonOperator(connection)
        CommonHelper.logger_json_key_value(request, logger)
        res = uploadOperator.upload_custom_image(request)
        return Response(res)

    # 上传多个文件(图片，视频等)
    @action(detail=False, methods=['POST'], url_path='uploadFiles')
    @csrf_exempt
    def upload_files(self, request):
        uploadOperator = CommonOperator(connection)
        CommonHelper.logger_json_key_value(request, logger)
        res = uploadOperator.upload_multi_files(request)
        return Response(res)


# 兵团数据
class TmBingtuanViewSet(viewsets.ModelViewSet):
    queryset = TmBingtuan.objects.all().order_by('id')
    serializer_class = TmBingtuanSerializer
    permission_classes = (IsAuthenticated,)
    # authentication_classes = (TokenAuthentication,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)

    # 为下列代码增加注释
    
    def list(self, request, *args, **kwargs):
        try:
            function_title = "获取所有兵团区划数据"
            start = LoggerHelper.set_start_log_info(logger)
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                page_response = self.get_paginated_response(serializer.data)
                # 增加url头
                page_response.data["url_head"] = CommonHelper.get_url_head()
                suceess_flag = "成功"
                data = Result.list(page_response.data, message=function_title + "{}".format(suceess_flag))
                LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                              function_title)
            return Response(data)
        except Exception as exp:
            # msg = "{}失败".format(function_title)
            fail_flag = "失败"
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 获取新疆的所有兵团区划
    @action(detail=False, methods=['GET'], url_path='getAllDivision')
    def get_all_division(self, request, *args, **kwargsst):
        try:
            query = CommonOperator(connection)
            CommonHelper.logger_json_key_value(request, logger)
            # corps_code = self.request.query_params.get('corps_code', '')
            res = query.get_all_bingtuan_division(request)

        except Exception as exp:
            res = {
                'success': False,
                'info': "获取新疆兵团的师级数据失败:{}".format(str(exp))
            }
        return Response(res)

    # 获取新疆兵团的师级数据
    @action(detail=False, methods=['GET'], url_path='getDivisionByCorps')
    def get_division_by_corps(self, request, *args, **kwargsst):
        try:
            query = CommonOperator(connection)
            CommonHelper.logger_json_key_value(request, logger)
            corps_code = self.request.query_params.get('corps_code', '')
            res = query.get_division_by_corps(corps_code, request)

        except Exception as exp:
            res = {
                'success': False,
                'info': "获取新疆兵团的师级数据失败:{}".format(str(exp))
            }
        return Response(res)

    # 通过师级获取团级数据
    @action(detail=False, methods=['GET'], url_path='getRegimentByDivision')
    def get_regiment_by_division(self, request, *args, **kwargsst):
        try:
            query = CommonOperator(connection)
            CommonHelper.logger_json_key_value(request, logger)
            regiment_code = self.request.query_params.get('division_code', '')
            res = query.get_regiment_by_division(regiment_code, request)

        except Exception as exp:
            res = {
                'success': False,
                'info': "通过师级获取团级数据失败:{}".format(str(exp))
            }
        return Response(res)


# 分省数据
class TmDdistrictViewSet(viewsets.ModelViewSet):
    queryset = TmDdistrict.objects.all().order_by('id')
    serializer_class = TmDdistrictSerializer
    permission_classes = (IsAuthenticated,)
    # authentication_classes = (TokenAuthentication,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)

    # 获取新疆的所有兵团区划
    @action(detail=False, methods=['GET'], url_path='getAllDivision')
    def get_all_division(self, request, *args, **kwargsst):
        try:
            query = CommonOperator(connection)
            CommonHelper.logger_json_key_value(request, logger)
            # corps_code = self.request.query_params.get('corps_code', '')
            res = query.get_all_xinjiang_division(request)

        except Exception as exp:
            res = {
                'success': False,
                'info': "获取新疆兵团的师级数据失败:{}".format(str(exp))
            }
        return Response(res)

    # 获取全国的分地区分省数据
    @action(detail=False, methods=['GET'], url_path='getRegionAndProvince')
    def get_region_and_province(self, request, *args, **kwargsst):
        try:
            query = CommonOperator(connection)
            CommonHelper.logger_json_key_value(request, logger)
            res = query.get_region_and_province(request)

        except Exception as exp:
            res = {
                'success': False,
                'info': "获取全国的分地区分省数据失败:{}".format(str(exp))
            }
        return Response(res)

    # 通过省份获取地市数据
    @action(detail=False, methods=['GET'], url_path='getCityByProvince')
    def get_city_by_province(self, request, *args, **kwargsst):
        try:
            query = CommonOperator(connection)
            CommonHelper.logger_json_key_value(request, logger)
            province_code = self.request.query_params.get('province_code', '')
            res = query.get_city_by_province(province_code, request)

        except Exception as exp:
            res = {
                'success': False,
                'info': "通过省份获取地市数据失败:{}".format(str(exp))
            }
        return Response(res)

    # 通过地市获取区县数据
    @action(detail=False, methods=['GET'], url_path='getCountyByCity')
    def get_county_by_city(self, request, *args, **kwargsst):
        try:
            query = CommonOperator(connection)
            CommonHelper.logger_json_key_value(request, logger)
            city_code = self.request.query_params.get('city_code', '')
            res = query.get_county_by_city(city_code, request)

        except Exception as exp:
            res = {
                'success': False,
                'info': "通过地市获取区县数据失败:{}".format(str(exp))
            }
        return Response(res)


# 标注符号数据表viewer类
class TtAnnotationSysmbolDataViewSet(viewsets.ModelViewSet):
    queryset = TtAnnotationSysmbolData.objects.all().order_by('id')
    serializer_class = TtAnnotationSysmbolDataSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # 标注符号查询
    @action(detail=False, methods=['POST'], url_path='search_symbol')
    def search_symbol(self, request):
        function_title = "标注符号查询"
        buisnessOperator = BuisnessOperator(connection)
        CommonHelper.logger_json_key_value(request, logger)
        res = buisnessOperator.search_symbol(request, function_title, connection)
        return Response(res)


# 标注类型字典表viewer类
class TtAnnotationTypeViewSet(viewsets.ModelViewSet):
    queryset = TtAnnotationType.objects.all().order_by('id')
    serializer_class = TtAnnotationTypeSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)


# 要素标注数据表viewer类
class TtFeatureAnnotationDataViewSet(viewsets.ModelViewSet):
    queryset = TtFeatureAnnotationData.objects.all().order_by('id')
    serializer_class = TtFeatureAnnotationDataSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # 获取临时标绘的所有标绘图形和空间范围
    @action(detail=False, methods=['POST'], url_path='get_annotations_of_all')
    def get_annotations_of_all(self, request):
        try:
            function_title = "获取临时标绘的所有标绘图形和空间范围"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.get_annotations_of_feature_table(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    @action(detail=False, methods=['POST'], url_path='get_detials_of_annotation_data')
    def get_detials_of_annotation_data(self, request):
        try:
            function_title = "获取指定标绘图形的字段信息"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.get_detials_of_feature_annotation_data(request, connection)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 根据类型获取标注数据
    @action(detail=False, methods=['POST'], url_path='get_annotation_data_by_type')
    def get_annotation_data_by_type(self, request):
        function_title = "根据类型获取标注数据"
        buisnessOperator = BuisnessOperator(connection)
        CommonHelper.logger_json_key_value(request, logger)
        res = buisnessOperator.get_annotation_data_by_sql(request, function_title, connection)
        return Response(res)

    # 根据sql获取标注数据
    @action(detail=False, methods=['POST'], url_path='get_annotation_data_by_sql')
    def get_annotation_data_by_sql(self, request):
        function_title = "根据sql获取标注数据"
        buisnessOperator = BuisnessOperator(connection)
        CommonHelper.logger_json_key_value(request, logger)
        res = buisnessOperator.get_annotation_data_by_sql(request, function_title, connection)
        return Response(res)

    # 标注数据分页查询
    @action(detail=False, methods=['POST'], url_path='query_list')
    def query_list(self, request):
        try:
            function_title = "标注数据分页查询"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.query_annotation_data_list_new(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 获取历史已新增字段列表
    @action(detail=False, methods=['POST'], url_path='get_history_add_field_list')
    def get_history_add_field_list(self, request):
        try:
            function_title = "获取历史已新增字段列表"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            res = operator.get_annotation_data_all_history_field()
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return Response(res)
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 全文检索
    @action(detail=False, methods=['POST'], url_path='full_search')
    def full_search(self, request):
        function_title = "全文检索"
        buisnessOperator = BuisnessOperator(connection)
        CommonHelper.logger_json_key_value(request, logger)
        # res = buisnessOperator.full_search(request, function_title, connection)
        res = buisnessOperator.full_search_new(request, function_title, connection)
        return Response(res)

    # 快速检索
    @action(detail=False, methods=['POST'], url_path='fast_search')
    def fast_search(self, request):
        function_title = "快速检索"
        buisnessOperator = BuisnessOperator(connection)
        CommonHelper.logger_json_key_value(request, logger)
        res = buisnessOperator.fast_search(request, function_title, connection)
        return Response(res)

    # 高级检索
    @action(detail=False, methods=['POST'], url_path='advance_search')
    def advance_search(self, request):
        function_title = "高级检索"
        buisnessOperator = BuisnessOperator(connection)
        CommonHelper.logger_json_key_value(request, logger)
        res = buisnessOperator.advance_search(request, function_title, connection)
        return Response(res)

    @action(detail=False, methods=['GET'], url_path='get_all_bztc')
    def get_all_bztc(self, request):
        function_title = "获取所有标注图层名称"
        CommonHelper.logger_json_key_value(request, logger)
        commonOperator = CommonOperator(connection)
        res = commonOperator.get_all_bztc(request, function_title)
        return Response(res)

    # 快速标注
    @action(detail=False, methods=['POST'], url_path='fast_annotation')
    def fast_annotation(self, request):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        table_ename = request.data["table_ename"]
        request.data.pop("table_ename")
        cursor = connection.cursor()
        request.data["id"] = SnowflakeIDUtil.snowflakeId()
        if table_ename == "tt_feature_annotation_data":
            request.data["create_user_id"] = request.auth.user_id
            request.data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            request.data["minx"] = None
            request.data["miny"] = None
            request.data["maxx"] = None
            request.data["maxy"] = None

        sql = "select * from  {} where name ='{}'".format(table_ename, request.data["name"])
        cursor.execute(sql)
        if cursor.fetchone():
            res = {
                'success': False,
                'info': "新增名称:{}已存在，请换个名称".format(request.data["name"])
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新视口书签失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            annotation_sysmbol_style_data = request.data["annotation_sysmbol_style"]
            request.data["annotation_sysmbol_style"] = json.dumps(request.data["annotation_sysmbol_style"],
                                                                  ensure_ascii=False)
            # 确保insert sql语句能正常执行
            request.data["annotation_sysmbol_style"] = request.data["annotation_sysmbol_style"].replace("'", "''")

            # 更新空间字段内容（采用GEOMETRYCOLLECTION保存符合几何对象，因为前端会传过来点、线、面）
            geom_collection = businessHelper.get_geometrycollection_from_annotation_sysmbol_style(
                annotation_sysmbol_style_data)
            request.data["geom"] = geom_collection

            insert_sql = businessHelper.build_insert_sql(table_ename, request.data, connection)
            print(insert_sql)
            cursor.execute(insert_sql)
            connection.commit()

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增标注",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))

            res = {
                'success': True,
                'info': "新增标注:{}成功".format(request.data["name"])
            }
            return Response(res)

    def create(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        buisnessOperator = BuisnessOperator(connection)
        name = request.data["name"]
        if len(TtFeatureAnnotationData.objects.filter(name=name)) > 0:
            res = {
                'success': False,
                'info': "新增的标注名称:{}已存在，请换个名称".format(name)
            }

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增视口书签失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            cursor = connection.cursor()
            history_fields = None
            new_fields = None
            if "history_fields" in request.data:
                history_fields = request.data["history_fields"]
                request.data.pop("history_fields")
            # 创建本次新增属性字段
            if "new_fields" in request.data:
                new_fields = request.data["new_fields"]
                request.data.pop("new_fields")
                is_repeate_new_field = False
                for new_field in new_fields:
                    is_repeate_new_field = buisnessOperator.is_annotation_data_add_field_cname_repeat(
                        new_field["field_cname"])
                    if is_repeate_new_field:
                        break
                if is_repeate_new_field:
                    res = {
                        'success': False,
                        'info': "新增的标注属性字段:{}已存在，请换个名称".format(new_field["field_cname"])
                    }
                    return Response(res)
                for new_field in new_fields:
                    new_field["dm_field_type"] = businessHelper.convert_to_pg_field_type(new_field["field_type"])
                    new_field["field_ename"] = buisnessOperator.get_annotation_data_add_field()
                    # 拼接增加字段sql
                    alter_sql = "ALTER TABLE tt_feature_annotation_data ADD {} {}; ".format(new_field["field_ename"],
                                                                                            new_field["dm_field_type"])
                    cursor.execute(alter_sql)
                    connection.commit()
                    # -- 给字段添加备注
                    alter_sql = "COMMENT ON COLUMN tt_feature_annotation_data.{} IS '{}'; ".format(
                        new_field["field_ename"], new_field["field_cname"])
                    cursor.execute(alter_sql)
                    connection.commit()

            # 录入固定属性字段内容
            request.data["id"] = SnowflakeIDUtil.snowflakeId()
            if "friend_foe_information" not in request.data:
                request.data["friend_foe_information_name"] = None
            else:
                if request.data["friend_foe_information"] is not None and str(
                        request.data["friend_foe_information"]).strip() != "":
                    request.data["friend_foe_information_name"] = TtFriendFoeInfo.objects.get(
                        id=request.data["friend_foe_information"]).info_cname
            if "intelligence_source" not in request.data:
                request.data["intelligence_source_name"] = None
            else:
                if request.data["intelligence_source"] is not None and str(
                        request.data["intelligence_source"]).strip() != "":
                    request.data["intelligence_source_name"] = TtIntelligenceSource.objects.get(
                        id=request.data["intelligence_source"]).source_cname
            if "type" not in request.data:
                request.data["type_name"] = None
            else:
                if request.data["type"] is not None and str(request.data["type"]).strip() != "":
                    request.data["type_name"] = TtAnnotationType.objects.get(
                        id=request.data["type"]).annotation_cname
            if "point_type" not in request.data:
                request.data["point_type_name"] = None
            else:
                if request.data["point_type"] is not None and str(request.data["point_type"]).strip() != "":
                    request.data["point_type_name"] = TtAnnotationPointType.objects.get(
                        id=request.data["point_type"]).point_cname
            request.data["create_user_id"] = request.auth.user_id
            request.data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 图片字段
            if "pics_file_id" in request.data:
                pics_file_id = request.data["pics_file_id"]
                pics_path = []
                for pic_file_id in pics_file_id:
                    if TtUploadFileData.objects.filter(id=pic_file_id).exists():
                        pics_path.append(TtUploadFileData.objects.get(id=pic_file_id).path)
                pics_path = ",".join(pics_path)
                request.data["pics_path"] = pics_path
            # 视频字段
            if "videos_file_id" in request.data:
                videos_file_id = request.data["videos_file_id"]
                videos_path = []
                for video_file_id in videos_file_id:
                    if TtUploadFileData.objects.filter(id=video_file_id).exists():
                        videos_path.append(TtUploadFileData.objects.get(id=video_file_id).path)
                videos_path = ",".join(videos_path)
                request.data["videos_path"] = videos_path
            if "pics_file_id" in request.data:
                request.data.pop("pics_file_id")
            if "videos_file_id" in request.data:
                request.data.pop("videos_file_id")

            annotation_sysmbol_style_data = request.data["annotation_sysmbol_style"]
            request.data["annotation_sysmbol_style"] = json.dumps(request.data["annotation_sysmbol_style"],
                                                                  ensure_ascii=False)

            TtFeatureAnnotationData.objects.create(**request.data)
            # 更新空间字段内容（采用GEOMETRYCOLLECTION保存符合几何对象，因为前端会传过来点、线、面）
            update_sql = "UPDATE tt_feature_annotation_data SET "
            geom_collection = businessHelper.get_geometrycollection_from_annotation_sysmbol_style(
                annotation_sysmbol_style_data)
            update_sql += " geom ={} ".format(geom_collection)

            # 录入历史新增属性字段
            if history_fields is not None and str(history_fields) != "" and str(history_fields) != "{}":
                for key, value in history_fields.items():
                    # print(f"Key: {key}, Value: {value}")
                    field_type = buisnessOperator.get_annotation_data_field_type(key)
                    update_sql += " , " + businessHelper.build_update_field_sql(key,
                                                                                field_type,
                                                                                value)
            # 录入本次新增属性字段
            if new_fields is not None and str(new_fields) != "" and str(new_fields) != "[]":
                for field in new_fields:
                    update_sql += " , " + businessHelper.build_update_field_sql(field["field_ename"],
                                                                                field["field_type"],
                                                                                field["field_value"])
            update_sql += " where id = {}".format(
                request.data["id"])
            cursor.execute(update_sql)
            connection.commit()

            # 更新TtFeatureAnnotationeNewFields，包括数据新增字段和选择的新增字段
            # 前端会把所有的历史字段和本次新增字段都返回
            obj = {}
            obj["new_fields_cname"] = ""
            obj["new_fields_ename"] = ""
            obj["new_fields_type"] = ""
            if history_fields is not None and str(history_fields) != "" and str(history_fields) != "{}":
                for key, value in history_fields.items():
                    obj["new_fields_cname"] += buisnessOperator.get_annotation_data_field_cname(key) + ","
                    obj["new_fields_ename"] += key + ","
                    obj["new_fields_type"] += buisnessOperator.get_annotation_data_field_type(key) + ","

            if new_fields is not None and str(new_fields) != "" and str(new_fields) != "[]":
                for field in new_fields:
                    obj["new_fields_cname"] += field["field_cname"] + ","
                    obj["new_fields_ename"] += field["field_ename"] + ","
                    obj["new_fields_type"] += field["field_type"] + ","

            if obj["new_fields_cname"] != "":
                obj["id"] = SnowflakeIDUtil.snowflakeId()
                obj["annotation_id"] = request.data["id"]
                obj["new_fields_cname"] = obj["new_fields_cname"][:-1]
                obj["new_fields_ename"] = obj["new_fields_ename"][:-1]
                obj["new_fields_type"] = obj["new_fields_type"][:-1]
                TtFeatureAnnotationeNewFields.objects.create(**obj)

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增标注",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))

            res = {
                'success': True,
                'info': "新增标注:{}成功".format(request.data["name"])
            }
            return Response(res)

    def update(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        id = kwargs["pk"]
        if len(TtFeatureAnnotationData.objects.filter(id=id)) > 0:
            old_name = TtFeatureAnnotationData.objects.filter(id=id)[0].name
        buisnessOperator = BuisnessOperator(connection)
        new_name = request.data["name"]
        if old_name != new_name and len(
                TtFeatureAnnotationData.objects.filter(name=new_name)) > 0:
            res = {
                'success': False,
                'info': "更新的标注名称:{}已存在，请换个名称".format(new_name)
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新视口书签失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:

            cursor = connection.cursor()
            history_fields = None
            new_fields = None
            if "history_fields" in request.data:
                history_fields = request.data["history_fields"]
                request.data.pop("history_fields")
            # 创建本次新增属性字段
            if "new_fields" in request.data:
                new_fields = request.data["new_fields"]
                request.data.pop("new_fields")
                is_repeate_new_field = False
                for new_field in new_fields:
                    is_repeate_new_field = buisnessOperator.is_annotation_data_add_field_cname_repeat(
                        new_field["field_cname"])
                    if is_repeate_new_field:
                        break
                if is_repeate_new_field:
                    res = {
                        'success': False,
                        'info': "新增的标注属性字段:{}已存在，请换个名称".format(new_field["field_cname"])
                    }
                    return Response(res)
                for new_field in new_fields:
                    new_field["dm_field_type"] = businessHelper.convert_to_pg_field_type(new_field["field_type"])
                    new_field["field_ename"] = buisnessOperator.get_annotation_data_add_field()
                    # 拼接增加字段sql
                    alter_sql = "ALTER TABLE tt_feature_annotation_data ADD {} {}; ".format(new_field["field_ename"],
                                                                                            new_field["dm_field_type"])
                    cursor.execute(alter_sql)
                    connection.commit()
                    # -- 给字段添加备注
                    alter_sql = "COMMENT ON COLUMN tt_feature_annotation_data.{} IS '{}'; ".format(
                        new_field["field_ename"], new_field["field_cname"])
                    cursor.execute(alter_sql)
                    connection.commit()

            # 更新固定字段内容
            if "friend_foe_information" not in request.data:
                pass
            else:
                if request.data["friend_foe_information"] is not None and str(
                        request.data["friend_foe_information"]).strip() != "":
                    request.data["friend_foe_information_name"] = TtFriendFoeInfo.objects.get(
                        id=request.data["friend_foe_information"]).info_cname
            if "intelligence_source" not in request.data:
                pass
            else:
                if request.data["intelligence_source"] is not None and str(
                        request.data["intelligence_source"]).strip() != "":
                    request.data["intelligence_source_name"] = TtIntelligenceSource.objects.get(
                        id=request.data["intelligence_source"]).source_cname
            if "type" not in request.data:
                pass
            else:
                if request.data["type"] is not None and str(request.data["type"]).strip() != "":
                    request.data["type_name"] = TtAnnotationType.objects.get(
                        id=request.data["type"]).annotation_cname
            if "point_type" not in request.data:
                pass
            else:
                if request.data["point_type"] is not None and str(request.data["point_type"]).strip() != "":
                    request.data["point_type_name"] = TtAnnotationPointType.objects.get(
                        id=request.data["point_type"]).point_cname
            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 图片字段
            if "pics_file_id" in request.data:
                pics_file_id = request.data["pics_file_id"]
                pics_path = []
                for pic_file_id in pics_file_id:
                    if TtUploadFileData.objects.filter(id=pic_file_id).exists():
                        pics_path.append(TtUploadFileData.objects.get(id=pic_file_id).path)
                pics_path = ",".join(pics_path)
                request.data["pics_path"] = pics_path
            # 视频字段
            if "videos_file_id" in request.data:
                videos_file_id = request.data["videos_file_id"]
                videos_path = []
                for video_file_id in videos_file_id:
                    if TtUploadFileData.objects.filter(id=video_file_id).exists():
                        videos_path.append(TtUploadFileData.objects.get(id=video_file_id).path)
                videos_path = ",".join(videos_path)
                request.data["videos_path"] = videos_path
            if "pics_file_id" in request.data:
                request.data.pop("pics_file_id")
            if "videos_file_id" in request.data:
                request.data.pop("videos_file_id")

            annotation_sysmbol_style_data = request.data["annotation_sysmbol_style"]
            request.data["annotation_sysmbol_style"] = json.dumps(request.data["annotation_sysmbol_style"],
                                                                  ensure_ascii=False)

            TtFeatureAnnotationData.objects.filter(id=id).update(**request.data)

            # super().update(request, *args, **kwargs)

            # 更新空间字段内容（采用GEOMETRYCOLLECTION保存符合几何对象，因为前端会传过来点、线、面）
            update_sql = "UPDATE tt_feature_annotation_data SET "
            geom_collection = businessHelper.get_geometrycollection_from_annotation_sysmbol_style(
                annotation_sysmbol_style_data)
            update_sql += " geom ={} ".format(geom_collection)

            # 录入历史新增属性字段
            if history_fields is not None and str(history_fields) != "" and str(history_fields) != "{}":
                for key, value in history_fields.items():
                    # print(f"Key: {key}, Value: {value}")
                    field_type = buisnessOperator.get_annotation_data_field_type(key)
                    update_sql += " , " + businessHelper.build_update_field_sql(key,
                                                                                field_type,
                                                                                value)
            # 录入本次新增属性字段
            if new_fields is not None and str(new_fields) != "" and str(new_fields) != "[]":
                for field in new_fields:
                    update_sql += " , " + businessHelper.build_update_field_sql(field["field_ename"],
                                                                                field["field_type"],
                                                                                field["field_value"])
            update_sql += " where id = {}".format(
                id)
            cursor.execute(update_sql)
            connection.commit()

            # 更新标注数据新增字段表(前端会把原来的history字段和这次选择的history字段，还有本次新输入的new字段，全部传过来))

            # 前端会把所有的历史字段和本次新增字段都返回
            obj = {}
            obj["new_fields_cname"] = ""
            obj["new_fields_ename"] = ""
            obj["new_fields_type"] = ""
            if history_fields is not None and str(history_fields) != "" and str(history_fields) != "{}":
                for key, value in history_fields.items():
                    obj["new_fields_cname"] += buisnessOperator.get_annotation_data_field_cname(key) + ","
                    obj["new_fields_ename"] += key + ","
                    obj["new_fields_type"] += buisnessOperator.get_annotation_data_field_type(key) + ","

            if new_fields is not None and str(new_fields) != "" and str(new_fields) != "[]":
                for field in new_fields:
                    obj["new_fields_cname"] += field["field_cname"] + ","
                    obj["new_fields_ename"] += field["field_ename"] + ","
                    obj["new_fields_type"] += field["field_type"] + ","

            if obj["new_fields_cname"] != "":
                obj["id"] = SnowflakeIDUtil.snowflakeId()
                obj["annotation_id"] = request.data["id"]
                obj["new_fields_cname"] = obj["new_fields_cname"][:-1]
                obj["new_fields_ename"] = obj["new_fields_ename"][:-1]
                obj["new_fields_type"] = obj["new_fields_type"][:-1]

                if not TtFeatureAnnotationeNewFields.objects.filter(annotation_id=id).exists():
                    obj["id"] = SnowflakeIDUtil.snowflakeId()
                    obj["annotation_id"] = id
                    TtFeatureAnnotationeNewFields.objects.create(**obj)
                else:
                    TtFeatureAnnotationeNewFields.objects.filter(annotation_id=id).update(**obj)

            res = {
                'success': True,
                'info': "修改标注成功"
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新标注",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)

    # # 删除
    def destroy(self, request, *args, **kwargs):
        title = "删除标注"
        res = ""
        id = kwargs["pk"]
        start = time.perf_counter()
        try:
            super().destroy(request, *args, **kwargs)
            # 同时删除标注数据新增字段记录
            TtFeatureAnnotationeNewFields.objects.filter(annotation_id=id).delete()
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title,
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            res = {
                'success': True,
                'info': "{}(编号为{})成功".format(title, id)
            }
        except Exception as exp:
            res = {
                'success': False,
                'info': "{}(编号为{})失败，原因为：{}".format(title, id, str(exp))
            }
        finally:
            res

        return Response(res)


# 敌我信息字典表viewer类
class TtFriendFoeInfoViewSet(viewsets.ModelViewSet):
    queryset = TtFriendFoeInfo.objects.all().order_by('id')
    serializer_class = TtFriendFoeInfoSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)


# 情报来源字典表viewer类
class TtIntelligenceSourceViewSet(viewsets.ModelViewSet):
    queryset = TtIntelligenceSource.objects.all().order_by('id')
    serializer_class = TtIntelligenceSourceSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)


# 标注点类型字典表viewer类
class TtPointTypeViewSet(viewsets.ModelViewSet):
    queryset = TtAnnotationPointType.objects.all().order_by('id')
    serializer_class = TtPointTypeSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)


# 字段类型字典表viewer类
class TtFieldTypeViewSet(viewsets.ModelViewSet):
    queryset = TtFieldType.objects.all().order_by('id')
    serializer_class = TtFieldTypeSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)


# POI数据表viewer类
class TtPoiDataViewSet(viewsets.ModelViewSet):
    queryset = TtPoiData.objects.all().order_by('id')
    serializer_class = TtPoiDataSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # 获取poi类型
    @action(detail=False, methods=['POST'], url_path='get_all_poi_type')
    def get_poi_type(self, request):
        function_title = "获取poi类型"
        buisnessOperator = BuisnessOperator(connection)
        CommonHelper.logger_json_key_value(request, logger)
        res = buisnessOperator.get_poi_type(request, function_title, connection)
        return Response(res)

    # 根据类型获取poi数据
    @action(detail=False, methods=['POST'], url_path='get_poi_data_by_type')
    def get_poi_data_by_type(self, request):
        function_title = "根据类型获取POI数据"
        buisnessOperator = BuisnessOperator(connection)
        CommonHelper.logger_json_key_value(request, logger)
        poi_type = request.data["poi_type"]
        # 用静态的，提供性能
        geojson_url = "http://{}:{}{}poi/{}.geojson".format(settings.PROJECT_SERVICE_IP,
                                                            settings.PROJECT_SERVICE_PORT,
                                                            settings.STATIC_URL,
                                                            poi_type)

        # 给前面返回geojson文件
        res = {
            'success': True,
            'geojson_url': geojson_url
        }
        # res = buisnessOperator.get_poi_data_by_sql(request, function_title, connection)
        return Response(res)

    # SQL查询获取poi数据
    @action(detail=False, methods=['POST'], url_path='get_poi_data_by_sql')
    def get_poi_data_by_sql(self, request):
        function_title = "根据SQL获取POI数据"
        buisnessOperator = BuisnessOperator(connection)
        CommonHelper.logger_json_key_value(request, logger)
        res = buisnessOperator.get_poi_data_by_sql(request, function_title, connection)
        return Response(res)


# 视口书签数据表viewer类
class TtViewBookmarkDataViewSet(viewsets.ModelViewSet):
    queryset = TtTaskDirectionBookmarkData.objects.all().order_by('id')
    serializer_class = TtViewBookmarkDataSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # 方向书签数据分页查询
    @action(detail=False, methods=['POST'], url_path='query_list')
    def query_list(self, request):
        try:
            function_title = "方向书签数据分页查询"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.query_view_bookmark_data_list(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    def list(self, request, *args, **kwargs):
        try:
            function_title = "获取方向书签列表"
            start = LoggerHelper.set_start_log_info(logger)
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                page_response = self.get_paginated_response(serializer.data)
                # 增加url头
                page_response.data["url_head"] = CommonHelper.get_url_head()
                suceess_flag = "成功"
                data = Result.list(page_response.data, message=function_title + "{}".format(suceess_flag))
                LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                              function_title)
            return Response(data)
        except Exception as exp:
            # msg = "{}失败".format(function_title)
            fail_flag = "失败"
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    def create(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        view_bookmark_name = request.data["view_bookmark_name"]
        if len(TtTaskDirectionBookmarkData.objects.filter(view_bookmark_name=view_bookmark_name)) > 0:
            res = {
                'success': False,
                'info': "新增的视口书签名:{}已存在，请换个名称".format(view_bookmark_name)
            }

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增视口书签失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            request.data["id"] = SnowflakeIDUtil.snowflakeId()
            request.data["create_user_id"] = request.auth.user_id
            request.data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            bingtuan_pt_xy_list = []
            bd_pt_xy_list = []
            district_pt_xy_list = []
            if "bingtuan_code_list" in request.data and str(request.data["bingtuan_code_list"]).strip() != "":
                for bingtuan_code in request.data["bingtuan_code_list"].split(","):
                    if TmShituanPt.objects.filter(code=bingtuan_code).exists():
                        shituan_pt = TmShituanPt.objects.get(code=bingtuan_code)
                        bingtuan_pt_xy_list.append(",".join([str(shituan_pt.lon), str(shituan_pt.lat)]))
            if "bd_code_list" in request.data and str(request.data["bd_code_list"]).strip() != "":
                for bd_code in request.data["bd_code_list"].split(","):
                    if TtBdxq.objects.filter(bdid=bd_code).exists():
                        bd_pt = TtBdxq.objects.get(bdid=bd_code)
                        bd_pt_xy_list.append(",".join([str(bd_pt.zuobiao_jingdu), str(bd_pt.zuobiao_weidu)]))
            if "district_code_list" in request.data and str(request.data["district_code_list"]).strip() != "":
                for district_code in request.data["district_code_list"].split(","):
                    if TmDistrictPt.objects.filter(code=district_code).exists():
                        district_pt = TmDistrictPt.objects.get(code=district_code)
                        district_pt_xy_list.append(",".join([str(district_pt.lon), str(district_pt.lat)]))
            request.data["bingtuan_pt_xy_list"] = ";".join(bingtuan_pt_xy_list)
            request.data["bd_pt_xy_list"] = ";".join(bd_pt_xy_list)
            request.data["district_pt_xy_list"] = ";".join(district_pt_xy_list)
            TtTaskDirectionBookmarkData.objects.create(**request.data)

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增视口书签",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))

            res = {
                'success': True,
                'info': "新增视口书签:{}成功".format(request.data["view_bookmark_name"])
            }
            return Response(res)

    def update(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        id = kwargs["pk"]
        if len(TtTaskDirectionBookmarkData.objects.filter(id=id)) > 0:
            old_view_bookmark_name = TtTaskDirectionBookmarkData.objects.filter(id=id)[0].view_bookmark_name

        new_view_bookmark_name = request.data["view_bookmark_name"]
        if old_view_bookmark_name != new_view_bookmark_name and len(
                TtTaskDirectionBookmarkData.objects.filter(view_bookmark_name=new_view_bookmark_name)) > 0:
            res = {
                'success': False,
                'info': "更新的视口书签名:{}已存在，请换个名称".format(new_view_bookmark_name)
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新视口书签失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新视口书签",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            TtTaskDirectionBookmarkData.objects.filter(id=id).update(**request.data)
            # super().update(request, *args, **kwargs)
            res = {
                'success': True,
                'info': "修改视口书签成功"
            }
            return Response(res)

    # # 删除
    def destroy(self, request, *args, **kwargs):
        title = "删除视口书签"
        res = ""
        id = kwargs["pk"]
        start = time.perf_counter()
        try:
            super().destroy(request, *args, **kwargs)
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title,
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            res = {
                'success': True,
                'info': "{}(编号为{})成功".format(title, id)
            }
        except Exception as exp:
            res = {
                'success': False,
                'info': "{}(编号为{})失败，原因为：{}".format(title, id, str(exp))
            }
        finally:
            res

        return Response(res)


class TtServiceInterfaceTypeViewSet(viewsets.ModelViewSet):
    queryset = TtSupermapServiceInterfaceType.objects.all().order_by('id')
    serializer_class = TtServiceInterfaceTypeSerializer
    permission_classes = (IsAuthenticated,)
    # token认证
    # authentication_classes = (TokenAuthentication,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)

    def list(self, request, *args, **kwargs):
        interface_type_category = self.request.query_params.get('interface_type_category')
        results = TtSupermapServiceInterfaceType.objects.filter(interface_type_category=interface_type_category)
        data = []
        for result in results:
            data.append(TtServiceInterfaceTypeSerializer(result).data)
        results = {'results': data}
        return Response(results)


class TtKeyPointAreaDataViewSet(viewsets.ModelViewSet):
    queryset = TtKeyPointAreaData.objects.all().order_by('id')
    serializer_class = TtKeyPointAreaDataSerializer
    permission_classes = (IsAuthenticated,)
    # token认证
    # authentication_classes = (TokenAuthentication,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)

    @action(detail=False, methods=['POST'], url_path='get_list')
    def get_list(self, request, *args, **kwargs):

        # interface_type_category = self.request.query_params.get('interface_type_category')
        results = TtKeyPointAreaData.objects.all().order_by('order_num')
        data = []
        for result in results:
            data.append(TtKeyPointAreaDataSerializer(result).data)
        for each in data:
            each.pop("create_user_id")
            each.pop("create_time")
            each.pop("modify_user_id")
            each.pop("modify_time")
            each.pop("address")
            each.pop("province")
            each.pop("city")
            each.pop("area")
            each.pop("doc_url")
            each.pop("overview")
            each.pop("thumbnail")
            if "poi_data" in each:
                each.pop("poi_type")
        results = {'results': data}
        # results["url_head"] = CommonHelper.get_url_head()
        return Response(results)

    @action(detail=False, methods=['POST'], url_path='get_detail')
    def get_detail(self, request, *args, **kwargs):
        id = self.request.data["id"]
        result = TtKeyPointAreaData.objects.get(id=id)
        result.doc_url = "http://{}:{}{}report/{}".format(settings.PROJECT_SERVICE_IP,
                                                          settings.PROJECT_SERVICE_PORT,
                                                          settings.STATIC_URL,
                                                          result.doc_url)
        data = {}
        data = (TtKeyPointAreaDataSerializer(result).data)
        result = {'result': data}
        result["url_head"] = CommonHelper.get_url_head()
        return Response(result)

    def get_object(self, *args, **kwargs):
        result = ""

        # 更新会进来
        if self.action == "update":
            return super().get_object(*args, **kwargs)
        else:
            result = super().get_object(*args, **kwargs)
            if getattr(result, 'doc_url') is not None and str(result.doc_url).strip() != "":
                result.doc_url = "http://{}:{}{}report/{}".format(settings.PROJECT_SERVICE_IP,
                                                                  settings.PROJECT_SERVICE_PORT,
                                                                  settings.STATIC_URL,
                                                                  result.doc_url)
                result.url_head = CommonHelper.get_url_head()
            data = {}
            data["result"] = result
            data["url_head"] = CommonHelper.get_url_head()

            return result

    def list(self, request, *args, **kwargs):

        # interface_type_category = self.request.query_params.get('interface_type_category')
        results = TtKeyPointAreaData.objects.all().order_by('order_num')
        data = []
        for result in results:
            result.doc_url = "http://{}:{}{}report/{}".format(settings.PROJECT_SERVICE_IP,
                                                              settings.PROJECT_SERVICE_PORT,
                                                              settings.STATIC_URL,
                                                              result.doc_url)
            data.append(TtKeyPointAreaDataSerializer(result).data)
        for each in data:
            each.pop("create_user_id")
            each.pop("create_time")
            each.pop("modify_user_id")
            each.pop("modify_time")
            if "poi_data" in each:
                each.pop("poi_type")
        results = {'results': data}
        results["url_head"] = CommonHelper.get_url_head()
        return Response(results)


# 标注数据热点收藏图层viewer类
class TtAnnotationHotDataViewSet(viewsets.ModelViewSet):
    queryset = TtAnnotationHotData.objects.all().order_by('id')
    serializer_class = TtAnnotationHotDataSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # 获取所有标注图层
    @action(detail=False, methods=['post'], url_path='get_all_bztree')
    def get_all_bztree(self, request):
        function_title = "获取所有标注图层"
        CommonHelper.logger_json_key_value(request, logger)
        commonOperator = CommonOperator(connection)
        res = commonOperator.get_all_bztree_new(request, function_title)
        return Response(res)

    # 获取指定数据表的可查询字段列表
    @action(detail=False, methods=['post'], url_path='get_query_fields_of_table')
    def get_query_fields_of_table(self, request):
        function_title = "获取指定数据表的可查询字段列表"
        CommonHelper.logger_json_key_value(request, logger)
        commonOperator = CommonOperator(connection)
        res = commonOperator.get_query_fields_of_table(request, function_title, connection)
        return Response(res)

    # 获取指定数据表和字段的唯一值
    @action(detail=False, methods=['post'], url_path='get_unique_value_of_field_in_table')
    def get_unique_value_of_field_in_table(self, request):
        function_title = "获取指定数据表和字段的唯一值"
        CommonHelper.logger_json_key_value(request, logger)
        commonOperator = CommonOperator(connection)
        res = commonOperator.get_unique_value_of_field_in_table(request, function_title, connection)
        return Response(res)

    # 判断数据表查询的where条件是否有效
    @action(detail=False, methods=['post'], url_path='is_valid_of_whereclause_of_table')
    def is_valid_of_whereclause_of_table(self, request):
        function_title = "判断数据表查询的where条件是否有效"
        CommonHelper.logger_json_key_value(request, logger)
        commonOperator = CommonOperator(connection)
        res = commonOperator.is_valid_of_whereclause_of_table(request, function_title, connection)
        return Response(res)


    # 分页查询热点图层
    @action(detail=False, methods=['POST'], url_path='query_list')
    def query_list(self, request):
        try:
            function_title = "热点图层数据分页查询"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.query_hot_data_list(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 创建热点图层
    @action(detail=False, methods=['POST'], url_path='create_hot_data')
    def create_hot_data(self, request):
        try:
            function_title = "创建热点图层数据"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            if len(TtAnnotationHotData.objects.filter(hot_data_name=request.data["hot_data_name"])) > 0:
                res = {
                    'success': False,
                    'info': "新增的热点图层名称:{}已存在，请换个名称".format(request.data["hot_data_name"])
                }

                logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                end = time.perf_counter()
                t = end - start
                logger.info("总共用时{}秒".format(t))
                LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增视口书签失败",
                                             request.path,
                                             HttpHelper.get_params_request(request),
                                             t, HttpHelper.get_ip_request(request))
                return Response(res)
            else:
                operator = BuisnessOperator(connection)
                response_data = operator.create_hot_data(request)
                LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                              function_title)
                return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 更新热点图层
    @action(detail=False, methods=['POST'], url_path='update_hot_data')
    def update_hot_data(self, request):
        try:
            function_title = "更新热点图层数据"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            id = request.data["id"]
            if len(TtAnnotationHotData.objects.filter(id=id)) > 0:
                old_hot_data_name = TtAnnotationHotData.objects.filter(id=id)[0].hot_data_name
            new_hot_data_name = request.data["hot_data_name"]
            if old_hot_data_name != new_hot_data_name and len(
                    TtAnnotationHotData.objects.filter(hot_data_name=new_hot_data_name)) > 0:
                res = {
                    'success': False,
                    'info': "更新的热点图层名称:{}已存在，请换个名称".format(new_hot_data_name)
                }
                logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                end = time.perf_counter()
                t = end - start
                logger.info("总共用时{}秒".format(t))
                LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新视口书签失败",
                                             request.path,
                                             HttpHelper.get_params_request(request),
                                             t, HttpHelper.get_ip_request(request))
                return Response(res)
            else:
                operator = BuisnessOperator(connection)
                response_data = operator.update_hot_data(request)
                LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                              function_title)
                return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 删除热点图层
    def destroy(self, request, *args, **kwargs):
        title = "删除热点图层"
        res = ""
        id = kwargs["pk"]
        start = time.perf_counter()
        try:
            view_name = TtAnnotationHotData.objects.get(id=id).hot_data_combine_view
            super().destroy(request, *args, **kwargs)
            # 同时删除视图
            # TtAnnotationHotData.objects.filter(annotation_id=id).delete()
            operator = BuisnessOperator(connection)
            operator.drop_view(view_name)

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title,
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            res = {
                'success': True,
                'info': "{}(编号为{})成功".format(title, id)
            }
        except Exception as exp:
            res = {
                'success': False,
                'info': "{}(编号为{})失败，原因为：{}".format(title, id, str(exp))
            }
        finally:
            res

        return Response(res)


# 部队详情表viewer类
class TtBdxqViewSet(viewsets.ModelViewSet):
    queryset = TtBdxq.objects.all().order_by('bdid')
    serializer_class = TtBdxqSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # 返回所有部队力量数据
    @action(detail=False, methods=['POST'], url_path='query_list')
    def query_list(self, request):
        try:
            function_title = "所有部队力量数据查询"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.get_all_bdxq(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 部队力量数据分页查询
    @action(detail=False, methods=['POST'], url_path='query_zhidui')
    def query_zhidui(self, request):
        try:
            function_title = "部队力量数据分页查询"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.query_bd_zhidui_data_list(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 获取指定部队力量和下设力量的名称及坐标
    @action(detail=False, methods=['POST'], url_path='get_zd_relation')
    def get_zd_relation(self, request):
        try:
            function_title = "获取指定部队力量和下设力量的名称及坐标"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.get_zd_relation(request, connection)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 获取指定部队力量的详情
    @action(detail=False, methods=['POST'], url_path='get_bd_detail')
    def get_bd_detail(self, request):
        try:
            function_title = "获取指定部队力量的详情"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.get_bd_detail(request, connection)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))


# 所属/防卫目标类型表viewer类
class TtFwmbViewSet(viewsets.ModelViewSet):
    queryset = TtFwmb.objects.all().order_by('f_id')
    serializer_class = TtFwmbSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # 获取所有的防卫目标类型
    @action(detail=False, methods=['GET'], url_path='getAll')
    def get_all_fwmb(self, request, *args, **kwargsst):
        try:
            query = CommonOperator(connection)
            CommonHelper.logger_json_key_value(request, logger)
            # corps_code = self.request.query_params.get('corps_code', '')
            res = query.get_all_fwmb(request)

        except Exception as exp:
            res = {
                'success': False,
                'info': "获取新疆兵团的师级数据失败:{}".format(str(exp))
            }
            pass
        return Response(res)

    # 查询指定的所属/防卫目标图层表
    @action(detail=False, methods=['POST'], url_path='query_table')
    def query_table(self, request):
        try:
            function_title = "查询指定的所属/防卫目标图层表"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.query_fwmb_table(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 获取指定目录下的所有/防卫目标图层表的标绘图形和空间范围
    @action(detail=False, methods=['POST'], url_path='get_annotations_of_tables')
    def get_annotations_of_tables(self, request):
        try:
            function_title = "获取指定目录下的所有/防卫目标图层表的标绘图形和空间范围"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.get_annotations_of_fwmb_tables(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 获取指定标绘图形的详情字段信息
    @action(detail=False, methods=['POST'], url_path='get_detials_of_annotation_data')
    def get_detials_of_annotation_data(self, request):
        try:
            function_title = "获取指定标绘图形的字段信息"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.get_detials_of_fwmb_annotation_data(request, connection)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 所属/防卫目标类型数据分页查询
    @action(detail=False, methods=['POST'], url_path='query_list')
    def query_list(self, request):
        try:
            function_title = "所属/防卫目标类型数据分页查询"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.query_fwmb_type_data_list(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 获取所属/防卫目标的图层表的字段
    @action(detail=False, methods=['POST'], url_path='get_filedinfo')
    def get_filedinfo(self, request):
        try:
            function_title = "获取所属/防卫目标的图层表的字段"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.query_fwmb_field_info_front_input(request, connection)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 增加所属/防卫目标的图层表的标注信息
    @action(detail=False, methods=['POST'], url_path='add_annotation')
    def add_annotation(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        table_id = request.data["table_id"]
        table_ename = TtFwmbTableRelation.objects.get(table_id=table_id).table_ename
        request.data.pop("table_id")
        cursor = connection.cursor()
        request.data["id"] = SnowflakeIDUtil.snowflakeId()

        sql = "select * from  {} where name ='{}'".format(table_ename, request.data["name"])
        cursor.execute(sql)
        if cursor.fetchone():
            res = {
                'success': False,
                'info': "新增名称:{}已存在，请换个名称".format(request.data["name"])
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增标注失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:

            # 图片字段
            if "pics_file_id" in request.data:
                pics_file_id = request.data["pics_file_id"]
                pics_path = []
                for pic_file_id in pics_file_id:
                    if TtUploadFileData.objects.filter(id=pic_file_id).exists():
                        pics_path.append(TtUploadFileData.objects.get(id=pic_file_id).path)
                pics_path = ",".join(pics_path)
                request.data.pop("pics_file_id")
                request.data["pics_path"] = pics_path
            # 视频字段
            if "videos_file_id" in request.data:
                videos_file_id = request.data["videos_file_id"]
                videos_path = []
                for video_file_id in videos_file_id:
                    if TtUploadFileData.objects.filter(id=video_file_id).exists():
                        videos_path.append(TtUploadFileData.objects.get(id=video_file_id).path)
                videos_path = ",".join(videos_path)
                request.data.pop("videos_file_id")
                request.data["videos_path"] = videos_path
            annotation_sysmbol_style_data = request.data["annotation_sysmbol_style"]
            request.data["annotation_sysmbol_style"] = json.dumps(request.data["annotation_sysmbol_style"],
                                                                  ensure_ascii=False)
            # 确保insert sql语句能正常执行
            request.data["annotation_sysmbol_style"] = request.data["annotation_sysmbol_style"].replace("'", "''")

            request.data["create_user_id"] = request.auth.user_id
            request.data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 更新空间字段内容（采用GEOMETRYCOLLECTION保存符合几何对象，因为前端会传过来点、线、面）
            geom_collection = businessHelper.get_geometrycollection_from_annotation_sysmbol_style(
                annotation_sysmbol_style_data)
            request.data["geom"] = geom_collection

            insert_sql = businessHelper.build_insert_sql(table_ename, request.data, connection)
            print(insert_sql)
            cursor.execute(insert_sql)
            connection.commit()

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增标注",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))

            res = {
                'success': True,
                'info': "新增标注:{}成功".format(request.data["name"])
            }
            return Response(res)

    # 更新所属/防卫目标的图层表的标注信息
    @action(detail=False, methods=['POST'], url_path='update_annotation')
    def update_annotation(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        id = request.data["id"]
        table_id = request.data["table_id"]
        table_ename = TtFwmbTableRelation.objects.get(table_id=table_id).table_ename
        request.data.pop("table_id")
        request.data.pop("id")
        # id = kwargs["pk"]
        cursor = connection.cursor()
        sql = "select name from  {} where id ='{}'".format(table_ename, id)
        cursor.execute(sql)
        record = cursor.fetchone()
        old_name = record[0]
        new_name = request.data["name"]
        sql = "select * from  {} where name ='{}'".format(table_ename, new_name)
        cursor.execute(sql)
        buisnessOperator = BuisnessOperator(connection)
        if old_name != new_name and cursor.fetchone():
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新标注失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            res = {
                'success': False,
                'info': "更新名称:{}已存在，请换个名称".format(request.data["name"])
            }
            return Response(res)

        else:

            # 图片字段
            if "pics_file_id" in request.data:
                pics_file_id = request.data["pics_file_id"]
                pics_path = []
                for pic_file_id in pics_file_id:
                    if TtUploadFileData.objects.filter(id=pic_file_id).exists():
                        pics_path.append(TtUploadFileData.objects.get(id=pic_file_id).path)
                pics_path = ",".join(pics_path)
                request.data.pop("pics_file_id")
                request.data["pics_path"] = pics_path
            # 视频字段
            if "videos_file_id" in request.data:
                videos_file_id = request.data["videos_file_id"]
                videos_path = []
                for video_file_id in videos_file_id:
                    if TtUploadFileData.objects.filter(id=video_file_id).exists():
                        videos_path.append(TtUploadFileData.objects.get(id=video_file_id).path)
                videos_path = ",".join(videos_path)
                request.data.pop("videos_file_id")
                request.data["videos_path"] = videos_path
            annotation_sysmbol_style_data = request.data["annotation_sysmbol_style"]
            request.data["annotation_sysmbol_style"] = json.dumps(request.data["annotation_sysmbol_style"],
                                                                  ensure_ascii=False)
            # 确保sql语句能正常执行
            request.data["annotation_sysmbol_style"] = request.data["annotation_sysmbol_style"].replace("'", "''")

            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 更新空间字段内容（采用GEOMETRYCOLLECTION保存符合几何对象，因为前端会传过来点、线、面）
            geom_collection = businessHelper.get_geometrycollection_from_annotation_sysmbol_style(
                annotation_sysmbol_style_data)
            request.data["geom"] = geom_collection

            update_sql = businessHelper.build_update_sql(table_ename, request.data, connection, "id={}".format(id))
            print(update_sql)
            cursor.execute(update_sql)
            connection.commit()

            res = {
                'success': True,
                'info': "修改标注成功"
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新标注",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)

    # 删除所属/防卫目标的图层表的标注信息
    @action(detail=False, methods=['POST'], url_path='delete_annotation')
    def delete_annotation(self, request, *args, **kwargs):
        title = "删除标注"
        res = ""
        # id = kwargs["pk"]
        start = time.perf_counter()
        try:
            id = request.data["id"]
            table_id = request.data["table_id"]
            table_ename = TtFwmbTableRelation.objects.get(table_id=table_id).table_ename
            sql = "delete from {} where id={}".format(table_ename, id)
            cursor = connection.cursor()
            cursor.execute(sql)
            connection.commit()
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title,
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            res = {
                'success': True,
                'info': "{}(编号为{})成功".format(title, id)
            }
        except Exception as exp:
            res = {
                'success': False,
                'info': "{}(编号为{})失败，原因为：{}".format(title, id, str(exp))
            }
        finally:
            res

        return Response(res)

    #
    # 导入所属/防卫目标数据表
    @action(detail=False, methods=['POST'], url_path='import_excel')
    def import_excel(self, request):
        try:
            function_title = "导入所属/防卫目标数据excel表"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.import_xls_into_fwmb_table(request, connection)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 导出所属/防卫目标数据表
    @action(detail=False, methods=['POST'], url_path='export_excel')
    def export_excel(self, request):
        try:
            function_title = "导出所属/防卫目标数据为excel表"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.export_xls_from_fwmb_table(request, connection)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 同时创建目录/数据表
    def create(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        buisnessOperator = BuisnessOperator(connection)
        f_pid = request.data["f_pid"]
        f_name = request.data["f_name"]
        f_mblx = request.data["f_mblx"]
        if len(TtFwmb.objects.filter(f_name=f_name, f_mblx=f_mblx)) > 0:
            res = {
                'success': False,
                'info': "新增的目标/数据表名称:{}已存在，请换个名称".format(f_name)
            }

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增目标类型失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            type = request.data["f_type"]
            request.data["f_id"] = SnowflakeIDUtil.snowflakeId()
            request.data["create_user_id"] = request.auth.user_id
            request.data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            max_num = CommonHelper.getFwmbMaxOrderNum(f_pid, type, connection)
            request.data["order_num"] = max_num + 1
            request.data["f_pname"] = TtFwmb.objects.get(f_id=request.data["f_pid"]).f_name
            # 创建目录
            if type == 1:
                TtFwmb.objects.create(**request.data)
            # 创建数据表
            elif type == 0:
                request.data["f_linktableid"] = SnowflakeIDUtil.snowflakeId()
                tableinfo = request.data["tableinfo"]
                request.data.pop("tableinfo")
                # 判断表名在数据库是否有
                if businessHelper.is_table_ename_exist(tableinfo["table_ename"], connection):
                    res = {
                        'success': False,
                        'info': "数据表{}已存在，请换个名称".format(tableinfo["table_ename"])
                    }
                    return Response(res)
                else:
                    if businessHelper.is_table_cname_exist(request.data["f_name"], connection):
                        res = {
                            'success': False,
                            'info': "数据表{}已存在，请换个名称".format(request.data["f_name"])
                        }
                        return Response(res)
                    else:
                        TtFwmb.objects.create(**request.data)
                        # {
                        #     "tableinfo": {
                        #         "table_ename": "table_001",
                        #         "field_info": [
                        #             {
                        #                 "field_cname": "配备设施", //字段中文名
                        #                 "field_ename": "wuqizhuangbei", //字段英文名
                        #                 "field_type": "string", //字段类型
                        #             },
                        #             {
                        #                 "field_cname": "配备设施2", //字段中文名
                        #                 "field_ename": "wuqizhuangbei2", //字段英文名
                        #                 "field_type": "string", //字段类型
                        #             }
                        #         ]
                        #     }
                        # }

                        # 创建表
                        tableinfo["table_cname"] = request.data["f_name"]
                        businessHelper.create_fwmb_table(tableinfo, connection)

                        obj = {}
                        obj["id"] = SnowflakeIDUtil.snowflakeId()
                        obj["table_id"] = request.data["f_linktableid"]
                        if "f_desc" in request.data:
                            obj["remark"] = request.data["f_desc"]
                        obj["table_ename"] = tableinfo["table_ename"]
                        obj["table_cname"] = tableinfo["table_cname"]
                        TtFwmbTableRelation.objects.create(**obj)

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增目标类型",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))

            res = {
                'success': True,
                'info': "新增目标类型:{}成功".format(request.data["f_name"])
            }
            return Response(res)

    # 已有目录表节点，创建数据表
    @action(detail=False, methods=['POST'], url_path='add_table')
    def add_table(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        buisnessOperator = BuisnessOperator(connection)
        f_id = request.data["f_id"]
        f_name = request.data["f_name"]
        f_mblx = request.data["f_mblx"]
        type = request.data["f_type"]
        # request.data["f_id"] = SnowflakeIDUtil.snowflakeId()
        request.data["modify_user_id"] = request.auth.user_id
        request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 创建数据表
        request.data["f_linktableid"] = SnowflakeIDUtil.snowflakeId()
        tableinfo = request.data["tableinfo"]
        request.data.pop("tableinfo")
        # 判断表名在数据库是否有
        if businessHelper.is_table_ename_exist(tableinfo["table_ename"], connection):
            res = {
                'success': False,
                'info': "数据表{}已存在，请换个名称".format(tableinfo["table_ename"])
            }
            return Response(res)
        else:
            if businessHelper.is_table_cname_exist(request.data["f_name"], connection):
                res = {
                    'success': False,
                    'info': "数据表{}已存在，请换个名称".format(request.data["f_name"])
                }
                return Response(res)
            else:
                # 更新连接表ID
                TtFwmb.objects.filter(f_id=f_id).update(**request.data)
                # 创建表
                tableinfo["table_cname"] = request.data["f_name"]
                # 默认要创建id字段和geom等字段
                businessHelper.create_fwmb_table(tableinfo, connection)

                obj = {}
                obj["id"] = SnowflakeIDUtil.snowflakeId()
                obj["table_id"] = request.data["f_linktableid"]
                if "f_desc" in request.data:
                    obj["remark"] = request.data["f_desc"]
                obj["table_ename"] = tableinfo["table_ename"]
                obj["table_cname"] = tableinfo["table_cname"]
                TtFwmbTableRelation.objects.create(**obj)

                logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                end = time.perf_counter()
                t = end - start
                logger.info("总共用时{}秒".format(t))
                LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增目标类型",
                                             request.path,
                                             HttpHelper.get_params_request(request),
                                             t, HttpHelper.get_ip_request(request))

                res = {
                    'success': True,
                    'info': "新增目标类型表:{}成功".format(request.data["f_name"])
                }
                return Response(res)

    # 更新顺序（同级节点下的目录节点和数据表的顺序是单独的，都从0开始）
    @action(detail=False, methods=['POST'], url_path='update_order_num')
    def update_order_num(self, request):
        try:
            function_title = "更新数据表节点的顺序"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.update_order_num(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 更新目录/数据表
    def update(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        id = kwargs["pk"]
        if len(TtFwmb.objects.filter(f_id=id)) > 0:
            old_name = TtFwmb.objects.filter(f_id=id)[0].f_name
            old_order_num = TtFwmb.objects.get(f_id=id).order_num
        f_pid = request.data["f_pid"]
        f_type = request.data["f_type"]
        new_name = request.data["f_name"]

        if old_name != new_name and len(
                TtFwmb.objects.filter(f_name=new_name, f_type=f_type)) > 0:
            res = {
                'success': False,
                'info': "更新的目录/数据表名称:{}已存在，请换个名称".format(new_name)
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新防卫目标失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            exist_order_num_list = CommonHelper.getFwmbOrderNumList(f_pid, f_type, connection)
            if "order_num" in request.data and old_order_num != request.data["order_num"] and request.data[
                "order_num"] in exist_order_num_list:
                res = {
                    'success': False,
                    'info': "更新的排序字段值:{}已存在，请换个名称".format(request.data["order_num"])
                }
                logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                end = time.perf_counter()
                t = end - start
                logger.info("总共用时{}秒".format(t))
                LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新防卫目标失败",
                                             request.path,
                                             HttpHelper.get_params_request(request),
                                             t, HttpHelper.get_ip_request(request))
                return Response(res)
            else:

                request.data["modify_user_id"] = request.auth.user_id
                request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # 更新目录
                if f_type == 1:
                    TtFwmb.objects.filter(f_id=id).update(**request.data)
                # 更新数据表
                elif f_type == 0:
                    tableinfo = request.data["tableinfo"]
                    request.data.pop("tableinfo")
                    table_id = TtFwmb.objects.get(f_id=id).f_linktableid
                    if TtFwmbTableRelation.objects.filter(table_id=table_id).exists():
                        old_table_ename = TtFwmbTableRelation.objects.get(table_id=table_id).table_ename
                        old_table_cname = TtFwmbTableRelation.objects.get(table_id=table_id).table_cname
                        # 判断表名在数据库是否有
                        if tableinfo["table_ename"] != old_table_ename and businessHelper.is_table_ename_exist(
                                tableinfo["table_ename"], connection):
                            res = {
                                'success': False,
                                'info': "数据表{}已存在，请换个名称".format(tableinfo["table_ename"])
                            }
                            return Response(res)
                        else:
                            # 判断表名在数据库是否有
                            if request.data["f_name"] != old_table_cname and businessHelper.is_table_cname_exist(
                                    request.data["f_name"], connection):
                                res = {
                                    'success': False,
                                    'info': "数据表{}已存在，请换个名称".format(request.data["f_name"])
                                }
                                return Response(res)
                            else:
                                TtFwmb.objects.filter(f_id=id).update(**request.data)
                                # 创建表
                                tableinfo["table_cname"] = request.data["f_name"]
                                businessHelper.create_fwmb_table(tableinfo, connection)

                                obj = {}
                                if "f_desc" in request.data:
                                    obj["remark"] = request.data["f_desc"]
                                obj["table_ename"] = tableinfo["table_ename"]
                                obj["table_cname"] = tableinfo["table_cname"]
                                TtFwmbTableRelation.objects.filter(table_id=table_id).update(**obj)

                logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                end = time.perf_counter()
                t = end - start
                logger.info("总共用时{}秒".format(t))
                LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新标注",
                                             request.path,
                                             HttpHelper.get_params_request(request),
                                             t, HttpHelper.get_ip_request(request))

                res = {
                    'success': True,
                    'info': "修改防卫目标成功"
                }
                return Response(res)

    # # 删除
    def destroy(self, request, *args, **kwargs):
        title = "删除目录或数据表"
        res = ""
        id = kwargs["pk"]
        start = time.perf_counter()
        try:
            if TtFwmb.objects.filter(f_id=id).exists():
                f_type = TtFwmb.objects.get(f_id=id).f_type
                f_pid = TtFwmb.objects.get(f_id=id).f_pid
                remove_f_id = TtFwmb.objects.get(f_id=id).f_id
                table_id = TtFwmb.objects.get(f_id=id).f_linktableid

                # 数据表
                if f_type == 0:
                    # 删除数据表后，跟它同级的其他数据表节点的order_num要重新计算
                    # 比如 0 1 2 3 把2删除后  变成 0 1 2
                    if TtFwmb.objects.filter(f_type=0, f_pid=f_pid).exists():
                        order_tables = TtFwmb.objects.filter(f_type=0, f_pid=f_pid)
                        order_infos = []
                        for order_table in order_tables:
                            order_infos.append({"f_id": order_table.f_id, "order_num": order_table.order_num})
                        order_infos = businessHelper.resort_order_num_after_remove_item(order_infos, remove_f_id)
                        for order_info in order_infos:
                            TtFwmb.objects.filter(f_id=order_info["f_id"]).update(order_num=order_info["order_num"])

                    # 删除表关系
                    if TtFwmbTableRelation.objects.filter(table_id=table_id).exists():
                        table_ename = TtFwmbTableRelation.objects.get(table_id=table_id).table_ename
                        TtFwmbTableRelation.objects.filter(table_id=table_id).delete()
                        # 如果是数据表，需要同时删除数据
                        businessHelper.drop_table(table_ename, connection)
                # 删除tt_fwmb里的数据表节点
                TtFwmb.objects.filter(f_id=id).delete()
                # super().destroy(request, *args, **kwargs)

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title,
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            res = {
                'success': True,
                'info': "{}(编号为{})成功".format(title, id)
            }
        except Exception as exp:
            res = {
                'success': False,
                'info': "{}(编号为{})失败，原因为：{}".format(title, id, str(exp))
            }
        finally:
            res

        return Response(res)


# 所属/防卫目标图层对应表viewer类
class TtFwmbTableRelationViewSet(viewsets.ModelViewSet):
    queryset = TtFwmbTableRelation.objects.all().order_by('id')
    serializer_class = TtFwmbTableRelationSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)


# 军标符号分级表viewer类
class TtJbfjViewSet(viewsets.ModelViewSet):
    queryset = TtJbfj.objects.all().order_by('id')
    serializer_class = TtJbfjSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)


# 地图书签数据表viewer类
class TtMapBookmarkDataViewSet(viewsets.ModelViewSet):
    queryset = TtMapBookmarkData.objects.all().order_by('id')
    serializer_class = TtMapBookmarkDataSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # 地图书签数据分页查询
    @action(detail=False, methods=['POST'], url_path='query_list')
    def query_list(self, request):
        try:
            function_title = "地图书签数据分页查询"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.query_map_bookmark_data_list(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    def list(self, request, *args, **kwargs):
        try:
            function_title = "获取地图方向书签列表"
            start = LoggerHelper.set_start_log_info(logger)
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                page_response = self.get_paginated_response(serializer.data)
                # 增加url头
                page_response.data["url_head"] = CommonHelper.get_url_head()
                suceess_flag = "成功"
                data = Result.list(page_response.data, message=function_title + "{}".format(suceess_flag))
                LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                              function_title)
            return Response(data)
        except Exception as exp:
            # msg = "{}失败".format(function_title)
            fail_flag = "失败"
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    def create(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        map_bookmark_name = request.data["map_bookmark_name"]
        if len(TtMapBookmarkData.objects.filter(map_bookmark_name=map_bookmark_name)) > 0:
            res = {
                'success': False,
                'info': "新增的地图书签名:{}已存在，请换个名称".format(map_bookmark_name)
            }

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增地图书签失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            obj = {}
            obj["id"] = SnowflakeIDUtil.snowflakeId()
            obj["create_user_id"] = request.auth.user_id
            obj["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            obj["modify_user_id"] = request.auth.user_id
            obj["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 根据name取file的值
            file = request.FILES.get('file')
            logger.info('上传图片是:%s' % file)
            if file is None:
                res = {
                    'success': False,
                    'info': "请选择要上传的截图"
                }
            else:
                # 创建mapsrceen文件夹
                CUSTOM_IAMGE_ROOT = os.path.join(BASE_DIR, '{}'.format(APP_NAME), '{}'.format(STATIC_NAME), 'mapsrceen'
                                                 )
                if not os.path.exists(CUSTOM_IAMGE_ROOT):
                    logger.info("创建mapsrceen文件夹")
                    os.makedirs(CUSTOM_IAMGE_ROOT)
                # 循环二进制写入
                file_name = file.name[0:file.name.rfind('.')]
                file_suffix = file.name[file.name.rfind('.') + 1:]
                with open(CUSTOM_IAMGE_ROOT + "/" + str(obj["id"]) + "." + file_suffix,
                          'wb') as f:
                    for i in file.readlines():
                        f.write(i)
                filepath = "mapsrceen/" + str(obj["id"]) + "." + file_suffix
                obj["map_screen"] = filepath
                request.data.pop("file")
                obj["lng"] = float(request.data["lng"])
                obj["lat"] = float(request.data["lat"])
                obj["elv"] = float(request.data["elv"])
                obj["heading"] = float(request.data["heading"])
                obj["pitch"] = float(request.data["pitch"])
                obj["roll"] = float(request.data["roll"])
                obj["map_bookmark_name"] = request.data["map_bookmark_name"]
                # 直接用request.data保存有问题
                TtMapBookmarkData.objects.create(**obj)

                logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                end = time.perf_counter()
                t = end - start
                logger.info("总共用时{}秒".format(t))
                LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增地图书签",
                                             request.path,
                                             HttpHelper.get_params_request(request),
                                             t, HttpHelper.get_ip_request(request))

                res = {
                    'success': True,
                    'info': "新增地图书签:{}成功".format(request.data["map_bookmark_name"])
                }
            return Response(res)

    def update(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        id = kwargs["pk"]
        if len(TtMapBookmarkData.objects.filter(id=id)) > 0:
            old_map_bookmark_name = TtMapBookmarkData.objects.filter(id=id)[0].map_bookmark_name

        new_map_bookmark_name = request.data["map_bookmark_name"]
        if old_map_bookmark_name != new_map_bookmark_name and len(
                TtMapBookmarkData.objects.filter(map_bookmark_name=new_map_bookmark_name)) > 0:
            res = {
                'success': False,
                'info': "更新的地图书签名:{}已存在，请换个名称".format(new_map_bookmark_name)
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新地图书签失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            obj = {}
            # 根据name取file的值
            file = request.FILES.get('file')
            logger.info('上传图片是:%s' % file)
            if file is not None:
                # 创建mapsrceen文件夹
                CUSTOM_IAMGE_ROOT = os.path.join(BASE_DIR, '{}'.format(APP_NAME), '{}'.format(STATIC_NAME), 'mapsrceen'
                                                 )
                if not os.path.exists(CUSTOM_IAMGE_ROOT):
                    logger.info("创建mapsrceen文件夹")
                    os.makedirs(CUSTOM_IAMGE_ROOT)
                # 循环二进制写入
                file_name = file.name[0:file.name.rfind('.')]
                file_suffix = file.name[file.name.rfind('.') + 1:]
                id2 = SnowflakeIDUtil.snowflakeId()
                with open(CUSTOM_IAMGE_ROOT + "/" + str(id2) + "." + file_suffix,
                          'wb') as f:
                    for i in file.readlines():
                        f.write(i)
                filepath = "mapsrceen/" + str(id2) + "." + file_suffix
                obj["map_screen"] = filepath

            obj["modify_user_id"] = request.auth.user_id
            obj["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            request.data.pop("file")
            obj["lng"] = float(request.data["lng"])
            obj["lat"] = float(request.data["lat"])
            obj["elv"] = float(request.data["elv"])
            obj["heading"] = float(request.data["heading"])
            obj["pitch"] = float(request.data["pitch"])
            obj["roll"] = float(request.data["roll"])
            obj["map_bookmark_name"] = request.data["map_bookmark_name"]
            # super().update(request, *args, **kwargs)
            TtMapBookmarkData.objects.filter(id=id).update(**obj)
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新地图书签",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            res = {
                'success': True,
                'info': "修改地图书签成功"
            }
            return Response(res)

    # # 删除
    def destroy(self, request, *args, **kwargs):
        title = "删除地图书签"
        res = ""
        id = kwargs["pk"]
        start = time.perf_counter()
        try:
            super().destroy(request, *args, **kwargs)
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title,
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            res = {
                'success': True,
                'info': "{}(编号为{})成功".format(title, id)
            }
        except Exception as exp:
            res = {
                'success': False,
                'info': "{}(编号为{})失败，原因为：{}".format(title, id, str(exp))
            }
        finally:
            res

        return Response(res)


# 我方类型表viewer类
class TtOursideDataViewSet(viewsets.ModelViewSet):
    queryset = TtOursideData.objects.all().order_by('id')
    serializer_class = TtOursideDataSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)


# 道路数据表viewer类
class TtRoadDataViewSet(viewsets.ModelViewSet):
    queryset = TtRoadData.objects.all().order_by('id')
    serializer_class = TtRoadDataSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)


# 工作区数据表viewer类
class TtWorkspaceDataViewSet(viewsets.ModelViewSet):
    queryset = TtWorkspaceData.objects.all().order_by('id')
    serializer_class = TtWorkspaceDataSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # 工作区数据分页查询
    @action(detail=False, methods=['POST'], url_path='query_list')
    def query_list(self, request):
        try:
            function_title = "工作区数据分页查询"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.query_workspace_data_list(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    def create(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        name = request.data["name"]
        if len(TtWorkspaceData.objects.filter(name=name)) > 0:
            res = {
                'success': False,
                'info': "新增的工作区名:{}已存在，请换个名称".format(name)
            }

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增工作区数据失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            request.data["id"] = SnowflakeIDUtil.snowflakeId()
            request.data["create_user_id"] = request.auth.user_id
            request.data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            TtWorkspaceData.objects.create(**request.data)

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增工作区数据",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))

            res = {
                'success': True,
                'info': "新增工作区数据:{}成功".format(request.data["name"])
            }
            return Response(res)

    def update(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        id = kwargs["pk"]
        if len(TtWorkspaceData.objects.filter(id=id)) > 0:
            old_name = TtWorkspaceData.objects.filter(id=id)[0].name

        new_name = request.data["name"]
        if old_name != new_name and len(
                TtWorkspaceData.objects.filter(name=new_name)) > 0:
            res = {
                'success': False,
                'info': "更新的工作区名:{}已存在，请换个名称".format(new_name)
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新工作区数据失败",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新工作区数据",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            super().update(request, *args, **kwargs)
            res = {
                'success': True,
                'info': "修改工作区数据成功"
            }
            return Response(res)

    # # 删除
    def destroy(self, request, *args, **kwargs):
        title = "删除工作区数据"
        res = ""
        id = kwargs["pk"]
        start = time.perf_counter()
        try:
            super().destroy(request, *args, **kwargs)
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title,
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            res = {
                'success': True,
                'info': "{}(编号为{})成功".format(title, id)
            }
        except Exception as exp:
            res = {
                'success': False,
                'info': "{}(编号为{})失败，原因为：{}".format(title, id, str(exp))
            }
        finally:
            res

        return Response(res)


# 专题图数据表viewer类
class TtThememapDataViewSet(viewsets.ModelViewSet):
    queryset = TtThememapData.objects.all().order_by('id')
    serializer_class = TtWorkspaceDataSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # 专题图数据分页查询
    @action(detail=False, methods=['POST'], url_path='query_list')
    def query_list(self, request):
        try:
            function_title = "专题图数据分页查询"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.query_thememap_data_list(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))


# 气象数据viewer类
# 只有viewer，没有实体表
class TtWeatherDataViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)

    # 气象数据获取
    @action(detail=False, methods=['POST'], url_path='get_weather_data')
    def get_weather_data(self, request):
        try:
            function_title = "气象数据获取"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.get_weather_data(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))



# 人流量监测区域viewer类
class TtPeopleFlowMonitorAreaViewSet(viewsets.ModelViewSet):
    queryset = TtPeopleFlowMonitorArea.objects.all().order_by('id')
    serializer_class = TtPeopleFlowMonitorAreaSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (ExpiringTokenAuthentication,)



    def list(self, request, *args, **kwargs):
        try:
            function_title = "人流量监测区域列表获取"
            start = LoggerHelper.set_start_log_info(logger)
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                page_response = self.get_paginated_response(serializer.data)
                # 增加url头
                page_response.data["url_head"] = CommonHelper.get_url_head()
                suceess_flag = "成功"
                data = Result.list(page_response.data, message=function_title + "{}".format(suceess_flag))
                LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                              function_title)
            return Response(data)
        except Exception as exp:
            # msg = "{}失败".format(function_title)
            fail_flag = "失败"
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))


    # 人流量监测数据获取
    @action(detail=False, methods=['POST'], url_path='get_flow')
    def get_flow(self, request):
        try:
            function_title = "人流量监测数据获取"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.get_peopleflow_data(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))

    # 人流量监测数据包导出
    @action(detail=False, methods=['POST'], url_path='export_flow')
    def export_flow(self, request):
        try:
            function_title = "人流量监测数据包导出"
            fail_flag = "失败"
            start = LoggerHelper.set_start_log_info(logger)
            operator = BuisnessOperator(connection)
            response_data = operator.export_peopleflow_data(request)
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          function_title)
            return response_data
        except Exception as exp:
            msg = "{}{}".format(function_title, fail_flag)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                       request.auth.user, request,
                                                       function_title, msg, None)
            return Result.fail(msg, str(exp))