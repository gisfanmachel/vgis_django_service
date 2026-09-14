# -*- coding: utf-8 -*-
# common 模块的模型：行政区划 + 上传文件
#
# 约定：managed = False + 显式 db_table（表由 database/ 下 SQL 手工维护，不走迁移）
from django.db import models


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
