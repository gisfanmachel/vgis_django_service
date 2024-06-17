#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/6/14 13:50
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : utils.py
# @Descr   : 
# @Software: PyCharm
import datetime
import time
class TimeUtil:
    @staticmethod
    def string2time_stamp(str_value):

        try:
            d = datetime.datetime.strptime(str_value, "%Y-%m-%d %H:%M:%S.%f")
            t = d.timetuple()
            time_stamp = int(time.mktime(t))
            time_stamp = float(str(time_stamp) + str("%06d" % d.microsecond)) / 1000000
            return time_stamp
        except ValueError as e:
            print(e)
            d = datetime.datetime.strptime(str_value, "%Y-%m-%d %H:%M:%S")
            t = d.timetuple()
            time_stamp = int(time.mktime(t))
            time_stamp = float(str(time_stamp) + str("%06d" % d.microsecond)) / 1000000
            return time_stamp
