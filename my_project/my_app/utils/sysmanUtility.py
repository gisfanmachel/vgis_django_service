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
from collections import defaultdict

from django.core.cache import cache

from my_app.models import SysParam, TtRetrivepassToken, AuthUser, SysRole, SysUserRole
from my_app.utils.commonUtility import CommonHelper
from my_app.utils.passwordUtility import PasswordHelper
from my_app.utils.snowflake_id_util import SnowflakeIDUtil


class SysmanHelper:
    def __init__(self):
        pass

    # ---------------- 缓存层（阶段 4） ----------------
    # SysParam 读多写少、读路径遍布 auth/middleware/list 接口，
    # 缓存 5 分钟既能消除每请求 3-5 次查表，又能在管理员改值后及时生效。
    # 注意：cast 默认 str，是为了让"是"/"否"这种中文 bool 仍能被原样读出；
    # 数字类配置（如 AUTH_TOKEN_AGE）必须显式传 cast=int。
    @staticmethod
    def get_param_cached(en_key, default=None, cast=str):
        cache_key = f'sys_param:{en_key}'
        v = cache.get(cache_key)
        if v is not None:
            return cast(v)
        try:
            obj = SysParam.objects.get(param_en_key=en_key)
            cache.set(cache_key, obj.param_value, 300)  # 5 min
            return cast(obj.param_value)
        except SysParam.DoesNotExist:
            return cast(default) if default is not None else None

    # ---------------- N+1 批量版 helper（阶段 2） ----------------
    # 旧版单点函数（getDepartInfo/getRoleByUser/getMenuByRole）在列表里被循环调用，
    # N 行数据触发 N 次 SQL；这里改成单条 ANY(%s) 数组参数 + Python 端内存拼装。

    @staticmethod
    def getFullDepartNameBulk(department_ids, connection,
                              sys_department_table="sys_department"):
        """单条 SQL 拿全部门，Python 内存递归拼父链"""
        if not department_ids:
            return {}
        with connection.cursor() as cur:
            cur.execute(
                "SELECT department_id, department_name, parent_id FROM {} "
                "WHERE department_id = ANY(%s)".format(sys_department_table),
                [list(department_ids)])
            rows = cur.fetchall()
        id2info = {r[0]: (r[1], r[2]) for r in rows}
        result = {}
        for did in department_ids:
            names = []
            cur_id = did
            while cur_id and cur_id != 1:
                info = id2info.get(cur_id)
                if not info:
                    break
                names.append(info[0])
                cur_id = info[1]
            result[did] = '/'.join(reversed(names))
        return result

    @staticmethod
    def getRoleByUserBulk(user_ids, connection,
                          sys_user_role_table="sys_user_role", sys_role_table="sys_role"):
        """单条 SQL 拿所有用户的角色"""
        out = {}
        if not user_ids:
            return out
        with connection.cursor() as cur:
            cur.execute("""
                SELECT ur.user_id, r.role_id, r.role_name
                FROM {0} ur
                JOIN {1} r ON ur.role_id = r.role_id
                WHERE ur.user_id = ANY(%s)
            """.format(sys_user_role_table, sys_role_table), [list(user_ids)])
            rows = cur.fetchall()
        bucket = defaultdict(lambda: ([], []))
        for uid, rid, rname in rows:
            bucket[uid][0].append(int(rid))
            bucket[uid][1].append(str(rname))
        return {uid: (rid_list, rname_list) for uid, (rid_list, rname_list) in bucket.items()}

    @staticmethod
    def getDepartInfoBulk(dept_ids, connection,
                          sys_department_table="sys_department"):
        """批量拿部门名（不含父链）；供 sql_search_department 等只需展示部门名的场景"""
        if not dept_ids:
            return {}
        with connection.cursor() as cur:
            cur.execute(
                "SELECT department_id, department_name FROM {} "
                "WHERE department_id = ANY(%s)".format(sys_department_table),
                [list(dept_ids)])
            return {r[0]: r[1] for r in cur.fetchall()}

    @staticmethod
    def getMenuByRoleBulk(role_ids, connection,
                          sys_role_menu_table="sys_role_menu",
                          sys_menu_table="sys_menu"):
        """批量拿每个角色关联的菜单 {menu_id, name}"""
        out = {}
        if not role_ids:
            return out
        with connection.cursor() as cur:
            cur.execute("""
                SELECT rm.role_id, m.menu_id, m.name
                FROM {0} rm
                JOIN {1} m ON rm.menu_id = m.menu_id
                WHERE rm.role_id = ANY(%s)
            """.format(sys_role_menu_table, sys_menu_table), [list(role_ids)])
            bucket = defaultdict(list)
            for rid, mid, mname in cur.fetchall():
                bucket[rid].append({'menu_id': mid, 'name': mname})
        return dict(bucket)

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
    # 说明：表名是 SQL 标识符，无法用占位符，只能用 format 拼（取值来自内部常量，非用户输入）；
    #       值一律走 %s 参数化。
    @staticmethod
    def getDepartInfo(department_id, connection, sys_department_table="sys_department"):
        sql = "select department_id,department_name,parent_id from {} where department_id=%s".format(
            sys_department_table)
        cursor = connection.cursor()
        cursor.execute(sql, [department_id])
        records = cursor.fetchone()
        if records is not None:
            return int(records[0]), str(records[1]), int(records[2])
        else:
            return None, None, None

    # 获取同级部门的order_num
    @staticmethod
    def getDepartOrderNum(parent_id, connection, sys_department_table="sys_department"):
        sql = "select order_num from {} where parent_id=%s".format(sys_department_table)
        cursor = connection.cursor()
        cursor.execute(sql, [parent_id])
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
        sql = "select department_id,department_name,parent_id from {} where parent_id=%s".format(
            sys_department_table)
        cursor = connection.cursor()
        cursor.execute(sql, [parent_id])
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
        sql = "select tablea.role_id,tableb.role_name from {} tablea ,{} tableb " \
              "where tablea.role_id=tableb.role_id and tablea.user_id=%s".format(
                  sys_user_role_table, sys_role_table)
        cursor = connection.cursor()
        cursor.execute(sql, [user_id])
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
        sql = "select menu_id from {} where role_id=%s".format(sys_role_menu_table)
        cursor = connection.cursor()
        cursor.execute(sql, [role_id])
        records = cursor.fetchall()
        menu_id_list = []
        for record in records:
            menu_id_list.append(int(record[0]))
        return menu_id_list

    # 获取同级菜单的order_num
    @staticmethod
    def getMenuOrderNum(parent_id, connection, sys_menu_table="sys_menu"):
        sql = "select sum(order_num) from {} where parent_id=%s".format(sys_menu_table)
        cursor = connection.cursor()
        cursor.execute(sql, [parent_id])
        record = cursor.fetchone()
        if record is None or record[0] is None:
            max_num = -1
        else:
            sql = "select max(order_num) from {} where parent_id=%s".format(sys_menu_table)
            cursor.execute(sql, [parent_id])
            record = cursor.fetchone()
            max_num = record[0] if record is not None else -1
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
