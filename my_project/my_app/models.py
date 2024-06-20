from django.contrib.gis.db import models
# Create your models here.
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.


# Create your models here.
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
    sex = models.CharField(unique=True, max_length=255)
    mobile = models.CharField(unique=True, max_length=100)
    status = models.IntegerField(blank=True, null=True)
    create_user_id = models.BigIntegerField(blank=True, null=True)
    create_time = models.DateTimeField(null=True, blank=True)
    modify_user_id = models.BigIntegerField(blank=True, null=True)
    modify_time = models.DateTimeField(null=True, blank=True)
    login_error_attempts = models.SmallIntegerField(default=0)
    login_locked_until = models.DateTimeField(null=True, blank=True)

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


# Django管理相关的模型
class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

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





# 上传文件表
class TtUploadFileData(models.Model):
    id = models.BigAutoField(primary_key=True)
    upload_user_id = models.BigIntegerField(blank=True, null=True)
    file_size = models.DecimalField(max_digits=24, decimal_places=0, blank=True, null=True)
    file_id = models.CharField(max_length=255, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    upload_time = models.DateTimeField(blank=True, null=True)
    file_suffix = models.CharField(max_length=255, blank=True, null=True)
    path = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tt_upload_file_data'


# 行政区划表
class TmDdistrict(models.Model):
    id = models.BigAutoField(primary_key=True)
    dis_name = models.CharField(max_length=255, blank=True, null=True)
    dis_code = models.IntegerField(blank=True, null=True)
    parent_code = models.IntegerField(blank=True, null=True)
    type = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tm_district'


class WorldBorder(models.Model):
    # Regular Django fields corresponding to the attributes in the
    # world borders shapefile.
    name = models.CharField(max_length=50)
    area = models.IntegerField()
    pop2005 = models.IntegerField("Population 2005")
    fips = models.CharField("FIPS Code", max_length=2, null=True)
    iso2 = models.CharField("2 Digit ISO", max_length=2)
    iso3 = models.CharField("3 Digit ISO", max_length=3)
    un = models.IntegerField("United Nations Code")
    region = models.IntegerField("Region Code")
    subregion = models.IntegerField("Sub-Region Code")
    lon = models.FloatField()
    lat = models.FloatField()
    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()
    # Returns the string representation of the model.
    class Meta:
        app_label = 't231_app'
        managed = False
        db_table = 'tm_world_border'


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

    class Meta:
        managed = False
        db_table = 'sys_message'
        db_table_comment = '系统消息表'