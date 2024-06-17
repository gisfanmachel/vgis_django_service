#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/6/10 15:08
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : alogirthmUtility.py
# @Descr   : 数据库操作帮助类
# @Software: PyCharm
from my_project import settings
import psycopg2


class DatabaseHelper:

    def __init__(self):
        pass

    # @staticmethod
    # def get_ksh_database_conection(logger):
    #     HOST = settings.DATABASES["ksh"]["HOST"]
    #     PORT = settings.DATABASES["ksh"]["PORT"]
    #     USER = settings.DATABASES["ksh"]["USER"]
    #     PASSWORD = settings.DATABASES["ksh"]["PASSWORD"]
    #     DATABASE = settings.DATABASES["ksh"]["NAME"]
    #     try:
    #         conn = psycopg2.connect(database=DATABASE, user=USER, password=PASSWORD,
    #                                 host=HOST, port=PORT)
    #         sql = "select count(*) from pg_tables;"
    #         cursor = conn.cursor()
    #         cursor.execute(sql)
    #         records = cursor.fetchall()
    #         logger.info("建立可视化数据连接成功")
    #     except Exception as exp:
    #         conn = None
    #         logger.error("建立可视化数据库连接失败，可能原因：{}".format(str(exp)))
    #     # 需要判断是否连接可视化数据库成功
    #     return conn
    #
    # @staticmethod
    # def close_ksh_database_conection(conn, logger):
    #     try:
    #         logger.info("关闭可视化数据库连接")
    #         conn.close()
    #     except Exception as exp:
    #         logger.error("关闭可视化数据库连接失败，可能原因：{}".format(str(exp)))


