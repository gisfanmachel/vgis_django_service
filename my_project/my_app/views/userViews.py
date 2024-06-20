import logging
import os

from django.contrib import auth
from django.db import connection
from license_authorize import license_authorize
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from my_app.manage.userManager import UserOperator
from my_app.models import AuthUser
from my_app.serializers import AuthUserSerializer
import datetime
from vgis_utils.vgis_datetime.datetimeTools import DateTimeHelper

from my_project.settings import AUTH_TOKEN_AGE, LINUX_LICENSE_PATH, WINDOWS_LICENSE_PATH

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
                if license_result != True:
                    if len(AuthUser.objects.filter(username=username)) > 0:
                        user_id = AuthUser.objects.filter(username=username)[0].id
                        oldToken = Token.objects.filter(user_id=user_id)
                        if len(oldToken) > 0:
                            now = int(DateTimeHelper.string2time_stamp(str(datetime.datetime.now())))
                            token_created = int(DateTimeHelper.string2time_stamp(str(oldToken[0].created)))
                            is_token_expired = False
                            if now - token_created > AUTH_TOKEN_AGE:
                                is_token_expired = True
                        if len(oldToken) > 0 and is_token_expired is False:
                            res = {
                                'success': False,
                                'code': -2,
                                'message': '用户已在别处登录!'
                            }
                        else:
                            userOperator = UserOperator(connection)
                            res = userOperator.login(request, username, password, verifcation, auth, Token)
                    else:
                        res = {
                            'success': False,
                            'code': -1,
                            'message': '用户名不正确!'
                        }
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
                    userOperator = UserOperator(connection)
                    res = userOperator.login(request, username, password, verifcation, auth,
                                                                 Token)
                else:
                    res = {
                        'success': False,
                        'code': -1,
                        'message': '许可已过期，请联系管理员!'
                    }
        return Response(res)



    # 身份认证，传入单点登录的token
    @action(detail=False, methods=['POST'], url_path='loginByToken')
    def login_by_token(self, request, *args, **kwargs):
        ssoToken = request.data.get('ssoToken')
        userOperator = UserOperator()
        res = userOperator.login_by_token(request, ssoToken, auth, Token)
        return Response(res)

    # 退出登录
    @action(detail=False, methods=['POST'], url_path='logout')
    def logout(self, request):
        username = request.data.get('username')
        userid = request.data.get('userid')
        userOperator = UserOperator(connection)
        res = userOperator.logout(request, Token, userid, auth)
        return Response(res)

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


#  分页相关操作类
class MyPage(PageNumberPagination):
    page_size_query_param = "max_page"
    page_query_param = "page"
