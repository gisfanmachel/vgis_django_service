#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    : 2021/2/17 20:53
# @Author  : gisfan_ai
# @Email   : gisfanmachel@gmail.com
# @File    : urls.py
# @Desc    ：路由器
# @Software: PyCharm

# from django.conf.urls import include
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from my_app.views.userViews import UserViewSet
from my_app.views.businessViews import TtUploadFileDataViewSet, TmDdistrictViewSet
from my_app.views.sysViews import SysConfigViewSet, SysDepartmentViewSet, SysLogViewSet, SysMenuViewSet, \
    SysOssViewSet, SysRoleViewSet, SysRoleMenuViewSet, SysUserViewSet, SysUserRoleViewSet, SysUserTokenViewSet, \
    AuthUserViewSet, SysDictViewSet, SysMessageViewSet, SysParamViewSet

router = DefaultRouter()
# 用户表（已废弃）路由器
router.register(r'user', UserViewSet, basename='user')
# 系统配置表路由器
router.register(r'sysConfig', SysConfigViewSet, basename='sysConfig')
# 系统部门表路由器
router.register(r'sysDepartment', SysDepartmentViewSet, basename='sysDepartment')
# 系统日志路由器
router.register(r'sysLog', SysLogViewSet, basename='sysLog')
# 系统菜单表路由器
router.register(r'sysMenu', SysMenuViewSet, basename='sysMenu')
# 系统定制表由器
router.register(r'sysOss', SysOssViewSet, basename='sysOss')
# 系统角色表由器
router.register(r'sysRole', SysRoleViewSet, basename='sysRole')
# 系统角色菜单表由器
router.register(r'sysRoleMenu', SysRoleMenuViewSet, basename='sysRoleMenu')
# 系统用户表由器
router.register(r'authUser', AuthUserViewSet, basename='authUser')
# 系统用户表（已废弃）由器
router.register(r'sysUser', SysUserViewSet, basename='sysUser')
# 系统用户角色表由器
router.register(r'sysUserRole', SysUserRoleViewSet, basename='sysUserRole')
# 系统用户token表由器
router.register(r'sysUserToken', SysUserTokenViewSet, basename='sysUserToken')
# 系统字典管理由器
router.register(r'sysDict', SysDictViewSet, basename='sysDict')
# 系统消息管理由器
router.register(r'sysMessage', SysMessageViewSet, basename='sysMessage')
# 系统参数管理由器
router.register(r'sysParam', SysParamViewSet, basename='sysParam')
# 上传文件表由器
router.register(r'ttUploadFileData', TtUploadFileDataViewSet, basename='ttUploadFileData')
# 行政区划表由器
router.register(r'tmDdistrict', TmDdistrictViewSet, basename='tmDdistrict')

# no_auth_router = DefaultRouter()
# # 文件相关操作
# no_auth_router.register(r'fileop', FileOpViews, basename='fileop')


# 根据项目名称修改url
urlpatterns = [
    path('my_api/', include(router.urls), name='my_api'),
    # path('fapi/', include(no_auth_router.urls), name='fapi'),
]

