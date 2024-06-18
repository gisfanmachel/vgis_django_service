# @Software: PyCharm
# !/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/12/15 20:15
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : sysViews.py
# @Descr   :
# @Software: PyCharm
import datetime
import os
import time

from django.db import connection
from loguru import logger
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from vgis_log.logTools import LoggerHelper
from vgis_utils.vgis_http.httpTools import HttpHelper

from my_app.manage.sysManager import SysOperator
from my_app.manage.userManager import UserOperator
from my_app.models import SysConfig, SysDepartment, SysLog, SysMenu, SysOss, SysRole, SysRoleMenu, SysUser, \
    SysUserRole, SysUserToken, AuthUser
from my_app.serializers import SysConfigSerializer, SysDepartmentSerializer, SysLogSerializer, SysMenuSerializer, \
    SysOssSerializer, SysRoleSerializer, SysRoleMenuSerializer, SysUserSerializer, SysUserRoleSerializer, \
    SysUserTokenSerializer, AuthUserSerializer
from my_app.utils.passwordUtility import PasswordHelper
from my_app.utils.sysmanUtility import SysmanHelper
from my_app.views.response.baseRespone import Result
from my_project import settings
from my_project.token import ExpiringTokenAuthentication


class SysConfigViewSet(viewsets.ModelViewSet):
    queryset = SysConfig.objects.all().order_by('id')
    serializer_class = SysConfigSerializer
    permission_classes = (IsAuthenticated,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)


class SysDepartmentViewSet(viewsets.ModelViewSet):
    queryset = SysDepartment.objects.all().order_by('department_id')
    serializer_class = SysDepartmentSerializer
    permission_classes = (IsAuthenticated,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)

    def create(self, request, *args, **kwargs):

        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        max_num = SysmanHelper.getDepartOrderNum(request.data["parent_id"], connection)
        request.data["order_num"] = max_num + 1
        request.data["del_flag"] = 0
        request.data["create_user_id"] = request.auth.user_id
        request.data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        end = time.perf_counter()
        t = end - start
        logger.info("总共用时{}秒".format(t))
        LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增部门",
                                     request.path,
                                     HttpHelper.get_params_request(request),
                                     t, HttpHelper.get_ip_request(request))
        return super().create(request)

    def update(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # id = kwargs["pk"]
        logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        end = time.perf_counter()
        t = end - start
        logger.info("总共用时{}秒".format(t))
        LoggerHelper.insert_log_info(SysLog, request.auth.user, "修改部门",
                                     request.path,
                                     HttpHelper.get_params_request(request),
                                     t, HttpHelper.get_ip_request(request))
        return super().update(request, *args, **kwargs)

    # 获取部门列表-sql
    @action(detail=False, methods=['GET'], url_path='sqlsearch')
    def sql_search(self, request):
        sysOperator = SysOperator(connection)
        department_name = self.request.query_params.get('department_name', '')
        department_status = self.request.query_params.get('department_status', '')
        res = sysOperator.sql_search_department(request, department_name, department_status)
        return Response(res)

    # 获取部门状态列表
    @action(detail=False, methods=['GET'], url_path='departstatus')
    def status_list(self, request):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        res = {
            'success': True,
            'info': [{'status': '正常', 'code': 1}, {'status': '停用', 'code': 0}]
        }
        logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        end = time.perf_counter()
        t = end - start
        logger.info("总共用时{}秒".format(t))
        LoggerHelper.insert_log_info(SysLog, request.auth.user, "获取部门状态列表",
                                     request.path,
                                     HttpHelper.get_params_request(request),
                                     t, HttpHelper.get_ip_request(request))
        return Response(res)

    # 修改部门状态
    @action(detail=False, methods=['POST'], url_path='setstatus')
    def set_status(self, request):
        sysOperator = SysOperator(connection)
        res = sysOperator.set_department_status(request)
        return Response(res)

    # 逻辑删除部门及下属部门
    @action(detail=False, methods=['POST'], url_path='delete')
    def delete_department(self, request):
        sysOperator = SysOperator(connection)
        res = sysOperator.delete_department(request)
        return Response(res)


class SysLogViewSet(viewsets.ModelViewSet):
    queryset = SysLog.objects.all().order_by('id')
    serializer_class = SysLogSerializer
    permission_classes = (IsAuthenticated,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)

    # 获取日志列表-sql
    @action(detail=False, methods=['GET'], url_path='sqlsearch')
    def sql_search(self, request):
        sysOperator = SysOperator(connection)
        username = self.request.query_params.get('username', '')
        querystarttime = self.request.query_params.get('querystarttime', '')
        queryendtime = self.request.query_params.get('queryendtime', '')
        res = sysOperator.sql_search_log(request, username, querystarttime, queryendtime)
        return Response(res)


class SysMenuViewSet(viewsets.ModelViewSet):
    queryset = SysMenu.objects.all().order_by('menu_id')
    serializer_class = SysMenuSerializer
    permission_classes = (IsAuthenticated,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)

    def list(self, request, *args, **kwargs):
        results = SysMenu.objects.all().order_by('menu_id')
        data = []
        for result in results:
            data.append(SysMenuSerializer(result).data)
        results = {'results': data}
        return Response(results)

    def create(self, request, *args, **kwargs):
        function_title = "新增菜单"
        start = LoggerHelper.set_start_log_info(logger)
        api_path = request.path
        menu_name = request.data["name"]
        if len(SysMenu.objects.filter(name=menu_name)) > 0:
            error_info = "新增的菜单名:{}已存在，请换个名称".format(menu_name)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, api_path,
                                                       request.auth.user, request,
                                                       function_title, error_info, None)
            return Result.fail(error_info, error_info)
        else:
            request.data["create_user_id"] = request.auth.user_id
            request.data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            super().create(request)

            LoggerHelper.set_end_log_info(SysLog, logger, start, api_path, request.auth.user, request,
                                          function_title)
            msg = "{}成功".format(function_title)
            return Result.sucess(msg, None)

    def update(self, request, *args, **kwargs):
        function_title = "修改菜单"
        start = LoggerHelper.set_start_log_info(logger)
        api_path = request.path
        id = kwargs["pk"]
        if len(SysMenu.objects.filter(menu_id=id)) > 0:
            old_menu_name = SysMenu.objects.filter(menu_id=id)[0].name

        new_menu_name = request.data["name"]
        if old_menu_name != new_menu_name and len(SysMenu.objects.filter(name=new_menu_name)) > 0:

            error_info = "更新的菜单名:{}已存在，请换个名称".format(new_menu_name)
            LoggerHelper.set_end_log_info_in_exception(SysLog, logger, start, api_path,
                                                       request.auth.user, request,
                                                       function_title, error_info, None)
            return Result.fail(error_info, error_info)
        else:
            super().update(request, *args, **kwargs)
            LoggerHelper.set_end_log_info(SysLog, logger, start, api_path, request.auth.user, request,
                                          function_title)
            msg = "{}成功".format(function_title)
            return Result.sucess(msg, None)


    # #删除菜单的同时，将sys_role_menu里的菜单删除
    def destroy(self, request, *args, **kwargs):
        id = kwargs["pk"]
        start = time.perf_counter()
        SysRoleMenu.objects.filter(menu_id=id).delete()
        logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        end = time.perf_counter()
        t = end - start
        logger.info("总共用时{}秒".format(t))
        LoggerHelper.insert_log_info(SysLog, request.auth.user, "删除菜单",
                                     request.path,
                                     HttpHelper.get_params_request(request),
                                     t, HttpHelper.get_ip_request(request))
        return super().destroy(request, *args, **kwargs)


class SysOssViewSet(viewsets.ModelViewSet):
    queryset = SysOss.objects.all().order_by('id')
    serializer_class = SysOssSerializer
    permission_classes = (IsAuthenticated,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)


class SysRoleViewSet(viewsets.ModelViewSet):
    queryset = SysRole.objects.all().order_by('role_id')
    serializer_class = SysRoleSerializer
    permission_classes = (IsAuthenticated,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)

    def create(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        role_name = request.data["role_name"]
        if len(SysRole.objects.filter(role_name=role_name)) > 0:
            res = {
                'success': False,
                'info': "新增的角色名:{}已存在，请换个名称".format(role_name)
            }

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增角色",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            request.data["create_user_id"] = request.auth.user_id
            request.data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            returnrole = super().create(request)
            for menu_id in request.data["menuIdList"]:
                obj = {}
                obj["role_id"] = returnrole.data["role_id"]
                obj["menu_id"] = menu_id
                SysRoleMenu.objects.create(**obj)

            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增角色",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))

            return returnrole

    def update(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        id = kwargs["pk"]
        if len(SysRole.objects.filter(role_id=id)) > 0:
            old_role_name = SysRole.objects.filter(role_id=id)[0].role_name

        new_role_name = request.data["role_name"]
        if old_role_name != new_role_name and len(SysRole.objects.filter(role_name=new_role_name)) > 0:
            res = {
                'success': False,
                'info': "更新的角色名:{}已存在，请换个名称".format(new_role_name)
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新角色",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            SysRoleMenu.objects.filter(role_id=id).delete()
            for menu_id in request.data["menuIdList"]:
                obj = {}
                obj["role_id"] = id
                obj["menu_id"] = menu_id
                SysRoleMenu.objects.create(**obj)
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新角色",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return super().update(request, *args, **kwargs)

    # 获取角色列表-sql
    @action(detail=False, methods=['GET'], url_path='sqlsearch')
    def sql_search(self, request):
        sysOperator = SysOperator(connection)
        role_name = self.request.query_params.get('role_name', '')
        res = sysOperator.sql_search_role(request, role_name)
        return Response(res)

    # # 删除角色的同时，将sys_role_menu \sys_user_role里的角色删除
    def destroy(self, request, *args, **kwargs):
        id = kwargs["pk"]
        start = time.perf_counter()
        SysUserRole.objects.filter(role_id=id).delete()
        SysRoleMenu.objects.filter(role_id=id).delete()
        logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        end = time.perf_counter()
        t = end - start
        logger.info("总共用时{}秒".format(t))
        LoggerHelper.insert_log_info(SysLog, request.auth.user, "删除角色",
                                     request.path,
                                     HttpHelper.get_params_request(request),
                                     t, HttpHelper.get_ip_request(request))
        return super().destroy(request, *args, **kwargs)


class SysRoleMenuViewSet(viewsets.ModelViewSet):
    queryset = SysRoleMenu.objects.all().order_by('id')
    serializer_class = SysRoleMenuSerializer
    permission_classes = (IsAuthenticated,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)


class SysUserViewSet(viewsets.ModelViewSet):
    queryset = SysUser.objects.all().order_by('user_id')
    serializer_class = SysUserSerializer
    permission_classes = (IsAuthenticated,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)


class AuthUserViewSet(viewsets.ModelViewSet):
    queryset = AuthUser.objects.all().order_by('id')
    serializer_class = AuthUserSerializer
    permission_classes = (IsAuthenticated,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)

    def create(self, request, *args, **kwargs):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        username = request.data["username"]
        if len(AuthUser.objects.filter(username=username)) > 0:
            res = {
                'success': False,
                'info': "新增的用户名:{}已存在，请换个名称".format(username)
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增用户",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            # maxid = AuthUser.objects.all().order_by("-id")[0].id
            # request.data["id"] = int(maxid) + 1
            request.data["is_superuser"] = False
            if "first_name" not in request.data or request.data["first_name"] is None:
                request.data["first_name"] = "null"
            if "last_name" not in request.data or request.data["last_name"] is None:
                request.data["last_name"] = "null"
            request.data["is_staff"] = True
            request.data["date_joined"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            request.data["is_active"] = True if int(request.data["status"]) == 1 else False
            request.data["password"] = PasswordHelper.getEncrptPassword(request.data["password"])
            request.data["create_user_id"] = request.auth.user_id
            request.data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            returnuser = super().create(request)
            for role_id in request.data["roleIdList"]:
                obj = {}
                obj["user_id"] = returnuser.data["id"]
                obj["role_id"] = role_id
                SysUserRole.objects.create(**obj)
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "新增用户",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return returnuser

    def update(self, request, *args, **kwargs):
        log_file_path = os.path.join(settings.LOGGER_ROOT,
                                     "{}_view.log".format(datetime.datetime.now().strftime('%Y%m%d%H%M%S')))
        logger.add(log_file_path, format="{time} | {level} | {message}", level="INFO", rotation="50MB")
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        id = kwargs["pk"]
        if len(AuthUser.objects.filter(id=id)) > 0:
            user_id = AuthUser.objects.filter(id=id)[0].id
            old_username = AuthUser.objects.filter(id=id)[0].username
            request.data["is_superuser"] = AuthUser.objects.filter(id=id)[0].is_superuser
            request.data["first_name"] = AuthUser.objects.filter(id=id)[0].first_name
            request.data["last_name"] = AuthUser.objects.filter(id=id)[0].last_name
            request.data["is_staff"] = AuthUser.objects.filter(id=id)[0].is_staff
            request.data["date_joined"] = AuthUser.objects.filter(id=id)[0].date_joined
            request.data["password"] = AuthUser.objects.filter(id=id)[0].password
            request.data["is_active"] = True if int(request.data["status"]) == 1 else False
            request.data["create_user_id"] = AuthUser.objects.filter(id=id)[0].create_user_id
            request.data["create_time"] = AuthUser.objects.filter(id=id)[0].create_time
            request.data["modify_user_id"] = request.auth.user_id
            request.data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        new_username = request.data["username"]
        if old_username != new_username and len(AuthUser.objects.filter(username=new_username)) > 0:
            res = {
                'success': False,
                'info': "更新的用户名:{}已存在，请换个名称".format(new_username)
            }
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新用户",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return Response(res)
        else:
            SysUserRole.objects.filter(user_id=user_id).delete()
            for role_id in request.data["roleIdList"]:
                obj = {}
                obj["user_id"] = user_id
                obj["role_id"] = role_id
                SysUserRole.objects.create(**obj)
            logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            end = time.perf_counter()
            t = end - start
            logger.info("总共用时{}秒".format(t))
            LoggerHelper.insert_log_info(SysLog, request.auth.user, "更新用户",
                                         request.path,
                                         HttpHelper.get_params_request(request),
                                         t, HttpHelper.get_ip_request(request))
            return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['POST'], url_path='get_details')
    # 获取用户详情
    def get_details(self, request, *args, **kwargs):
        userid = request.data.get('userid')
        userOperator = UserOperator(connection)
        res = userOperator.get_details(request, userid)
        return Response(res)

    def destroy(self, request, *args, **kwargs):
        # instance = self.get_object()
        # self.perform_destroy(instance)
        # return Result.ok()

        id = kwargs["pk"]
        start = time.perf_counter()
        SysUserRole.objects.filter(user_id=id).delete()
        logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        end = time.perf_counter()
        t = end - start
        logger.info("总共用时{}秒".format(t))
        LoggerHelper.insert_log_info(SysLog, request.auth.user, "删除用户",
                                     request.path,
                                     HttpHelper.get_params_request(request),
                                     t, HttpHelper.get_ip_request(request))
        return super().destroy(request, *args, **kwargs)

    # 获取用户列表-sql
    @action(detail=False, methods=['GET'], url_path='sqlsearch')
    def sql_search(self, request):
        userOperator = UserOperator(connection)
        user_name = self.request.query_params.get('user_name', '')
        user_name = self.request.query_params.get('user_name', '')
        full_name = self.request.query_params.get('full_name', '')
        res = userOperator.sql_search(request, user_name, full_name)
        return Response(res)

    # 获取用户状态列表
    @action(detail=False, methods=['GET'], url_path='userstatus')
    def status_list(self, request):
        start = time.perf_counter()
        logger.info("开始时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        res = {
            'success': True,
            'info': [{'status': '正常', 'code': 1}, {'status': '停用', 'code': 0}]
        }
        logger.info("结束时间：" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        end = time.perf_counter()
        t = end - start
        logger.info("总共用时{}秒".format(t))

        LoggerHelper.insert_log_info(SysLog, request.auth.user, "获取用户状态列表",
                                     "/api/authUser/userstatus",
                                     HttpHelper.get_params_request(request),
                                     t, HttpHelper.get_ip_request(request))
        return Response(res)

    # 修改用户状态
    @action(detail=False, methods=['POST'], url_path='setstatus')
    def set_status(self, request):
        userOperator = UserOperator(connection)
        res = userOperator.set_status(request)
        return Response(res)


class SysUserRoleViewSet(viewsets.ModelViewSet):
    queryset = SysUserRole.objects.all().order_by('id')
    serializer_class = SysUserRoleSerializer
    permission_classes = (IsAuthenticated,)
    # token认证
    # authentication_classes = (TokenAuthentication,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)


class SysUserTokenViewSet(viewsets.ModelViewSet):
    queryset = SysUserToken.objects.all().order_by('user_id')
    serializer_class = SysUserTokenSerializer
    permission_classes = (IsAuthenticated,)
    # 自定义token认证
    authentication_classes = (ExpiringTokenAuthentication,)
