# -*- coding: utf-8 -*-
# user_manage 模块的路由 —— 前缀 my_api/userman/
#
# 前缀用 userman 而不是 user：router 名本来就是 user，
# 若再用 user 当模块前缀会拼出 /my_api/user/user/login/ 这种双写。
#
# 注意：ttUserpassQuestion（密保问题字典）属于忘记密码功能，一并放在本模块；
#       它是登录前就要拉取的免鉴权接口。
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from my_app.module.user_manage.views import TtUserpassQuestionViewSet, UserViewSet

router = DefaultRouter()
router.register(r'user', UserViewSet, basename='user')
router.register(r'ttUserpassQuestion', TtUserpassQuestionViewSet, basename='ttUserpassQuestion')

urlpatterns = [
    path('my_api/userman/', include(router.urls), name='user_manage'),
]
