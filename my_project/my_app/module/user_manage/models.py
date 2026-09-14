# -*- coding: utf-8 -*-
# user_manage 模块的模型：认证/身份相关表 + 忘记密码两张表
#
# 约定：managed = False + 显式 db_table（表由外部 SQL 维护，不走迁移）
# 说明：AuthUser 等认证表放在本模块；sys_manage 的 authUser 增删改接口
#       通过 from my_app.module.user_manage.models import AuthUser 跨模块引用。
from django.db import models


# 认证相关的模型


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    fullname = models.CharField(max_length=255)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    department_id = models.BigIntegerField(blank=True, null=True)
    # 注意：sex / mobile 不能声明 unique=True。
    # 数据库 auth_user 上只有主键和 username 索引，并无这两列的唯一约束；
    # 声明 unique=True 会让 DRF 序列化器在新增用户时按"性别不能重复"校验，
    # 导致第二个同性别的用户直接建不了（原模型为 inspectdb 误判所留）。
    sex = models.CharField(max_length=255, blank=True, null=True)
    mobile = models.CharField(max_length=100, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    create_time = models.DateTimeField(null=True, blank=True)
    modify_user_id = models.BigIntegerField(blank=True, null=True)
    modify_time = models.DateTimeField(null=True, blank=True)
    login_error_attempts = models.SmallIntegerField(default=0)
    login_locked_until = models.DateTimeField(null=True, blank=True)
    # 忘记密码用的密保问题与答案（数据库已具备这两列；
    # SysmanHelper.retrieve_password 走裸 SQL 读，模型里也要声明，
    # 否则通过 ORM 写入不会落库）
    userpass_question = models.CharField(max_length=2550, blank=True, null=True)
    userpass_answer = models.CharField(max_length=2550, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


# 忘记密码-密保问题表
class TtUserpassQuestion(models.Model):
    id = models.BigAutoField(primary_key=True)
    question = models.CharField(max_length=10000, db_comment="找回密码的问题")

    class Meta:
        managed = False
        db_table = 'tt_userpass_question'
        db_table_comment = '用户密保问题表'


# 忘记密码-一次性重置令牌表
class TtRetrivepassToken(models.Model):
    id = models.BigAutoField(primary_key=True)
    key = models.CharField(max_length=1000, db_comment="一次性重置密码的key")
    user_id = models.BigIntegerField(blank=True, null=True, db_comment="用户id")
    create_time = models.DateTimeField(null=True, blank=True, db_comment='创建时间')

    class Meta:
        managed = False
        db_table = 'tt_retrivepass_token'
        db_table_comment = '密码找回令牌表'
