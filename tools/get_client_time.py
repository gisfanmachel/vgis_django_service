#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2023/8/9 10:03
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : get_client_time.py
# @Descr   : 
# @Software: PyCharm
import time

# 服务端代码获取方式
get_time = int(time.time() * 1000)
print("当前时间：{}".format(get_time))

strtime = "2022-05-06 00:00:00"
time_obj=time.strptime(strtime, "%Y-%m-%d %H:%M:%S")
get_time=int(time.mktime(time_obj)*1000)
print("指定时间：{}".format(get_time))

# 客户端代码获取方式
# # current time
# # var d = new Date()
# # ct=d.getTime()
#
# # set time
# # var d = new Date("2023-5-12")
# # ct=d.getTime()