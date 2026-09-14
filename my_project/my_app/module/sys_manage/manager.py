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

from my_app.module.sys_manage.models import SysDepartment, SysLog
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
            sql = "select department_id,department_name,parent_id,state,order_num,create_time,master,tel,email,del_flag from sys_department where 1=1 and del_flag=0"
            params = []
            if department_name is not None and str(department_name).strip() != "":
                sql += " and department_name like %s"
                params.append("%{}%".format(department_name))
            if department_status is not None and str(department_status).strip() != "":
                sql += " and state = %s"
                params.append(department_status)
            sql += " order by create_time desc"
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
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
            # IN 子句按元素个数生成占位符，id 列表逐个参数化
            sql = "update sys_department set del_flag=1 where department_id in ({})".format(
                ','.join(['%s'] * len(department_id_list)))
            cursor = self.connection.cursor()
            cursor.execute(sql, department_id_list)
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
            sql = "select role_id,role_name,remark,create_time from sys_role where 1=1 "
            params = []
            if role_name is not None and str(role_name).strip() != "":
                sql += " and role_name like %s"
                params.append("%{}%".format(role_name))
            sql += " order by create_time desc"
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
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
            sql = "select id,username,operation,method,params,time,ip,create_date from sys_log where 1=1 "
            params = []
            if username is not None and str(username).strip() != "":
                sql += " and username like %s"
                params.append("%{}%".format(username))
            if querystarttime is not None and str(querystarttime).strip() != "":
                sql += " and create_date >= %s"
                params.append(querystarttime)
            if queryendtime is not None and str(queryendtime).strip() != "":
                sql += " and create_date <= %s"
                params.append(queryendtime)
            sql += " order by create_date desc"
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
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
            # 修正：原 SQL 写成 "where 1=1 tablea.dict_catelog_id=tableb.id"，两个条件之间漏了 and
            sql = "select tablea.id,tablea.type_value,tablea.memo_value,tableb.dict_catelog_name "
            sql += "from sys_dict tablea,sys_dict_catelog tableb "
            sql += "where 1=1 and tablea.dict_catelog_id=tableb.id and tablea.dict_catelog_id=%s "
            sql += "order by tablea.id asc"
            cursor = self.connection.cursor()
            cursor.execute(sql, [dict_catelog_id])
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
            # 修正：同 sql_search_dict，原 SQL 漏了 and
            sql = "select tablea.id,tablea.type_value,tablea.memo_value,tableb.dict_catelog_name "
            sql += "from sys_dict tablea,sys_dict_catelog tableb "
            sql += "where 1=1 and tablea.dict_catelog_id=tableb.id and tablea.dict_catelog_id=%s and tablea.id=%s "
            sql += "order by tablea.id asc"
            cursor = self.connection.cursor()
            cursor.execute(sql, [dict_catelog_id, id])
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

    @staticmethod
    def replace_between(text, start_marker, end_marker, replacement="******"):
        """
        把 text 中 start_marker 与 end_marker 之间的内容替换为 replacement。
        用于日志脱敏，例如把登录参数里的密码打码：
            "a=1&password=xx&verifcation=y" -> "a=1&password=******&verifcation=y"

        注意：sys_search_log 一直在调用本方法，但历史上**从未定义**，
        导致日志列表接口一旦遇到 method 含 "login" 的记录就整个查询失败。
        这里补上实现。任一标记找不到时原样返回，不抛异常。
        """
        if not text:
            return text
        start = text.find(start_marker)
        if start == -1:
            return text
        start += len(start_marker)
        end = text.find(end_marker, start)
        if end == -1:
            return text
        return text[:start] + replacement + text[end:]

    def get_max_id(self, tablename):
        sql = "select max(id) from {}".format(tablename)
        cursor = self.connection.cursor()
        cursor.execute(sql)
        record = cursor.fetchone()
        # 注意：空表时 max(id) 返回的是 (None,) 而不是 None，
        # 只判断 record is not None 会对 None 调 int() 直接抛 TypeError，
        # 导致「表为空时新增第一条数据必失败」。
        if record is None or record[0] is None:
            return 0
        return int(record[0])

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
            # 先判断是否有重复（参数化，避免值里含单引号时 SQL 崩、也防注入）
            cursor.execute("select count(*) from sys_dict where dict_catelog_id = %s and type_value = %s",
                           [dict_catelog_id, type_value])
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
                # 修正：原语句列了 4 个字段却只给了 3 个值，必然报错
                cursor.execute(
                    "insert into sys_dict (id,dict_catelog_id,type_value,memo_value) values (%s,%s,%s,%s)",
                    [self.get_max_id("sys_dict") + 1, dict_catelog_id, type_value, memo_value])

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
            # 先判断是否有重复（参数化）
            cursor.execute(
                "select count(*) from sys_dict where dict_catelog_id = %s and type_value = %s and id != %s",
                [dict_catelog_id, type_value, id])
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
                cursor.execute(
                    "update sys_dict set type_value=%s,memo_value=%s where id=%s",
                    [type_value, memo_value, id])
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
            cursor.execute("delete from sys_dict where id = %s", [id])
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
            # 修正：原 SQL 里时间条件写的是 tableb.create_time，但 FROM 里只有
            # tablea(sys_message) 和 tablec(auth_user)，根本没有 tableb 别名，SQL 必然报错；
            # 应为 tablea.create_time（sys_message 的创建时间）。
            # 同时值全部改为 %s 参数化。
            sql = '''
                select
                    tablea.message,tablea.create_time,tablea.id,tablec.username,tablec.fullname
                from
                    sys_message tablea,
                    auth_user tablec
                where
                    1=1
                    and tablea.user_id=tablec.id
                    and tablec.username like %s
                    and tablea.create_time >= %s
                    and tablea.create_time <= %s
                order by tablec.username
            '''
            cursor = self.connection.cursor()
            cursor.execute(sql, ["%{}%".format(username), querystarttime, queryendtime])
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
            cursor.execute("delete from sys_message where id = %s", [id])
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
