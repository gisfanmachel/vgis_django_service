import logging
import os
import time

from django.contrib import auth
from django.db import connection
from license_authorize import license_authorize
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from my_app.module.user_manage.manager import UserOperator
from my_app.models import SysLog
from my_app.module.user_manage.models import AuthUser, TtUserpassQuestion
from my_app.module.user_manage.serializers import AuthUserSerializer, TtUserpassQuestionSerializer
from vgis_log.logTools import LoggerHelper
from vgis_utils.vgis_http.httpTools import HttpHelper

from my_app.utils.commonUtility import CommonHelper
from my_app.utils.sysmanUtility import SysmanHelper
from my_project.settings import LINUX_LICENSE_PATH, WINDOWS_LICENSE_PATH

'''
ViewSets定义视图的行为,ModelViewSet默认支持以下action
list: /api/project_batch_data/  TYPE:GET
retrevie:/api/project_batch_data/1  TYPE:GET
create:/api/project_batch_data/  jsonbody   TYPE:POST
delete: /api/project_batch_data/1/  TYPE:DELETE
update: /api/project_batch_data/1/  json body TYPE:PUT
'''
logger = logging.getLogger('django')

import platform
platformType = platform.system().lower()
# 用户相关操作类
class UserViewSet(viewsets.ModelViewSet):
    # loggerHelper = LoggerHelper()
    # 权限，登录操作对所有用户都可执行
    permission_classes = (AllowAny,)
    # 指定查询集
    queryset = AuthUser.objects.all()
    # 指定序列化器
    serializer_class = AuthUserSerializer

    # 身份认证，传入json：{"username":"gpsuser","password":"root12345"}--已不适用
    @action(detail=False, methods=['POST'], url_path='login')
    def login(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        verifcation = request.data.get('verifcation')

        # 增加许可授权
        # client_time = 1684489627117
        client_time = request.data.get('client_time')
        lic_path = WINDOWS_LICENSE_PATH if platformType == 'windows' else LINUX_LICENSE_PATH
        if client_time == None:
            res = {
                'success': False,
                'code': -1,
                'message': '接口请求失败，缺少client_time!'
            }
        else:
            if not os.path.exists(lic_path):
                res = {
                    'success': False,
                    'code': -1,
                    'message': '没有找到许可文件，请联系管理员!'
                }
            else:
                license_result = license_authorize.check_validity(client_time, lic_path)
                # 修正：原写法是 if license_result != True，条件写反了——
                # 导致「许可有效时」反而走到 else 返回"许可已过期"，普通登录永远进不去，
                # 而 loginWithForce 用的是 == True（正确）。这里与之保持一致。
                if license_result == True:
                    # 「已在别处登录」的判定已下沉到 UserOperator.login，且放在密码校验之后。
                    # 原实现在这里提前判定，导致已登录的账号即使密码输错也返回
                    # "用户已在别处登录"，既掩盖密码错误又泄露账号存在性；
                    # 「用户名不正确」也一并由 UserOperator.login 统一返回。
                    userOperator = UserOperator(connection)
                    res = userOperator.login(request, username, password, verifcation, auth, Token)
                else:
                    res = {
                        'success': False,
                        'code': -1,
                        'message': '许可已过期，请联系管理员!'
                    }


        return Response(res)


    # 身份认证，强制登录，冲掉别的地方登录
    @action(detail=False, methods=['POST'], url_path='loginWithForce')
    def login_with_force(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        verifcation = request.data.get('verifcation')

        # 增加许可授权
        # client_time = 1684489627117
        client_time = request.data.get('client_time')
        lic_path = WINDOWS_LICENSE_PATH if platformType == 'windows' else LINUX_LICENSE_PATH
        if client_time==None:
            res = {
                'success': False,
                'code': -1,
                'message': '接口请求失败，缺少client_time!'
            }
        else:
            if not os.path.exists(lic_path):
                res = {
                    'success': False,
                    'code': -1,
                    'message': '没有找到许可文件，请联系管理员!'
                }
            else:
                license_result = license_authorize.check_validity(client_time, lic_path)
                if license_result == True:
                    # force=True：跳过"已在别处登录"检查，直接顶掉对方的登录态
                    userOperator = UserOperator(connection)
                    res = userOperator.login(request, username, password, verifcation, auth,
                                             Token, force=True)
                else:
                    res = {
                        'success': False,
                        'code': -1,
                        'message': '许可已过期，请联系管理员!'
                    }
        return Response(res)



    # 身份认证，传入A系统登录后的token，自动登录B系统
    @action(detail=False, methods=['POST'], url_path='loginByToken')
    def login_by_token(self, request, *args, **kwargs):
        token_value = request.data.get('token')
        userOperator = UserOperator(connection)
        res = userOperator.login_with_token(request, token_value, Token)
        return Response(res)

    # 验证token是否有效（含是否过期）
    @action(detail=False, methods=['POST'], url_path='isTokenExpired')
    def is_token_expired(self, request, *args, **kwargs):
        token_value = request.data.get('token')
        userOperator = UserOperator(connection)
        res = userOperator.is_token_expired(request, token_value, Token)
        return Response(res)

    # 通过token获取用户信息
    @action(detail=False, methods=['POST'], url_path='getUseInfoByToken')
    def get_userinfo_by_token(self, request, *args, **kwargs):
        token_value = request.data.get('token')
        userOperator = UserOperator(connection)
        res = userOperator.get_userinfo_by_token(request, token_value, Token)
        return Response(res)

    # 找回密码--密保问题验证，通过后下发一次性 userkey
    @action(detail=False, methods=['POST'], url_path='retrieve_password')
    def retrieve_password(self, request):
        start = time.perf_counter()
        username = request.data['username']
        userpass_question = request.data['userpass_question']
        userpass_answer = request.data['userpass_answer']
        res = SysmanHelper.retrieve_password(username, userpass_question, userpass_answer, connection,
                                             CommonHelper.get_local_flag(request))
        end = time.perf_counter()
        t = end - start
        LoggerHelper.insert_log_info(SysLog, username, "密保问题验证",
                                     request.path,
                                     HttpHelper.get_params_request(request),
                                     t, HttpHelper.get_ip_request(request))
        return Response(res)

    # 重置密码--用一次性 userkey 改密码
    @action(detail=False, methods=['POST'], url_path='reset_password')
    def reset_password(self, request):
        start = time.perf_counter()
        userid = request.data['userid']
        userkey = request.data['userkey']
        userpass = request.data['userpass']
        res = SysmanHelper.reset_password(userid, userkey, userpass, connection,
                                          CommonHelper.get_local_flag(request))
        end = time.perf_counter()
        t = end - start
        username = AuthUser.objects.get(id=userid).username
        LoggerHelper.insert_log_info(SysLog, username, "重置密码",
                                     request.path,
                                     HttpHelper.get_params_request(request),
                                     t, HttpHelper.get_ip_request(request))
        return Response(res)

    # # 退出登录
    # # 移到sysView.py里，需要增加token，这样可以避免误操作（不加token的误调用）
    # @action(detail=False, methods=['POST'], url_path='logout')
    # def logout(self, request):
    #     username = request.data.get('username')
    #     userid = request.data.get('userid')
    #     userOperator = UserOperator(connection)
    #     res = userOperator.logout(request, Token, userid, auth)
    #     return Response(res)

    # 获取验证码
    @action(detail=False, methods=['GET'], url_path='verfication')
    def verfication(self, request):
        userOperator = UserOperator(connection)
        return userOperator.get_verifaction_code(request)

    # 获取是否开启验证码
    @action(detail=False, methods=['GET'], url_path='is_use_verfication')
    def is_use_verfication(self, request):
        userOperator = UserOperator(connection)
        res = userOperator.return_is_use_verification_code(request)
        return Response(res)

    # 退出登录（与 PNT 项目对齐：路径为 user/logout/；authUser/logout/ 同样可用）
    # 注意：UserViewSet 整体是 AllowAny，但退出登录会删掉账号的 token，
    #       属写操作，这里单独要求已认证，避免"不带 token 的误调用"把别人踢下线。
    @action(detail=False, methods=['POST'], url_path='logout', permission_classes=[IsAuthenticated])
    def logout(self, request):
        username = request.data.get('username')
        userid = request.data.get('userid')
        userOperator = UserOperator(connection)
        res = userOperator.logout(request, Token, userid, auth)
        return Response(res)


#  分页相关操作类
class MyPage(PageNumberPagination):
    page_size_query_param = "max_page"
    page_query_param = "page"


# 忘记密码的密保问题（登录前要能拉取，因此 AllowAny 且不做 token 认证）
class TtUserpassQuestionViewSet(viewsets.ModelViewSet):
    queryset = TtUserpassQuestion.objects.all().order_by('id')
    serializer_class = TtUserpassQuestionSerializer
    permission_classes = (AllowAny,)
    # 刻意不配 authentication_classes：登录前需要拉取密保问题
