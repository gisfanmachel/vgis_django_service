from django.contrib.gis.db import models
# from django.db import models
# Create your models here.
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


# Create your models here.
# Django管理相关的模型
class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    # 用字符串惰性引用：AuthUser 已搬到 my_app.module.user_manage.models，
    # 而本文件的模块聚合 import 在末尾，直接引用会在类定义时报 NameError。
    # Django 会在 app registry 装配完成后解析字符串引用。
    user = models.ForeignKey('AuthUser', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


# ===========================================================================
# 分模块模型的显式导入
#
# my_app/module/<模块>/models.py 里定义的模型**不会**被 Django 自动发现：
# 模块包不是 Django app（全项目只有 my_app 一个 app），而 apps.populate()
# 只会自动 import my_app.models，不递归子包。因此必须在这里显式导入，
# 否则模型不进 app registry，ORM 用不了。
#
# app_label 不用手写：Django 按最长前缀匹配，my_app.module.demo.models
# 会自动归到 my_app 这个 app。
#
# 这里不采用"靠 URLconf 的 import 链顺带注册"的做法 —— 那样一旦某模块
# 没被 include，它的模型会静默消失，排查成本很高。
#
# 注意：本块必须放在文件末尾（所有扁平模型定义之后），
# 且下面的模型若要引用上面模块里的模型，请用字符串惰性引用（如 'AuthUser'）。
#
# 新增模块时在下面加一行即可。
# ===========================================================================
from my_app.module.common.models import *        # noqa: F401,F403,E402
from my_app.module.sys_manage.models import *    # noqa: F401,F403,E402
from my_app.module.user_manage.models import *   # noqa: F401,F403,E402
from my_app.module.demo.models import *          # noqa: F401,F403,E402