# -*- coding: utf-8 -*-
# demo 模块的模型
#
# 约定（各模块一致）：
#   - 一律 managed = False + 显式 db_table：表由 database/ 下的 SQL 手工建，
#     Django 只做 ORM 映射，不生成/执行迁移
#   - 模块包不是 Django app，app_label 由 Django 按最长前缀匹配自动归到 my_app
#   - 但 Django 不会自动 import my_app.module.<x>.models，
#     所以必须由 my_app/models.py 显式 import（见那个文件的说明）
from django.db import models


class TtDemoItem(models.Model):
    """演示数据表：框架 CRUD / 分页 / Excel 导入导出的模板载体"""

    id = models.BigAutoField(primary_key=True)
    # item_code 有唯一索引，是 Excel 导入 upsert 的依据
    item_code = models.CharField(max_length=64, db_comment="业务编码（唯一）")
    item_name = models.CharField(max_length=255, db_comment="名称")
    # 下面两个外键指向既有系统表，用于演示多表联合查询
    category_id = models.BigIntegerField(blank=True, null=True, db_comment="类别id → sys_dict_catelog.id")
    department_id = models.BigIntegerField(blank=True, null=True, db_comment="部门id → sys_department.department_id")
    amount = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True, db_comment="金额")
    item_status = models.SmallIntegerField(blank=True, null=True, default=1, db_comment="状态 1启用/0停用")
    occur_date = models.DateField(blank=True, null=True, db_comment="发生日期")
    remark = models.CharField(max_length=500, blank=True, null=True, db_comment="备注")
    create_user_id = models.BigIntegerField(blank=True, null=True, db_comment="创建人id")
    create_time = models.DateTimeField(blank=True, null=True, db_comment="创建时间")
    modify_user_id = models.BigIntegerField(blank=True, null=True, db_comment="修改人id")
    modify_time = models.DateTimeField(blank=True, null=True, db_comment="修改时间")

    class Meta:
        managed = False
        db_table = "tt_demo_item"
        db_table_comment = "demo 模块演示表"
