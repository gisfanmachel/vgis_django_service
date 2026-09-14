# -*- coding: utf-8 -*-
# common 模块的路由 —— 前缀 my_api/common/
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from my_app.module.common.views import TmDdistrictViewSet, TtUploadFileDataViewSet

router = DefaultRouter()
router.register(r'ttUploadFileData', TtUploadFileDataViewSet, basename='ttUploadFileData')
router.register(r'tmDdistrict', TmDdistrictViewSet, basename='tmDdistrict')

urlpatterns = [
    path('my_api/common/', include(router.urls), name='common'),
]
