#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 雪花ID生成（与 Django 框架模板 my_app/utils/snowflake_id_util.py 保持一致）
# @Software: PyCharm
from toollib.guid import SnowFlake


class SnowflakeIDUtil:
    @staticmethod
    def snowflakeId():
        # worker_id_bits / datacenter_id_bits 置 0，生成较短（15位以内）的 ID
        snow = SnowFlake(worker_id_bits=0, datacenter_id_bits=0)
        return snow.gen_uid()


if __name__ == '__main__':
    for i in range(5):
        print(SnowflakeIDUtil.snowflakeId())
