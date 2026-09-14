# -*- coding: utf-8 -*-
# sys_manage 模块的模型：系统管理相关的全部表
#   配置/部门/日志/菜单/OSS/角色/角色菜单/用户/用户角色/用户Token/参数/字典/消息
#
# 约定：managed = False + 显式 db_table（表由 database/ 下 SQL 手工维护，不走迁移）
from django.db import models


# 业务数据相关的模型

# 配置参数表
class SysConfig(models.Model):
    id = models.BigAutoField(primary_key=True)
    param_key = models.CharField(max_length=50, blank=True, null=True)
    param_value = models.CharField(max_length=2000, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    remark = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_config'


# 部门表
class SysDepartment(models.Model):
    department_id = models.BigAutoField(primary_key=True)
    department_name = models.CharField(max_length=128, blank=True, null=True)
    parent_id = models.BigIntegerField(blank=True, null=True)
    state = models.CharField(max_length=1, blank=True, null=True)
    state_date = models.DateField(blank=True, null=True)
    order_num = models.BigIntegerField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)
    del_flag = models.IntegerField(blank=True, null=True)
    master = models.CharField(max_length=255, blank=True, null=True)
    tel = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_department'


# 日志表
class SysLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, blank=True, null=True)
    operation = models.CharField(max_length=50, blank=True, null=True)
    method = models.CharField(max_length=200, blank=True, null=True)
    params = models.CharField(max_length=5000, blank=True, null=True)
    time = models.FloatField()
    ip = models.CharField(max_length=64, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    error_info = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_log'


# 菜单表
class SysMenu(models.Model):
    menu_id = models.BigAutoField(primary_key=True)
    parent_id = models.BigIntegerField(blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    perms = models.CharField(max_length=500, blank=True, null=True)
    type = models.IntegerField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    order_num = models.IntegerField(blank=True, null=True)
    is_show = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_menu'


class SysOss(models.Model):
    id = models.BigAutoField(primary_key=True)
    url = models.CharField(max_length=200, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_oss'


# 角色表
class SysRole(models.Model):
    role_id = models.BigAutoField(primary_key=True)
    role_name = models.CharField(max_length=100, blank=True, null=True)
    remark = models.CharField(max_length=100, blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_role'


# 用户角色菜单表
class SysRoleMenu(models.Model):
    id = models.BigAutoField(primary_key=True)
    role_id = models.BigIntegerField(blank=True, null=True)
    menu_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_role_menu'


# 用户表-未用
class SysUser(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=100, blank=True, null=True)
    salt = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    mobile = models.CharField(max_length=100, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)
    department_id = models.BigIntegerField(blank=True, null=True)
    sex = models.CharField(max_length=255, blank=True, null=True)
    fullname = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_user'





# 用户角色表
class SysUserRole(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.BigIntegerField(blank=True, null=True)
    role_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_user_role'


# 用户登录token表
class SysUserToken(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    token = models.CharField(max_length=100)
    expire_time = models.DateTimeField(blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_user_token'





# 说明：原 WorldBorder 模型（GeoDjango 示例，tm_world_border 表）已移除。
# 它与配套的 my_app/load.py 都来自 Django GIS 示例代码，MYDB 与 PNT 中均无该表，
# 框架从未使用，属残留死代码。


class SysParam(models.Model):
    id = models.BigAutoField(primary_key=True, db_comment="id")
    param_en_key = models.CharField(max_length=200, db_comment="参数键英文名称")
    param_cn_key = models.CharField(max_length=200, db_comment="参数键中文名称")
    param_value = models.CharField(max_length=255, db_comment="参数键值")
    create_time = models.DateTimeField(blank=True, null=True, db_comment='创建时间')
    create_user_id = models.BigIntegerField(blank=True, null=True, db_comment='创建人')
    update_time = models.DateTimeField(blank=True, null=True, db_comment='更新时间')
    update_user_id = models.BigIntegerField(blank=True, null=True, db_comment='更新人id')

    class Meta:
        managed = False
        db_table = 'sys_param'
        db_table_comment = '系统参数表'

class SysDict(models.Model):
    id = models.BigAutoField(primary_key=True, db_comment="id")
    dict_catelog_id = models.BigIntegerField(blank=True, null=True)
    type_value = models.CharField(max_length=200, db_comment="参数键英文名称")
    memo_value = models.CharField(max_length=200, db_comment="参数键中文名称")
    param_value = models.CharField(max_length=255, db_comment="参数键值")
    create_time = models.DateTimeField(blank=True, null=True, db_comment='创建时间')
    create_user_id = models.BigIntegerField(blank=True, null=True, db_comment='创建人')
    update_time = models.DateTimeField(blank=True, null=True, db_comment='更新时间')
    update_user_id = models.BigIntegerField(blank=True, null=True, db_comment='更新人id')

    class Meta:
        managed = False
        db_table = 'sys_dict'
        db_table_comment = '系统字典表'

class SysMessage(models.Model):
    id = models.BigAutoField(primary_key=True, db_comment="id")
    user_id = models.BigIntegerField(blank=True, null=True,db_comment="用户id")
    message = models.CharField(max_length=2550, db_comment="消息")
    # sys_message 的按时间检索接口（sysManager.sql_search_message）依赖该列，
    # 缺列会导致该接口 SQL 报错，故表与模型一并补上。
    create_time = models.DateTimeField(blank=True, null=True, db_comment="创建时间")

    class Meta:
        managed = False
        db_table = 'sys_message'
        db_table_comment = '系统消息表'
