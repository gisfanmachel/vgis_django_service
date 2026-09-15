# -*- coding: utf-8 -*-
# gis_service 模块的序列化器
#
# 用法：
#   1) 在 vector/tables/ 列表 / tasks/{id}/ 等 REST 响应里把 ORM 对象转 dict；
#   2) 仅 fields = "__all__"，不做字段裁剪（接口契约不动；用户强约束）
from rest_framework import serializers

from my_app.module.gis_service.models import GISLayer, GISTask


class GISTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = GISTask
        fields = "__all__"


class GISLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = GISLayer
        fields = "__all__"