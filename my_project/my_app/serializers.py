# -*- coding: utf-8 -*-
"""
===================================
#!/usr/bin/python3.9
@Author: chenxw
@Email : gisfanmachel@gmail.com
@File: serializers.py.py
@Date: Create in 2021/2/5 19:49
@Description: 序列化器
@ Software: PyCharm
===================================
"""

from rest_framework import serializers
from my_app.models import AuthUser, TtUploadFileData, SysConfig, SysDepartment, SysLog, SysMenu, SysOss, SysRole, \
    SysRoleMenu, SysUser, \
    SysUserRole, SysUserToken, TmDdistrict, SysParam, SysDict, SysMessage


# 用户信息表序列化器
class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = "__all__"



# 上传文件表序列器
class TtUploadFileDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TtUploadFileData
        fields = "__all__"

# 行政区划表序列器
class TmDdistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = TmDdistrict
        fields = "__all__"

# 系统配置表序列器
class SysConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysConfig
        fields = "__all__"


# 系统部门表序列器
class SysDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysDepartment
        fields = "__all__"


# 系统日志表序列器
class SysLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysLog
        fields = "__all__"

# 系统菜单表序列器
class SysMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysMenu
        fields = "__all__"


# 系统定制表序列器
class SysOssSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysOss
        fields = "__all__"


# 系统角色表序列器
class SysRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysRole
        fields = "__all__"


# 系统角色菜单表序列器
class SysRoleMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysRoleMenu
        fields = "__all__"


# 系统用户表（已废弃）序列器
class SysUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUser
        fields = "__all__"


# 系统用户角色表序列器
class SysUserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUserRole
        fields = "__all__"


# 系统用户token表序列器
class SysUserTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUserToken
        fields = "__all__"

#系统参数序列器
class SysParamSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysParam
        fields = "__all__"

#系统参数序列器
class SysDictSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysDict
        fields = "__all__"

# 系统参数序列器
class SysMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysMessage
        fields = "__all__"