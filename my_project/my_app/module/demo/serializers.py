# -*- coding: utf-8 -*-
# demo 模块的序列化器
from rest_framework import serializers

from my_app.module.demo.models import TtDemoItem


class TtDemoItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TtDemoItem
        fields = "__all__"
