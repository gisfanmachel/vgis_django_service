# -*- coding: utf-8 -*-
# common 模块的序列化器
from rest_framework import serializers

from my_app.module.common.models import TmDdistrict, TtUploadFileData


class TtUploadFileDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = TtUploadFileData
        fields = "__all__"


class TmDdistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = TmDdistrict
        fields = "__all__"
