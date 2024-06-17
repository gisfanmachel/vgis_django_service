#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2023/1/4 14:15
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : sysmanUtility.py
# @Descr   : 
# @Software: PyCharm
from my_app.models import SysRole, SysUserRole


class SysmanHelper:
    def __init__(self):
        pass

    # 获取当前登录用户角色
    @staticmethod
    def getRoleOfLoginUser(request):
        user_id = request.auth.user_id
        role_id = SysUserRole.objects.filter(user_id=user_id)[0].role_id
        role_name = SysRole.objects.filter(role_id=role_id)[0].role_name
        return role_name

    # 获取部门层级信息
    @staticmethod
    def getFullDepartName(department_id, connection):
        full_department_name = ""
        department_id, department_name, parent_id = SysmanHelper.getDepartInfo(department_id, connection)
        full_department_name = department_name
        while parent_id != 1:
            department_id = parent_id
            department_id, department_name, parent_id = SysmanHelper.getDepartInfo(department_id, connection)
            full_department_name = department_name + "-" + full_department_name
        return full_department_name

    # 获取部门信息
    @staticmethod
    def getDepartInfo(department_id, connection):
        sql = "select department_id,department_name,parent_id from sys_department where department_id={}".format(
            department_id)
        cursor = connection.cursor()
        cursor.execute(sql)
        records = cursor.fetchone()
        if records is not None:
            return int(records[0]), str(records[1]), int(records[2])
        else:
            return None, None, None

    # 获取同级部门的order_num
    @staticmethod
    def getDepartOrderNum(parent_id, connection):
        sql = "select order_num from sys_department where parent_id={}".format(
            parent_id)
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

    # 获取部门信息
    @staticmethod
    def getDepartByParent(parent_id, connection):
        sql = "select department_id,department_name,parent_id from sys_department where parent_id={}".format(
            parent_id)
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
    def getDepartIdAllLevel(department_id, connection):
        result_department_id_list = []
        result_department_id_list.append(department_id)
        sub_department_id_list = SysmanHelper.getDepartByParent(department_id, connection)
        if len(sub_department_id_list) > 0:
            result_department_id_list = result_department_id_list + sub_department_id_list
            for sub_department_id in sub_department_id_list:
                sub_sub_department_id_list = SysmanHelper.getDepartByParent(sub_department_id, connection)
                if len(sub_sub_department_id_list) > 0:
                    result_department_id_list = result_department_id_list + sub_sub_department_id_list

        return result_department_id_list

    # 获取角色信息
    @staticmethod
    def getRoleByUser(user_id, connection):
        sql = "select tablea.role_id,tableb.role_name from sys_user_role tablea ,sys_role tableb where tablea.role_id=tableb.role_id and tablea.user_id={}".format(
            user_id)
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
    def getMenuByRole(role_id, connection):
        sql = "select menu_id from  sys_role_menu where role_id={}".format(
            role_id)
        cursor = connection.cursor()
        cursor.execute(sql)
        records = cursor.fetchall()
        menu_id_list = []
        for record in records:
            menu_id_list.append(int(record[0]))
        return menu_id_list
