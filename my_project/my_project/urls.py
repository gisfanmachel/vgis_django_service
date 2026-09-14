"""my_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

说明（Django 6 兼容）：
  - 原 rest_framework_swagger 已停止维护且不支持新版，改用 drf-spectacular
  - 原 rest_framework.documentation.include_docs_urls 在 DRF 3.18 已移除，不再引用
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    # API 文档：/docs/ 是 Swagger UI，/docs/schema/ 是 OpenAPI schema
    path('docs/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # ---- 分模块路由：各模块前缀写死在模块自己的 urls.py 里 ----
    # 新增模块只需在这里加一行 include。
    # 前缀冲突由 my_app/checks.py 的 system check 在启动时校验（manage.py check 也会跑）。
    path('', include('my_app.module.sys_manage.urls')),
    path('', include('my_app.module.common.urls')),
    path('', include('my_app.module.user_manage.urls')),
    path('', include('my_app.module.demo.urls')),
]
