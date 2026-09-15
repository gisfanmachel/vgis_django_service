#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/12/15 20:13
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : commonManager.py
# @Descr   : 多源数据
# @Software: PyCharm
import datetime
import logging
import os
import time
import uuid

from vgis_log.logTools import LoggerHelper
from vgis_utils.vgis_http.httpTools import HttpHelper

from my_app.module.common import models
from my_app.models import SysLog
from my_app.tasks import insert_log_info_async
from my_project import settings

logger = logging.getLogger('django')


class CommonOperator:
    def __init__(self, connection):
        self.connection = connection

    # 获取全国的分地区分省数据
    def get_region_and_province(self, request):
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            # 阶段 2 N+1 优化：原实现是「先取所有 region_code → 再每个 region_code 一次 SQL 查省份」，
            # 大区数 * 1 次 SQL；改为：
            #   1) DISTINCT 拿 region（去重）
            #   2) 单条 WHERE region_code IN (...) 把全量省份一次拿回
            #   3) Python 端按 region_code 分组拼 province_list
            # 大区 7 个 + 31 省 → 原本 8 次 SQL，现在 2 次
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT DISTINCT region_name, region_code FROM tm_region "
                "ORDER BY region_code LIMIT 100"
            )
            region_rows = cursor.fetchall()
            if not region_rows:
                return {
                    'success': True,
                    'total': 0,
                    'info': [],
                }
            region_codes = [int(r[1]) for r in region_rows]
            # ANY(%s) 数组参数：相比拼 IN 子句（占位符动态生成）更安全
            cursor.execute(
                "SELECT region_code, dis_name, dis_code FROM tm_region "
                "WHERE region_code = ANY(%s) ORDER BY region_code, id LIMIT 500",
                [region_codes],
            )
            province_rows = cursor.fetchall()
            # group by region_code（保留 SQL 内的顺序：先 region_code 再 id）
            province_grouped = {}
            for rc, dn, dc in province_rows:
                province_grouped.setdefault(int(rc), []).append((str(dn), int(dc)))
            data_list = []
            for record in region_rows:
                obj = {}
                obj['region_name'] = str(record[0])
                obj['region_code'] = int(record[1])
                province_list = []
                for province_name, province_code in province_grouped.get(obj['region_code'], []):
                    obj2 = {}
                    obj2["province_name"] = province_name
                    obj2["province_code"] = province_code
                    obj2['province_json'] = "http://{}:{}{}district/{}.json".format(
                        settings.PROJECT_SERVICE_IP,
                        settings.PROJECT_SERVICE_PORT,
                        settings.STATIC_URL,
                        province_code,
                    )
                    province_list.append(obj2)
                obj['province_list'] = province_list
                data_list.append(obj)
            res = {
                'success': True,
                'total': len(data_list),
                'info': data_list,
            }

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))

            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, "获取全国的分地区分省数据",
                                         "/api/tmDdistrict/getRegionAndProvince",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("获取全国的分地区分省数据失败：" + str(exp))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "获取全国的分地区分省数据失败：{}".format(str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))

            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, "获取全国的分地区分省数据失败",
                                         "/api/tmDdistrict/getRegionAndProvince",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 通过省份获取地市数据
    def get_city_by_province(self, province_code, request):
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            # 获取
            sql = "select dis_name,dis_code from tm_district where parent_code=%s"
            cursor = self.connection.cursor()
            cursor.execute(sql, [province_code])
            records = cursor.fetchall()
            data_list = []
            for record in records:
                obj = {}
                obj['city_name'] = str(record[0])
                obj['city_code'] = int(record[1])
                obj['city_json'] = "http://{}:{}{}district/{}.json".format(settings.ZXD_SERVICE_IP,
                                                                           settings.ZXD_SERVICE_PORT,
                                                                           settings.STATIC_URL,
                                                                           obj['city_code'])
                data_list.append(obj)
            res = {
                'success': True,
                'total': len(data_list),
                'info': data_list
            }

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, "通过省份获取地市数据",
                                         "/api/tmDdistrict/getCityByProvince",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))

        except Exception as exp:
            logger.error("通过省份获取地市数据失败：" + str(exp))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "通过省份获取地市数据失败：{}".format(str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))

            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, "通过省份获取地市数据失败",
                                         "/api/tmDdistrict/getCityByProvince",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 通过地市获取区县数据
    def get_county_by_city(self, city_code, request):
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            # 获取
            sql = "select dis_name,dis_code from tm_district where parent_code=%s"
            cursor = self.connection.cursor()
            cursor.execute(sql, [city_code])
            records = cursor.fetchall()
            data_list = []
            for record in records:
                obj = {}
                obj['county_name'] = str(record[0])
                obj['county_code'] = int(record[1])
                obj['county_json'] = "http://{}:{}{}district/{}.json".format(settings.PROJECT_SERVICE_IP,
                                                                             settings.PROJECT_SERVICE_PORT,
                                                                             settings.STATIC_URL,
                                                                             obj['county_code'])
                data_list.append(obj)
            res = {
                'success': True,
                'total': len(data_list),
                'info': data_list
            }

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, "通过地市获取区县数据",
                                         "/api/tmDdistrict/getCityByProvince",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("通过地市获取区县数据失败：" + str(exp))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "通过地市获取区县数据失败：{}".format(str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, "通过地市获取区县数据失败",
                                         "/api/tmDdistrict/getCityByProvince",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 单上传文件
    def upload_single_file(self, request):
        function_title = "上传文件"
        api_path = request.path
        start = LoggerHelper.set_start_log_info(logger)
        # 根据name取file的值
        file = request.FILES.get('file')
        logger.info('上传文件是:%s' % file)
        # 创建upload文件夹
        if not os.path.exists(settings.UPLOAD_ROOT):
            logger.info("创建upload文件夹")
            os.makedirs(settings.UPLOAD_ROOT)
        res = ""
        try:
            if file is None:
                res = {
                    'success': False,
                    'info': "请选择要上传的文件"
                }
            else:
                data = {}
                data['file_id'] = uuid.uuid4()
                data['file_name'] = file.name[0:file.name.rfind('.')]
                data['file_suffix'] = file.name[file.name.rfind('.') + 1:]
                data['upload_user_id'] = request.auth.user_id
                data['upload_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # 循环二进制写入
                with open(settings.UPLOAD_ROOT + "/" + str(data['file_id']) + "." + str(data['file_suffix']),
                          'wb') as f:
                    for i in file.readlines():
                        f.write(i)
                filepath = settings.UPLOAD_ROOT + "/" + str(data['file_id']) + "." + str(data['file_suffix'])
                file_size = os.path.getsize(filepath)
                # file_size = filesizeformat(file_size)
                data['file_size'] = file_size
                data['path'] = os.path.basename(filepath) + "/" + str(data['file_id']) + "." + str(data['file_suffix'])
                models.TtUploadFileData.objects.create(**data)
                res = {
                    'success': True,
                    'info': "上传文件成功",
                    'file_uuid': data['file_id']
                }

            LoggerHelper.set_end_log_info(SysLog, logger, start, api_path, request.auth.user, request,
                                          function_title)

        except Exception as exp:
            res = LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, api_path,
                                                             request.auth.user, request,
                                                             function_title, None, exp)
        finally:
            return res

    # 多上传文件
    def upload_multi_files(self, request):
        function_title = "上传文件"
        api_path = request.path
        start = LoggerHelper.set_start_log_info(logger)
        # 根据name取file的值
        files = request.FILES.getlist('files')
        logger.info('上传文件是:%s' % files)
        # 创建upload文件夹
        if not os.path.exists(settings.UPLOAD_ROOT):
            logger.info("创建upload文件夹")
            os.makedirs(settings.UPLOAD_ROOT)
        res = ""
        try:
            if files is None:
                res = {
                    'success': False,
                    'info': "请选择要上传的文件"
                }
            else:
                file_uuid_list = []
                for file in files:
                    data = {}
                    data['file_id'] = uuid.uuid4()
                    data['file_name'] = file.name[0:file.name.rfind('.')]
                    data['file_suffix'] = file.name[file.name.rfind('.') + 1:]
                    data['upload_user_id'] = request.auth.user_id
                    data['upload_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # 循环二进制写入
                    with open(settings.UPLOAD_ROOT + "/" + str(data['file_id']) + "." + str(data['file_suffix']),
                              'wb') as f:
                        for i in file.readlines():
                            f.write(i)
                    filepath = settings.UPLOAD_ROOT + "/" + str(data['file_id']) + "." + str(data['file_suffix'])
                    file_size = os.path.getsize(filepath)
                    # file_size = filesizeformat(file_size)
                    data['file_size'] = file_size
                    data['path'] = os.path.basename(filepath) + "/" + str(data['file_id']) + "." + str(
                        data['file_suffix'])
                    models.TtUploadFileData.objects.create(**data)
                    file_uuid_list.append(data['file_id'])
                res = {
                    'success': True,
                    'info': "上传文件成功",
                    'file_uuid': file_uuid_list
                }

            LoggerHelper.set_end_log_info(SysLog, logger, start, api_path, request.auth.user, request,
                                          function_title)

        except Exception as exp:
            res = LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, api_path,
                                                             request.auth.user, request,
                                                             function_title, None, exp)
        finally:
            return res
