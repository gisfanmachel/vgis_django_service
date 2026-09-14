# -*- coding: utf-8 -*-
# user_manage 模块的序列化器
from rest_framework import serializers

from my_app.module.user_manage.models import AuthUser, TtRetrivepassToken, TtUserpassQuestion


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = "__all__"


class TtUserpassQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TtUserpassQuestion
        fields = "__all__"


class TtRetrivepassTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = TtRetrivepassToken
        fields = "__all__"
