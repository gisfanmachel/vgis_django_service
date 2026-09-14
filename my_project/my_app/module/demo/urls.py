# -*- coding: utf-8 -*-
# demo 模块的路由
#
# 约定：路由前缀写死在模块自己的 urls.py 里（形如 my_api/<模块名>/），
#       顶层 my_project/urls.py 只需一行 path('', include('my_app.module.demo.urls'))。
# 这样新增模块不用动顶层聚合逻辑；代价是**前缀冲突要在顶层显式校验**
# （见 my_project/urls.py 里的启动期检查）。
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from my_app.module.demo.views import TtDemoItemViewSet

router = DefaultRouter()
router.register(r'ttDemoItem', TtDemoItemViewSet, basename='ttDemoItem')

urlpatterns = [
    path('my_api/demo/', include(router.urls), name='demo'),
]
