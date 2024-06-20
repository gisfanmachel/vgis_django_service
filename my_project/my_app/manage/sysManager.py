#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/12/15 20:08
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : sysManager.py
# @Descr   : 系统管理
# @Software: PyCharm
import datetime
import logging
import time

from loguru import logger
from vgis_log.logTools import LoggerHelper
from vgis_utils.vgis_http.httpTools import HttpHelper
from vgis_utils.vgis_list.listTools import ListHelper

from my_app.models import SysDepartment
from my_app.models import SysLog
from my_app.utils.sysmanUtility import SysmanHelper

logger = logging.getLogger('django')


class SysOperator:
    def __init__(self, connection):
        self.connection = connection

    # 获取部门列表-sql
    def sql_search_department(self, request, department_name, department_status):
        title = "获取部门列表数据"
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            # 获取部门列表信息
            sql = "select department_id,department_name,parent_id,state,order_num,create_time,master,tel,email,del_flag from sys_department  where 1=1 and del_flag =0"
            if department_name is not None and str(department_name).strip() != "":
                sql += " and department_name like '%{}%'".format(department_name)
            if department_status is not None and str(department_status).strip() != "":
                sql += " and state ='{}'".format(department_status)
            sql += " order by create_time desc"
            cursor = self.connection.cursor()
            cursor.execute(sql)
            records = cursor.fetchall()
            data_list = []
            for record in records:
                obj = {}
                obj['department_id'] = int(record[0])
                obj['department_name'] = str(record[1])
                obj['parent_id'] = int(record[2])
                department_id, department_name, parent_id = SysmanHelper.getDepartInfo(obj['parent_id'],
                                                                                       self.connection)
                obj['parent_name'] = department_name
                obj['state'] = "正常" if int(record[3]) == 1 else "停用"
                obj['order_num'] = int(record[4])
                obj['create_time'] = str(record[5])
                obj['master'] = str(record[6])
                obj['tel'] = str(record[7])
                obj['email'] = str(record[8])
                obj['del_flag'] = str(record[9])
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
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title, "/api/sysDepartment/sqlsearch",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", "/api/sysDepartment/sqlsearch",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 设置部门状态
    def set_department_status(self, request):
        department_id = request.data["department_id"]
        department_status = request.data["department_status"]
        title = "设置部门状态"
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            SysDepartment.objects.filter(department_id=department_id).update(state=department_status)
            res = {
                'success': True,
                'info': "{}成功".format(title)
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title, "/api/sysDepartment/departstatus",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", "/api/sysDepartment/departstatus",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 逻辑删除部门及下属部门
    def delete_department(self, request):
        department_id = request.data["department_id"]
        title = "逻辑删除部门数据"
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            # 获取当前部门的所有下级部门，暂时支持三级部门
            department_id_list = SysmanHelper.getDepartIdAllLevel(department_id, self.connection)
            sql = "update sys_department  set del_flag=1 where department_id in ({})".format(
                ListHelper.get_number_str_by_list(department_id_list))
            cursor = self.connection.cursor()
            cursor.execute(sql)
            self.connection.commit()
            res = {
                'success': True,
                'info': "删除成功，包括本级及下级部门：{}".format(ListHelper.get_number_str_by_list(department_id_list))
            }

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title, "/api/sysDepartment/delete/",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", "/api/sysDepartment/delete/",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 获取角色列表-sql
    def sql_search_role(self, request, role_name):
        title = "获取角色列表数据"
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            # 获取角色列表信息
            sql = "select role_id,role_name,remark,create_time from sys_role  where 1=1 "
            if role_name is not None and str(role_name).strip() != "":
                sql += " and role_name like '%{}%'".format(role_name)
            sql += " order by create_time desc"
            cursor = self.connection.cursor()
            cursor.execute(sql)
            records = cursor.fetchall()
            data_list = []
            for record in records:
                obj = {}
                obj['role_id'] = int(record[0])
                obj['role_name'] = str(record[1])
                obj['menu_id_list'] = SysmanHelper.getMenuByRole(int(record[0]), self.connection)
                obj['remark'] = str(record[2])
                obj['create_time'] = str(record[3])
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
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title, "/api/sysRole/sqlsearch",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", "/api/sysRole/sqlsearch",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 获取日志列表-sql
    def sql_search_log(self, request, username, querystarttime, queryendtime):
        title = "获取日志列表数据"
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            # 获取角色列表信息
            sql = "select id,username,operation,method,params,time,ip,create_date from sys_log  where 1=1 "
            if username is not None and str(username).strip() != "":
                sql += " and username like '%{}%'".format(username)
            if querystarttime is not None and str(querystarttime).strip() != "":
                sql += " and create_date >= '{}'".format(querystarttime)
            if queryendtime is not None and str(queryendtime).strip() != "":
                sql += " and create_date <= '{}'".format(queryendtime)
            sql += " order by create_date desc"
            cursor = self.connection.cursor()
            cursor.execute(sql)
            records = cursor.fetchall()
            data_list = []
            for record in records:
                obj = {}
                obj['log_id'] = int(record[0])
                obj['username'] = str(record[1])
                obj['operation'] = str(record[2])
                obj['method'] = str(record[3])
                obj['params'] = str(record[4])
                # 如果是登录接口，对密码进行脱敏处理
                if "login" in obj['method']:
                    obj['params'] = self.replace_between(obj['params'], '&password=', '&verifcation=', '******')
                obj['time'] = int(record[5]) if record[5] is not None and str(record[5]).strip() != "" else None
                obj['ip'] = str(record[6])
                obj['create_date'] = str(record[7])
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
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title, "/api/sysLog/sqlsearch",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", "/api/sysLog/sqlsearch",
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 获取数据字典类别数据

    def get_dict_catelog_list(self, request, title):
        # title = "获取数据字典类别数据"
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        res = ""
        try:

            # 获取归属于这个字典类别下的字典信息
            sql = "select id,dict_catelog_name from sys_dict_catelog"
            sql += " order by id asc"
            cursor = self.connection.cursor()
            cursor.execute(sql)
            records = cursor.fetchall()
            data_list = []
            for record in records:
                obj = {}
                obj['dict_catelog_id'] = int(record[0])
                obj['dict_catelog_name'] = str(record[1]) if record[1] is not None else ""
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
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title, request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 获取数据字典列表-sql
    def sql_search_dict(self, request, dict_catelog_id, title):
        # title = "获取数据字典列表数据"
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            # 获取归属于这个字典类别下的字典信息
            sql = "select tablea.id,tablea.type_value,tablea.memo_value,tableb.dict_catelog_name from sys_dict tablea,sys_dict_catelog tableb  where 1=1 tablea.dict_catelog_id=tableb.id and tablea.dict_catelog_id={}".format(
                dict_catelog_id)
            sql += " order by id asc"
            cursor = self.connection.cursor()
            cursor.execute(sql)
            records = cursor.fetchall()
            data_list = []
            for record in records:
                obj = {}
                obj['id'] = int(record[0])
                obj['type_value'] = str(record[1])
                obj['memo_value'] = str(record[2]) if record[2] is not None else ""
                obj['dict_catelog_name'] = str(record[3]) if record[3] is not None else ""
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
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title, request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 通过编号获取数据字典详情
    def get_detail_by_condition(self, request, dict_catelog_id, id, title):
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:

            # 获取归属于这个字典类别下的字典信息
            sql = "select tablea.id,tablea.type_value,tablea.memo_value,tableb.dict_catelog_name from sys_dict tablea,sys_dict_catelog tableb  where 1=1 tablea.dict_catelog_id=tableb.id and tablea.dict_catelog_id={} and tablea.id={}".format(
                dict_catelog_id, id)
            sql += " order by id asc"
            cursor = self.connection.cursor()
            cursor.execute(sql)
            records = cursor.fetchall()
            data_list = []
            for record in records:
                obj = {}
                obj['dict_catelog_id'] = dict_catelog_id
                obj['dict_catelog_name'] = str(record[3]) if record[3] is not None else ""
                obj['id'] = int(record[0])
                obj['type_value'] = str(record[1])
                obj['memo_value'] = str(record[2]) if record[2] is not None else ""

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
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title, request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    def get_max_id(self, tablename):
        sql = "select max(id) from {}".format(tablename)
        cursor = self.connection.cursor()
        cursor.execute(sql)
        record = cursor.fetchone()
        return int(record[0]) if record is not None else 0

    # 添加数据字典
    def add_dict(self, request, title):
        # title = "获取数据字典"
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            dict_catelog_id = request.data.get("dict_catelog_id")
            type_value = request.data.get("type_value")
            memo_value = request.data.get("memo_value")
            cursor = self.connection.cursor()
            # 先判断是否有重复
            sql = "select count(*) from sys_dict where dict_catelog_id ={} and type_value='{}'".format(dict_catelog_id,
                                                                                                       type_value)
            cursor.execute(sql)
            record = cursor.fetchone()
            if record[0] > 0:
                res = {
                    'success': False,
                    'info': "添加数据字典失败，该字典类别下已存在该字典信息"
                }
                logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                end = time.perf_counter()
                t = end - start
                logger.info("总共用时{}秒".format(t))
                LoggerHelper.insert_log_info(SysLog, request.auth.user, res['info'], request.path,
                                             HttpHelper.get_params_request(request),
                                             t, HttpHelper.get_ip_request(request))
            else:
                sql = "insert into sys_dict (id,dict_catelog_id,type_value,memo_value) values ({},'{}','{}') ".format(
                    self.get_max_id("sys_dict") + 1, dict_catelog_id,
                    type_value, memo_value
                )

                cursor.execute(sql)
                self.connection.commit()
                res = {
                    'success': True,
                    'info': "添加数据字典成功"
                }
                logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                end = time.perf_counter()
                t = end - start
                logger.info("总共用时{}秒".format(t))
                # 日志入库
                LoggerHelper.insert_log_info(SysLog, request.auth.user, title, request.path,
                                             HttpHelper.get_params_request(request),
                                             t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 编辑数据字典
    def update_dict(self, request, title):
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            dict_catelog_id = request.data.get("dict_catelog_id")
            id = request.data.get("id")
            type_value = request.data.get("type_value")
            memo_value = request.data.get("memo_value")
            cursor = self.connection.cursor()
            # 先判断是否有重复
            sql = "select count(*) from sys_dict where dict_catelog_id ={} and type_value='{}' and id!={}".format(
                dict_catelog_id,
                type_value, id)
            cursor.execute(sql)
            record = cursor.fetchone()
            if record[0] > 0:
                res = {
                    'success': False,
                    'info': "更新数据字典失败，该字典类别下已存在该字典信息"
                }
                logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                end = time.perf_counter()
                t = end - start
                logger.info("总共用时{}秒".format(t))
                LoggerHelper.insert_log_info(SysLog, request.auth.user, res['info'], request.path,
                                             HttpHelper.get_params_request(request),
                                             t, HttpHelper.get_ip_request(request))
            else:
                sql = "update  sys_dict set type_value='{}',memo_value='{}' where id={} ".format(
                    type_value,
                    memo_value, id
                )

                cursor.execute(sql)
                self.connection.commit()
                res = {
                    'success': True,
                    'info': "更新数据字典成功"
                }
                logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                end = time.perf_counter()
                t = end - start
                logger.info("总共用时{}秒".format(t))
                # 日志入库
                LoggerHelper.insert_log_info(SysLog, request.auth.user, title, request.path,
                                             HttpHelper.get_params_request(request),
                                             t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 删除数据字典
    def delete_dict(self, request, title):
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            dict_catelog_id = request.data.get("dict_catelog_id")
            id = request.data.get("id")
            cursor = self.connection.cursor()
            sql = "delete from  sys_dict where id = {} ".format(
                id
            )
            cursor.execute(sql)
            self.connection.commit()
            res = {
                'success': True,
                'info': "{}成功".format(title)
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title, request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 获取消息列表-sql
    def sql_search_message(self, request, username, querystarttime, queryendtime, title):
        res = ""
        start = time.perf_counter()
        if querystarttime == "":
            querystarttime = "2024-01-01 00:00:00"
        if queryendtime == "":
            queryendtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            sql = '''
                select
                    tablea.message,tablea.create_time,tablea.id,tablec.username,tablec.fullname
                from
                    sys_message tablea
                    auth_user tablec
                where
                    1=1
                    and tablea.user_id=tablec.id
                    and tablec.username like '%{}%'
                    and tableb.create_time>='{}'
	                and tableb.create_time<='{}'
                    order by tablec.username
            '''.format(username, querystarttime, queryendtime)
            cursor = self.connection.cursor()
            cursor.execute(sql)
            records = cursor.fetchall()
            data_list = []
            for record in records:
                obj = {}
                obj['id'] = int(record[2])
                obj['message'] = str(record[0])
                obj['time'] = str(record[1])
                obj['usernam'] = str(record[3])
                obj['fullname'] = str(record[4]) if record[4] is not None else ""
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
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title, request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res

    # 删除用户消息
    def delete_message(self, request, title):
        res = ""
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            id = request.data.get("id")
            cursor = self.connection.cursor()
            sql = "delete from  sys_message where id = {}".format(
                id
            )
            cursor.execute(sql)
            self.connection.commit()
            res = {
                'success': True,
                'info': "{}成功".format(title)
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title, request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        except Exception as exp:
            logger.error("{}失败：{}".format(title, str(exp)))
            logger.error(exp)
            logger.error(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
            logger.error(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
            res = {
                'success': False,
                'info': "{}失败：{}".format(title, str(exp))
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            # 日志入库
            LoggerHelper.insert_log_info(SysLog, request.auth.user, title + "失败", request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
        finally:
            return res
