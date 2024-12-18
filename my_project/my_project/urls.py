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
"""
from django.contrib import admin
from django.urls import path

from django.contrib import admin
from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework_swagger.views import get_swagger_view
schema_view = get_swagger_view(title='API文档')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', schema_view),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('', include('my_app.urls')),
    path('async_view/', asyncViews.my_view, name='async_view'),
    path('start_task/', celeryViews.start_task, name='start_task'),
    path('check_task/', celeryViews.check_task, name='check_task'),
]