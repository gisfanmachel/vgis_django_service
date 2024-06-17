"""
#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
@Project :zwbx_fzcd_service
@File    :uploadUtility.py
@IDE     :PyCharm
@Author  :chenxw
@Date    :2023/8/17 10:19
@Descr:
"""
from my_app import models
from my_project import settings

# 根据上传文件ID获取文件相关信息
def get_file_info_by_upload_file_id(file_id):
    result = models.TtUploadFileData.objects.filter(file_id=file_id)
    if len(result) > 0:
        file_path = settings.UPLOAD_ROOT + "/" + file_id + "." + result[0].file_suffix
        file_suffix = result[0].file_suffix.lower()
        file_name = result[0].file_name
        return file_path, file_name, file_suffix
    else:
        return None, None, None
