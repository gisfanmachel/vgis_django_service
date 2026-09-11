#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2023/1/4 14:15
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : sysmanUtility.py
# @Descr   : 系统管理相关帮助类
# @Software: PyCharm
import datetime
import uuid

from my_app.models import TtRetrivepassToken, AuthUser, SysRole, SysUserRole
from my_app.utils.commonUtility import CommonHelper
from my_app.utils.passwordUtility import PasswordHelper
from my_app.utils.snowflake_id_util import SnowflakeIDUtil


class SysmanHelper:
    def __init__(self):
        pass

    # 获取当前登录用户角色
    @staticmethod
    def getRoleOfLoginUser(request, user_scope=None):
        user_id = request.auth.user_id
        role_id = SysUserRole.objects.filter(user_id=user_id)[0].role_id
        role_name = SysRole.objects.filter(role_id=role_id)[0].role_name
        return role_name

    # 获取部门层级信息
    @staticmethod
    def getFullDepartName(department_id, connection, sys_department_table="sys_department"):
        full_department_name = ""
        department_id, department_name, parent_id = SysmanHelper.getDepartInfo(department_id, connection,
                                                                              sys_department_table)
        full_department_name = department_name
        while parent_id != 1:
            department_id = parent_id
            department_id, department_name, parent_id = SysmanHelper.getDepartInfo(department_id, connection,
                                                                                   sys_department_table)
            full_department_name = department_name + "-" + full_department_name
        return full_department_name

    # 获取部门信息
    @staticmethod
    def getDepartInfo(department_id, connection, sys_department_table="sys_department"):
        sql = "select department_id,department_name,parent_id from {} where department_id={}".format(
            sys_department_table, department_id)
        cursor = connection.cursor()
        cursor.execute(sql)
        records = cursor.fetchone()
        if records is not None:
            return int(records[0]), str(records[1]), int(records[2])
        else:
            return None, None, None

    # 获取同级部门的order_num
    @staticmethod
    def getDepartOrderNum(parent_id, connection, sys_department_table="sys_department"):
        sql = "select order_num from {} where parent_id={}".format(
            sys_department_table, parent_id)
        cursor = connection.cursor()
        cursor.execute(sql)
        records = cursor.fetchall()
        if records is None:
            max_num = -1
        else:
            max_num = records[0][0]
        for record in records:
            if record[0] > max_num:
                max_num = record[0]
        return max_num

    # 获取下级部门信息
    @staticmethod
    def getDepartByParent(parent_id, connection, sys_department_table="sys_department"):
        sql = "select department_id,department_name,parent_id from {} where parent_id={}".format(
            sys_department_table, parent_id)
        cursor = connection.cursor()
        cursor.execute(sql)
        records = cursor.fetchall()
        department_id_list = []
        if records is not None:
            for record in records:
                department_id_list.append(int(record[0]))
        return department_id_list

    # 获取部门及下级部门的department_id
    # 暂时支持三级部门
    @staticmethod
    def getDepartIdAllLevel(department_id, connection, sys_department_table="sys_department"):
        result_department_id_list = []
        result_department_id_list.append(department_id)
        sub_department_id_list = SysmanHelper.getDepartByParent(department_id, connection, sys_department_table)
        if len(sub_department_id_list) > 0:
            result_department_id_list = result_department_id_list + sub_department_id_list
            for sub_department_id in sub_department_id_list:
                sub_sub_department_id_list = SysmanHelper.getDepartByParent(sub_department_id, connection,
                                                                            sys_department_table)
                if len(sub_sub_department_id_list) > 0:
                    result_department_id_list = result_department_id_list + sub_sub_department_id_list

        return result_department_id_list

    # 获取角色信息
    @staticmethod
    def getRoleByUser(user_id, connection, user_scope=None,
                      sys_user_role_table="sys_user_role", sys_role_table="sys_role"):
        sql = "select tablea.role_id,tableb.role_name from {} tablea ,{} tableb where tablea.role_id=tableb.role_id and tablea.user_id={}".format(
            sys_user_role_table, sys_role_table, user_id)
        cursor = connection.cursor()
        cursor.execute(sql)
        records = cursor.fetchall()
        role_id_list = []
        role_name_list = []
        for record in records:
            role_id_list.append(int(record[0]))
            role_name_list.append(str(record[1]))
        return role_id_list, role_name_list

    # 获取菜单信息
    @staticmethod
    def getMenuByRole(role_id, connection, sys_role_menu_table="sys_role_menu"):
        sql = "select menu_id from  {} where role_id={}".format(
            sys_role_menu_table, role_id)
        cursor = connection.cursor()
        cursor.execute(sql)
        records = cursor.fetchall()
        menu_id_list = []
        for record in records:
            menu_id_list.append(int(record[0]))
        return menu_id_list

    # 获取同级菜单的order_num
    @staticmethod
    def getMenuOrderNum(parent_id, connection, sys_menu_table="sys_menu"):
        sql = "select sum(order_num) from {} where parent_id={}".format(sys_menu_table,
                                                                        parent_id)
        cursor = connection.cursor()
        cursor.execute(sql)
        record = cursor.fetchone()
        if record[0] is None:
            max_num = -1
        else:
            sql = "select max(order_num) from {} where parent_id={}".format(sys_menu_table, parent_id)
            cursor.execute(sql)
            record = cursor.fetchone()
            max_num = record[0]
        return max_num

    # ---------------- 密码找回 ----------------
    # 密保问题验证，通过后下发一次性 userkey
    # 依赖 auth_user 表字段：userpass_question / userpass_answer，以及 tt_retrivepass_token 表
    @staticmethod
    def retrieve_password(username, userpass_question, userpass_answer, connection, local="CH"):
        res = {}
        # 参数化查询，避免用户名里带引号造成的SQL注入/语法错误
        sql = "select userpass_question,userpass_answer,id from auth_user where username=%s"
        cursor = connection.cursor()
        cursor.execute(sql, [username])
        record = cursor.fetchone()
        if record is not None:
            userpass_question_db, userpass_answer_db, userid = record[0], record[1], record[2]
            if userpass_question == userpass_question_db and userpass_answer == userpass_answer_db:
                # 设置找回密码的token
                key = str(uuid.uuid4())
                my_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                TtRetrivepassToken.objects.create(id=SnowflakeIDUtil.snowflakeId(), key=key, user_id=userid,
                                                  create_time=my_time)

                res = {
                    'success': True,
                    'info': CommonHelper.get_local_str2("RETRIEVE_PASSWORD_SUCCESS", local),
                    'userid': userid,
                    'userkey': key
                }
            else:
                res = {
                    'success': False,
                    'info': CommonHelper.get_local_str2("SECURITY_QUESTION_OR_ANSWER_WRONG", local)
                }
        else:
            res = {
                'success': False,
                'info': CommonHelper.get_local_str2("USERNAME_NOT_EXIST", local)
            }
        return res

    # 用一次性 userkey 重置密码
    @staticmethod
    def reset_password(userid, userkey, userpass, connection, local="CH"):
        res = {}
        sql = "select key from tt_retrivepass_token where user_id=%s order by create_time desc"
        cursor = connection.cursor()
        cursor.execute(sql, [userid])
        record = cursor.fetchone()
        if record is not None and str(record[0]) == str(userkey):
            encrpt_pass = PasswordHelper.getEncrptPassword(userpass)
            AuthUser.objects.filter(id=userid).update(password=encrpt_pass)
            # 删除找回密码的token（一次性）
            TtRetrivepassToken.objects.filter(user_id=userid).delete()
            res = {
                'success': True,
                'info': CommonHelper.get_local_str2("RESET_PASSWORD_SUCCESS", local)
            }
        else:
            res = {
                'success': False,
                'info': CommonHelper.get_local_str2("RESET_PASSWORD_FAIL", local)
            }
        return res
