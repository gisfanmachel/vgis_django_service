#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    : 2022/5/7 10:01
# @Author  : gisfan_ai
# @Email   : gisfanmachel@gmail.com
# @File    : userManager.py
# @Desc    ：置信度系统的业务处理类
# @Software: PyCharm

import datetime
import io
import logging
import random
from datetime import timedelta

from PIL import Image, ImageDraw, ImageFont
from django.db.models import F
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.utils import timezone
from loguru import logger
from vgis_log.logTools import LoggerHelper
from vgis_utils.vgis_datetime.datetimeTools import DateTimeHelper

# 用户相关操作类
from my_app.apps import MyAppConfig
from my_app.models import SysLog, SysParam
from my_app.module.user_manage.models import AuthUser
from my_app.utils.commonUtility import CommonHelper
from my_app.utils.sysmanUtility import SysmanHelper
from my_project import settings
from my_project.settings import IS_USE_VERIFICATION_CODE

logger = logging.getLogger('django')


class UserOperator:
    def __init__(self, connection):
        self.connection = connection


    def get_LOGIN_LOCKED_TIME(self):
        # 阶段 4：5 分钟缓存；默认值 600 秒（10 分钟）
        return SysmanHelper.get_param_cached('LOGIN_LOCKED_TIME', 600, cast=int)

    def get_LOGIN_ERROR_ATTEMPTS(self):
        # 阶段 4：5 分钟缓存；默认值 4 次
        return SysmanHelper.get_param_cached('LOGIN_ERROR_ATTEMPTS', 4, cast=int)

    def return_is_use_verification_code(self,request):
        res = {
            'success': True,
            'code': 1,
            'value': self.get_is_use_verification_code()
        }
        return res



    def get_is_use_verification_code(self):
        # 阶段 4：5 分钟缓存；"是" 才开
        v = SysmanHelper.get_param_cached('IS_USE_VERIFICATION_CODE', '否')
        return True if v == "是" else False
    # 登录
    # 通过用户名和密码登录
    # 连续输错4次密码，锁定10分钟，10分钟后没输错一次密码都重新锁定10分钟---参数可配置
    def login(self, request, username, password, verifcation, auth, Token, force=False):
        """
        :param force: False（默认）时，若该账号已有未过期的 token，拒绝登录并返回"已在别处登录"；
                      True 时跳过该检查，直接顶掉对方的登录态（供 loginWithForce 使用）。
        """
        function_title = "用户登录"
        try:
            start = LoggerHelper.set_start_log_info(logger)
            # 修正 P0 bug：原先"exists 判断"+"get 取对象"两次往返，
            # 改成单条 .first() 同时承担"是否存在"与"取对象"两个职责，少一次 SQL。
            userObject = AuthUser.objects.filter(username=username).first()
            if userObject is None:
                error_message = "账号名不存在，请联系管理员。"
                res = {
                    'success': False,
                    'code': -1,
                    'message': error_message
                }
                return res
            # 账号被锁
            if userObject.login_locked_until and userObject.login_locked_until > timezone.now():
                # 账号被锁定
                remaining_time = (userObject.login_locked_until - timezone.now()).total_seconds()
                error_message = "账号已被锁定，请在{}后重试。".format(DateTimeHelper.convert_seconds(remaining_time))
                res = {
                    'success': False,
                    'code': -1,
                    'message': error_message
                }
                return res
            # 账号没有被锁
            else:
                user = auth.authenticate(username=username, password=password)
                # 登录失败
                if not user:
                    # 登录失败，增加失败次数（原子自增，避免两个并发请求读到相同旧值后各自 save 互相覆盖）
                    AuthUser.objects.filter(username=username).update(
                        login_error_attempts=Coalesce(F('login_error_attempts'), 0) + 1
                    )
                    # 原子自增后再读一次最新值，用于判定是否要锁
                    userObject.refresh_from_db(fields=['login_error_attempts'])
                    if (userObject.login_error_attempts or 0) >= self.get_LOGIN_ERROR_ATTEMPTS():
                        AuthUser.objects.filter(username=username).update(
                            login_locked_until=timezone.now() + timedelta(seconds=self.get_LOGIN_LOCKED_TIME())
                        )
                    res = {
                        'success': False,
                        'code': -1,
                        'message': '用户名或密码不对!'
                    }
                    return res
                else:
                    # 验证码
                    # 验证码
                    if self.get_is_use_verification_code():
                        try:
                            if verifcation != request.session['code']:
                                res = {
                                    'success': False,
                                    'code': -1,
                                    'message': '验证码不对!'
                                }
                                return res
                        except:
                            res = {
                                'success': False,
                                'code': -1,
                                'message': '验证码匹配有问题!'
                            }
                            return res
                    # 登录成功，重置失败次数并解锁账号
                    userObject.login_error_attempts = 0
                    userObject.login_locked_until = None
                    userObject.save()
            # 判断登录成功的用户是否为有效用户
            if user.is_active:
                # 「已在别处登录」的检查放在密码校验通过之后：
                # 原实现把这一步放在 userViews 里、且早于密码校验，导致一个已登录的账号
                # 即使密码输错也返回"用户已在别处登录"，既掩盖了密码错误、又泄露了账号存在性。
                if not force:
                    existing_token = Token.objects.filter(user=user).first()
                    if existing_token is not None and not self._check_token_expired(existing_token):
                        # 注意：本方法外层是 try/finally，finally 里那句 return res 会覆盖 try 内的 return，
                        # 所以这里必须先把结果赋给 res 再返回，直接 return 字面量会导致
                        # finally 里访问未赋值的 res 而抛 UnboundLocalError。
                        res = {
                            'success': False,
                            'code': -2,
                            'message': '用户已在别处登录!'
                        }
                        return res
                auth.login(request, user)
                # 删除原有的Token
                old_token = Token.objects.filter(user=user)
                old_token.delete()
                # 创建新的Token
                token = Token.objects.create(user=user)
                res = {
                    'success': True,
                    'code': 0,
                    'info': "{}成功！".format(function_title),
                    "userid": user.id,
                    "username": user.username,
                    "token": token.key
                }
            else:
                res = {
                    'success': False,
                    'code': -1,
                    'message': '用户被禁用！',
                    "userid": user.id,
                    "username": user.username
                }
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, username, request, function_title)
        except Exception as exp:
            res = LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path, username,
                                                             request,
                                                             function_title, None, exp)
        finally:
            return res

    # 获取用户详情（姓名/部门/角色/菜单）
    # 返回 (user_info, res)，user_info 为 None 表示查询失败
    def get_user_info(self, request, start, function_title, user_id, user_name):
        sys_department_table = "sys_department"
        sys_user_role_table = "sys_user_role"
        sys_role_table = "sys_role"
        sys_menu_table = "sys_menu"
        sys_role_menu_table = "sys_role_menu"
        logClass = SysLog
        user_info = None
        res = ""
        try:
            user_info = {}
            # 获取获取用户姓名，部门（表名是标识符用 format，值走 %s 参数化）
            sql = "select tablea.username,tablea.fullname,tablea.department_id,tableb.department_name from auth_user tablea "
            sql += " left join {} tableb on tablea.department_id=tableb.department_id".format(sys_department_table)
            sql += " where tablea.id=%s"
            cursor = self.connection.cursor()
            cursor.execute(sql, [user_id])
            record = cursor.fetchone()
            if record is not None:
                user_info["userid"] = user_id
                user_info["username"] = record[0]
                user_info["fullname"] = record[1]
                user_info["department_id"] = record[2]
                user_info["department_name"] = record[3]

            # --获取用户的角色（多个）
            sql = "select distinct tablec.role_name, tablec.role_id from {} tablec ".format(sys_role_table)
            sql += " left join  {} tabled on tablec.role_id = tabled.role_id".format(sys_user_role_table)
            sql += " where tabled.user_id =%s"
            cursor.execute(sql, [user_id])
            records = cursor.fetchall()
            role_list = []
            role_ids = []
            for record in records:
                role_info = {}
                role_info["role_name"] = record[0]
                role_info["role_id"] = record[1]
                role_list.append(role_info)
                role_ids.append(int(record[1]))
            user_info["role_list"] = role_list

            # --根据角色获取可访问数据权限和菜单权限
            menu_list = []
            if len(role_ids) > 0:
                sql = "select distinct tablee.menu_id,tablee.parent_id, tablee.name, tablee.url,tablee.type,tablee.icon,tablee.order_num,tablee.is_show"
                sql += " from {} tablee".format(sys_menu_table)
                sql += " left join {} tablef on tablee.menu_id = tablef.menu_id".format(sys_role_menu_table)
                # IN 子句按元素个数动态生成占位符，role_ids 逐个参数化
                sql += " where tablef.role_id in ({})".format(','.join(['%s'] * len(role_ids)))
                sql += " and tablee.is_show='Y'"
                sql += " order by tablee.order_num"
                cursor.execute(sql, role_ids)
                records = cursor.fetchall()
                menu_id_list = []
                for record in records:
                    if record[0] not in menu_id_list:
                        menu_id_list.append(record[0])
                        menu_list.append(
                            {"menu_id": record[0], "parent_id": record[1], "name": record[2], "url": record[3],
                             "type": record[4], "icon": record[5], "order_num": record[6],
                             "is_show": record[7]})
            user_info["menu_list"] = menu_list

            LoggerHelper.set_end_log_info(logClass, logger, start, request.path, user_name,
                                          request,
                                          function_title)

        except Exception as exp:
            res = LoggerHelper.set_end_log_info_in_exception(logClass, logger, start, request.path,
                                                             user_name, request,
                                                             function_title, None, exp)
            user_info = None
        finally:
            return user_info, res

    # 获取用户详情
    def get_details(self, request, user_id):
        function_title = CommonHelper.get_local_str("GET_USER_DETAILS", request)
        start = LoggerHelper.set_start_log_info(logger)
        user_info, res = self.get_user_info(request, start, function_title, user_id, request.auth.user)
        if user_info is not None:
            res = {
                'success': True,
                'message': user_info
            }
        return res

    # 获取认证Token的有效期（单位：秒）
    def get_AUTH_TOKEN_AGE(self):
        # 阶段 4：5 分钟缓存；默认值取自 settings
        return SysmanHelper.get_param_cached('AUTH_TOKEN_AGE', settings.AUTH_TOKEN_AGE, cast=int)

    # 校验一个token是否已过期
    def _check_token_expired(self, token_obj):
        now = int(DateTimeHelper.string2time_stamp(str(datetime.datetime.now())))
        token_created = int(DateTimeHelper.string2time_stamp(str(token_obj.created)))
        return now - token_created > self.get_AUTH_TOKEN_AGE()

    # 通过已存在的token直接登录（A系统登录后免登B系统）
    def login_with_token(self, request, token_value, Token):
        function_title = CommonHelper.get_local_str("LOGIN_BY_TOKEN", request)
        start = LoggerHelper.set_start_log_info(logger)
        user = request.user
        old_token = Token.objects.filter(key=token_value)
        if len(old_token) > 0:
            user = old_token[0].user
            if self._check_token_expired(old_token[0]):
                res = {
                    'success': False,
                    'code': -1,
                    'message': CommonHelper.get_local_str("TOKEN_EXPIRED", request)
                }
            else:
                res = {
                    'success': True,
                    'code': 0,
                    'message': CommonHelper.get_local_str("TOKEN_LOGIN_SUCCESS", request),
                    "userid": user.id,
                    "username": user.username,
                    "token": token_value
                }
        else:
            res = {
                'success': False,
                'code': -1,
                'message': CommonHelper.get_local_str("TOKEN_NOT_EXIST", request)
            }
        LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, user, request, function_title)
        return res

    # 验证token是否过期
    def is_token_expired(self, request, token_value, Token):
        function_title = CommonHelper.get_local_str("VERIFY_TOKEN_EXPIRED", request)
        start = LoggerHelper.set_start_log_info(logger)
        user = request.user
        old_token = Token.objects.filter(key=token_value)
        if len(old_token) > 0:
            res = {
                'success': True,
                'message': CommonHelper.get_local_str("SUCCESS_SUFFIX", request).format(function_title),
                "is_token_expired": self._check_token_expired(old_token[0])
            }
        else:
            res = {
                'success': False,
                'message': CommonHelper.get_local_str("FAIL_SUFFIX", request).format(function_title),
            }
        LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, user, request, function_title)
        return res

    # 通过用户token获取用户信息
    def get_userinfo_by_token(self, request, token_value, Token):
        function_title = CommonHelper.get_local_str("GET_USER_INFO_BY_TOKEN", request)
        start = LoggerHelper.set_start_log_info(logger)
        user = request.user
        old_token = Token.objects.filter(key=token_value)
        if len(old_token) > 0:
            user = old_token[0].user
            user_id = user.id
            user_name = user.username
            res = {
                'success': True,
                'message': CommonHelper.get_local_str("SUCCESS_SUFFIX", request).format(function_title),
                "userid": user_id,
                "username": user_name
            }
            # 只有显式传了 user_scope 才回带角色/菜单，避免每次登录都多查三张表
            if "user_scope" in request.data:
                user_info, res2 = self.get_user_info(request, start, function_title, user_id, user_name)
                res["user_info"] = user_info
        else:
            res = {
                'success': False,
                'message': CommonHelper.get_local_str("FAIL_SUFFIX", request).format(function_title),
            }
        LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, user, request, function_title)
        return res

    # 退出
    def logout(self, request, Token, user_id, auth):
        function_title = "用户退出"
        user = request.user
        start = LoggerHelper.set_start_log_info(logger)
        # 删除登录的token信息
        old_token = Token.objects.filter(user_id=user_id)
        old_token.delete()
        # # 删除登录的保险类型记录信息
        # old_insurance = SysUserLogin.objects.filter(user_id=user_id)
        # old_insurance.delete()
        auth.logout(request)
        res = {
            'code': 0,
            'message': '用户退出成功！',
            "userid": user_id,
        }

        LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, user, request, function_title)

        return res

    # 生成验证码
    def get_verifaction_code(self, request):
        function_title = "生成验证码"
        start = LoggerHelper.set_start_log_info(logger)
        # 背景颜色
        bgcolor = (random.randrange(10, 160), random.randrange(50, 160), 255)
        # 宽高
        width = 140
        height = 60
        # 创建画板
        img = Image.new(mode='RGB', size=(width, height), color=bgcolor)
        # 创建画笔
        draw = ImageDraw.Draw(img, mode='RGB')
        # 定义字符
        text = 'ABCDEFGH12345678'
        # 字体对象，字体，字号
        font1 = ImageFont.truetype(MyAppConfig.verification_font_path, 30)
        # temp用来存储随机生成的验证码
        temp = ''
        for i in range(6):
            # 每循环一次,从a到z中随机生成一个字母或数字
            # 65到90为字母的ASCII码,使用chr把生成的ASCII码转换成字符
            # str把生成的数字转换成字符串
            temp1 = text[random.randrange(0, len(text))]
            # 把生成的随机码存起来
            temp += temp1
            # 每一次生成新的颜色
            color1 = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            # 把文字写到img中
            draw.text((i * 24, i * 6), temp1, color1, font1)
        # 保存到内存流
        buf = io.BytesIO()
        img.save(buf, 'png')
        # 将验证码保存并传递
        request.session['code'] = temp

        LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, None, request, function_title)

        # 将得到的对象返回
        return HttpResponse(buf.getvalue(), 'image/png')

    # 获取用户列表-sql
    def sql_search(self, request,  username, fullname):
        title = "获取用户列表数据"
        res = ""
        start = LoggerHelper.set_start_log_info(logger)
        try:
            # 获取用户列表信息
            # 注意：模糊查询条件原先是 "like '%{}%'".format(前端传值)，属典型 SQL 注入点，
            #       改为 %s 参数化；% 通配符拼在参数值里，不放进 SQL 文本。
            sql = "select tablea.id,tablea.username,tablea.fullname,tableb.department_name,tableb.department_id,tablea.mobile,tablea.sex,tablea.status,tablea.create_time from auth_user tablea"
            sql += " left join sys_department tableb on tablea.department_id=tableb.department_id where tablea.is_superuser=false "
            params = []
            if username is not None and str(username).strip() != "":
                sql += " and tablea.username like %s"
                params.append("%{}%".format(username))
            if fullname is not None and str(fullname).strip() != "":
                sql += " and tablea.fullname like %s"
                params.append("%{}%".format(fullname))
            sql += " order by tablea.create_time desc"
            sql += " LIMIT 500"
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
            records = cursor.fetchall()
            # 阶段 2：原 N+1 — 每行一次 getFullDepartName + 一次 getRoleByUser；
            # 改为先 collect id 列表，再 Bulk 一次拿全，循环内只查 dict。
            user_ids = [int(r[0]) for r in records]
            dept_ids = [int(r[4]) for r in records]
            depart_name_map = SysmanHelper.getFullDepartNameBulk(dept_ids, self.connection)
            role_map = SysmanHelper.getRoleByUserBulk(user_ids, self.connection)
            data_list = []
            for record in records:
                obj = {}
                obj['user_id'] = int(record[0])
                obj['user_name'] = str(record[1])
                obj['full_name'] = str(record[2])
                obj['department_name'] = depart_name_map.get(int(record[4]), "")
                role_id_list, role_name_list = role_map.get(int(record[0]), ([], []))
                obj['role_id_list'] = role_id_list
                obj['role_name_list'] = role_name_list
                obj['mobile'] = str(record[5])
                obj['sex'] = str(record[6])
                obj['status'] = "正常" if int(record[7]) == 1 else "停用"
                obj['create_time'] = str(record[8])
                data_list.append(obj)
            # LIMIT 500 内部硬保护，截掉超出部分（API 不告诉前端）
            res = {
                'success': True,
                'total': len(data_list),
                'info': data_list
            }

            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          title)


        except Exception as exp:
            res = LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                             request.auth.user, request,
                                                             title, None, exp)

        finally:
            return res

        # 设置用户状态

    # 设置用户状态
    def set_status(self, request):
        user_id = request.data["user_id"]
        user_status = request.data["user_status"]

        title = "设置用户状态"
        res = ""
        start = LoggerHelper.set_start_log_info(logger)
        try:

            AuthUser.objects.filter(id=user_id).update(status=user_status)
            res = {
                'success': True,
                'info': "{}成功".format(title)
            }

            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user, request,
                                          title)

        except Exception as exp:

            res = LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                             request.auth.user, request,
                                                             title, None, exp)
        finally:
            return res
