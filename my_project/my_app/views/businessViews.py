#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2023/3/13 13:53
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : businessViews.py
# @Descr   : 业务操作视图
# @Software: PyCharm
import logging

from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from my_app.manage.commonManager import CommonOperator
from my_app.models import TtUploadFileData, \
    TmDdistrict
from my_app.serializers import TtUploadFileDataSerializer, TmDdistrictSerializer
from my_project.token import ExpiringTokenAuthentication

from my_project.my_app.utils.commonUtility import CommonHelper

logger = logging.getLogger('django')


# 业务表单操作实例
# # 预保单 附件2投保单
# class TtInsurancePreViewSet(viewsets.ModelViewSet):
#     queryset = TtInsurancePre.objects.all().order_by('id')
#     serializer_class = TtInsurancePreSerializer
#     permission_classes = (IsAuthenticated,)
#     # token认证
#     # authentication_classes = (TokenAuthentication,)
#     # 自定义token认证
#     authentication_classes = (ExpiringTokenAuthentication,)

#   增删改查方法，通过自动生成代码方法构建

#
#     # 预保单数据查询
#     @action(detail=False, methods=['GET'], url_path='sql')
#     def sql_search_pre_insurance_data(self, request, *args, **kwargsst):
#         try:
#             function_title = "查询预保数据"
#             query = BuisnessOperator(connection)
#             agent_name = self.request.query_params.get('agent_name', '')
#             pre_insurance_policy_number = self.request.query_params.get('pre_insurance_policy_number', '')
#             sub_insurance_policy_number = self.request.query_params.get('sub_insurance_policy_number', '')
#             insured_name = self.request.query_params.get('insured_name', '')
#             vessel_name = self.request.query_params.get('vessel_name', '')
#             insurance_year = self.request.query_params.get('insurance_year', '')
#             insurance_month = self.request.query_params.get('insurance_month', '')
#
#             res = query.sql_search_pre_insurance_data(function_title,agent_name, pre_insurance_policy_number,
#                                                       sub_insurance_policy_number,
#                                                       insured_name,
#                                                       vessel_name, insurance_year, insurance_month, request)
#
#         except Exception as exp:
#             res = {
#                 'success': False,
#                 'info': "{}失败:{}".format(function_title,str(exp))
#             }
#             pass
#         return Response(res)
#
#     # OCR识别投保单
#     @action(detail=False, methods=['POST'], url_path='ocrFileContent')
#     def ocr_file_content(self, request):
#         try:
#             businessOperator = BuisnessOperator(connection)
#             insurance_type, insurance_target_type, insurance_target_sub_name, insurance_target_sub_filed = CommonHelper.get_insurance_type_full(
#                 request)
#             insurance_info_full = insurance_type + "-" + insurance_target_type + "-" + insurance_target_sub_name
#             # (货运险 - 原油，附件2）
#             if insurance_info_full == "货运险-石油-原油":
#                 res = businessOperator.ocr_pre_insurance_file_content_cargo_insurance_crude_oil(request)
#             # (货运险 - 成品油）
#             if insurance_info_full == "货运险-石油-成品油":
#                 res = businessOperator.ocr_pre_insurance_file_content_cargo_insurance_finished_oil(request)
#             # (财产险-仓储-短期）
#             if insurance_info_full == "财产险-仓储-短期":
#                 res = businessOperator.ocr_insurance_file_content_property_insurance_storage_short_term(request)
#             # (财产险-仓储-长期）
#             if insurance_info_full == "财产险-仓储-长期":
#                 res = businessOperator.ocr_insurance_file_content_property_insurance_storage_long_term(request)
#         except Exception as exp:
#             res = {
#                 'success': False,
#                 'info': "OCR识别投保单失败:{}".format(str(exp))
#             }
#         return Response(res)
#
#    # 导出预保单
#     @action(detail=False, methods=['POST'], url_path='export')
#     def export_to_file(self, request):
#         try:
#             businessOperator = BuisnessOperator(connection)
#             insurance_type, insurance_target_type, insurance_target_sub_name, insurance_target_sub_filed = CommonHelper.get_insurance_type_full(
#                 request)
#             insurance_info_full = insurance_type + "-" + insurance_target_type + "-" + insurance_target_sub_name
#             # (货运险 - 原油，附件2）
#             if insurance_info_full == "货运险-石油-原油":
#                 res = businessOperator.export_pre_insurance_to_pdf_cargo_insurance_crude_oil(request)
#
#
#         except Exception as exp:
#             res = {
#                 'success': False,
#                 'info': "预保单导出失败:{}".format(str(exp))
#             }
#         return Response(res)


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
