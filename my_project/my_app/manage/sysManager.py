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
