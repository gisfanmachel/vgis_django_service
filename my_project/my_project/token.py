#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/6/14 13:49
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : token.py.py
# @Descr   : 
# @Software: PyCharm
import datetime

from django.core.cache import cache
# from django.utils.translation import ugettext_lazy as _
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.authtoken.models import Token

# 获取请求头里的token信息
from my_project.settings import AUTH_TOKEN_AGE, TOKEN_KEY
from my_project.utils import TimeUtil


def get_authorization_header(request):
    """
    Return request's 'Authorization:' header, as a bytestring.

    Hide some test client ickyness where the header can be unicode.
    """
    auth = request.META.get('HTTP_AUTHORIZATION', b'')
    if isinstance(auth, type('')):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth


# 自定义的ExpiringTokenAuthentication认证方式
class ExpiringTokenAuthentication(BaseAuthentication):
    model = Token

    def authenticate(self, request):
        auth = get_authorization_header(request)

        if not auth:
            return None
        try:
            token = auth.decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)
        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        # 增加了缓存机制
        # 首先先从缓存中查找
        token_cache = 'token_' + key
        cache_user = cache.get(token_cache)
        if cache_user:
            return (cache_user.user, cache_user)  # 首先查看token是否在缓存中，若存在，直接返回用户
        try:
            token = self.model.objects.get(key=key[6:])

        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed('认证失败')

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('用户被禁止')

        now = int(TimeUtil.string2time_stamp(str(datetime.datetime.now())))
        token_created = int(TimeUtil.string2time_stamp(str(token.created)))

        # 满足条件的话，就表示token已失效，提示用户重新登录刷新token.
        if now - token_created > AUTH_TOKEN_AGE:
            old_token = self.model.objects.filter(key=key[6:])
            user_id=old_token[0].user_id
            old_token.delete()
            # # 删除登录的保险类型记录信息
            # old_insurance = SysUserLogin.objects.filter(user_id=token.user_id)
            # old_insurance.delete()
            raise exceptions.AuthenticationFailed('认证信息过期')

        if token:
            token_cache = 'token_' + key
            cache.set(token_cache, token, AUTH_TOKEN_AGE)  # 添加 token_xxx 到缓存
        return (token.user, token)

    def authenticate_header(self, request):
        # return 'Authorization'
        return TOKEN_KEY
