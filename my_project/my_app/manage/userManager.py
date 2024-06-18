#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    : 2022/5/7 10:01
# @Author  : gisfan_ai
# @Email   : gisfanmachel@gmail.com
# @File    : userManager.py
# @Desc    ：置信度系统的业务处理类
# @Software: PyCharm

import io
import logging
import random
from datetime import timedelta

from PIL import Image, ImageDraw, ImageFont
from django.http import HttpResponse
from django.utils import timezone
from loguru import logger
from vgis_log.logTools import LoggerHelper
from vgis_utils.vgis_datetime.datetimeTools import DateTimeHelper

# 用户相关操作类
from my_app.apps import MyAppConfig
from my_app.models import AuthUser, SysLog
from my_app.utils.sysmanUtility import SysmanHelper
from my_project import settings
from my_project.settings import IS_USE_VERIFICATION_CODE

logger = logging.getLogger('django')


class UserOperator:
    def __init__(self, connection):
        self.connection = connection

    # 登录
    # 通过用户名和密码登录
    # 连续输错4次密码，锁定10分钟，10分钟后没输错一次密码都重新锁定10分钟---参数可配置
    def login(self, request, username, password, verifcation, auth, Token):
        function_title = "用户登录"
        try:
            start = LoggerHelper.set_start_log_info(logger)
            userObject = AuthUser.objects.get(username=username)
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
                    # 登录失败，增加失败次数
                    if userObject.login_error_attempts is None:
                        userObject.login_error_attempts = 1
                    else:
                        userObject.login_error_attempts += 1
                    if userObject.login_error_attempts >= settings.LOGIN_ERROR_ATTEMPTS:
                        # 锁定账号
                        userObject.login_locked_until = timezone.now() + timedelta(seconds=settings.LOGIN_LOCKED_TIME)
                    userObject.save()
                    res = {
                        'success': False,
                        'code': -1,
                        'message': '用户名或密码不对!'
                    }
                    return res
                else:
                    # 验证码
                    # 验证码
                    if IS_USE_VERIFICATION_CODE:
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

    # 获取用户详情
    def get_details(self, request, user_id):
        function_title = "获取用户详情"
        start = LoggerHelper.set_start_log_info(logger)
        res = ""
        try:
            user_info = {}
            # 获取获取用户姓名，部门
            sql = "select tablea.username,tablea.fullname,tableb.department_name from auth_user tablea "
            sql += " left join sys_department tableb on tablea.department_id=tableb.department_id"
            sql += " where tablea.id={}".format(user_id)
            cursor = self.connection.cursor()
            cursor.execute(sql)
            record = cursor.fetchone()
            if record is not None:
                user_info["userid"] = user_id
                user_info["username"] = record[0]
                user_info["fullname"] = record[1]
                user_info["department_name"] = record[2]

            # --获取用户的角色（多个）
            sql = "select distinct tablec.role_name, tablec.role_id from sys_role tablec "
            sql += " left join  sys_user_role tabled on tablec.role_id = tabled.role_id"
            sql += " where tabled.user_id ={}".format(user_id)
            cursor.execute(sql)
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
            data_list = []
            menu_list = []
            if len(role_ids) > 0:
                sql = "select distinct tablee.menu_id,tablee.parent_id, tablee.name, tablee.url,tablee.type,tablee.icon,tablee.order_num,tablee.is_show"
                sql += " from sys_menu tablee"
                sql += " left join sys_role_menu tablef on tablee.menu_id = tablef.menu_id"
                sql += " where tablef.role_id in ({})".format(','.join([str(i) for i in role_ids]))
                sql += " and tablee.is_show='Y'"
                # sql += " and (tablee.icon='data' or  tablee.icon='menu')"
                sql += " order by tablee.order_num"
                cursor.execute(sql)
                records = cursor.fetchall()
                menu_id_list = []
                for record in records:
                    if record[0] not in menu_id_list:
                        menu_id_list.append(record[0])
                        # if record[2] == "data":
                        #     data_list.append({"data_type": record[1]})
                        # if record[2] == "menu":
                        menu_list.append(
                            {"menu_id": record[0], "parent_id": record[1], "name": record[2], "url": record[3],
                             "type": record[4], "icon": record[5], "order_num": record[6],
                             "is_show": record[7]})
            # user_info["data_list"] = data_list
            user_info["menu_list"] = menu_list

            res = {
                'success': True,
                'message': user_info
            }
            LoggerHelper.set_end_log_info(SysLog, logger, start, request.path, request.auth.user,
                                          request,
                                          function_title)

        except Exception as exp:
            res = LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, request.path,
                                                             request.auth.user, request,
                                                             function_title, None, exp)
        finally:
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
            sql = "select tablea.id,tablea.username,tablea.fullname,tableb.department_name,tableb.department_id,tablea.mobile,tablea.sex,tablea.status,tablea.create_time from auth_user tablea"
            sql+=" left join sys_department tableb on tablea.department_id=tableb.department_id where  tablea.is_superuser=false "
            if username is not None and str(username).strip() != "":
                sql += " and tablea.username like '%{}%'".format(username)
            if fullname is not None and str(fullname).strip() != "":
                sql += " and tablea.fullname like '%{}%'".format(fullname)
            sql += " order by tablea.create_time desc"
            cursor = self.connection.cursor()
            cursor.execute(sql)
            records = cursor.fetchall()
            data_list = []
            for record in records:
                obj = {}
                obj['user_id'] = int(record[0])
                obj['user_name'] = str(record[1])
                obj['full_name'] = str(record[2])
                obj['department_name'] = SysmanHelper.getFullDepartName(int(record[4]), self.connection)
                obj['role_id_list'], obj['role_name_list'] = SysmanHelper.getRoleByUser(int(record[0]), self.connection)
                obj['mobile'] = str(record[5])
                obj['sex'] = str(record[6])
                obj['status'] = "正常" if int(record[7]) == 1 else "停用"
                obj['create_time'] = str(record[8])
                data_list.append(obj)
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
