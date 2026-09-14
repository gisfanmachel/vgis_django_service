# -*- coding: utf-8 -*-
# sys_manage 模块的序列化器
from rest_framework import serializers

from my_app.module.sys_manage.models import (
    SysConfig, SysDepartment, SysDict, SysLog, SysMenu, SysMessage,
    SysOss, SysParam, SysRole, SysRoleMenu, SysUser, SysUserRole, SysUserToken,
)


class SysConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysConfig
        fields = "__all__"


class SysDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysDepartment
        fields = "__all__"


class SysLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysLog
        fields = "__all__"


class SysMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysMenu
        fields = "__all__"


class SysOssSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysOss
        fields = "__all__"


class SysRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysRole
        fields = "__all__"


class SysRoleMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysRoleMenu
        fields = "__all__"


class SysUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUser
        fields = "__all__"


class SysUserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUserRole
        fields = "__all__"


class SysUserTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysUserToken
        fields = "__all__"


class SysParamSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysParam
        fields = "__all__"


class SysDictSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysDict
        fields = "__all__"


class SysMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SysMessage
        fields = "__all__"
