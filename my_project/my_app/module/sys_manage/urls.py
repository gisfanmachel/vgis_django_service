# -*- coding: utf-8 -*-
# sys_manage 模块的路由 —— 前缀 my_api/sysman/
#
# 覆盖：系统配置 / 部门 / 日志 / 菜单 / OSS / 角色 / 角色菜单 /
#       authUser（用户增删改）/ 用户角色 / 用户Token / 参数 / 字典 / 消息
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from my_app.module.sys_manage.views import (
    AuthUserViewSet, SysConfigViewSet, SysDepartmentViewSet, SysDictViewSet, SysLogViewSet,
    SysMenuViewSet, SysMessageViewSet, SysOssViewSet, SysParamViewSet, SysRoleMenuViewSet,
    SysRoleViewSet, SysUserRoleViewSet, SysUserTokenViewSet, SysUserViewSet,
)

router = DefaultRouter()
router.register(r'sysConfig', SysConfigViewSet, basename='sysConfig')
router.register(r'sysDepartment', SysDepartmentViewSet, basename='sysDepartment')
router.register(r'sysLog', SysLogViewSet, basename='sysLog')
router.register(r'sysMenu', SysMenuViewSet, basename='sysMenu')
router.register(r'sysOss', SysOssViewSet, basename='sysOss')
router.register(r'sysRole', SysRoleViewSet, basename='sysRole')
router.register(r'sysRoleMenu', SysRoleMenuViewSet, basename='sysRoleMenu')
router.register(r'authUser', AuthUserViewSet, basename='authUser')
router.register(r'sysUser', SysUserViewSet, basename='sysUser')
router.register(r'sysUserRole', SysUserRoleViewSet, basename='sysUserRole')
router.register(r'sysUserToken', SysUserTokenViewSet, basename='sysUserToken')
router.register(r'sysDict', SysDictViewSet, basename='sysDict')
router.register(r'sysMessage', SysMessageViewSet, basename='sysMessage')
router.register(r'sysParam', SysParamViewSet, basename='sysParam')

urlpatterns = [
    path('my_api/sysman/', include(router.urls), name='sys_manage'),
]
