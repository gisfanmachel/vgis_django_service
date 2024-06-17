#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2023/8/9 10:04
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : kill_linux_port.py
# @Descr   : 
# @Software: PyCharm

import os


# 获取端口的pid
# lsof -i:10843.
# 杀死pid对应的进程
# kill -9 9688



port = 28611
cmd = "lsof -i:{}".format(port)
output = os.popen(cmd, "r")
info = output.readlines()
# 获取端口的PID
pid_list = []
if info is not None:
    row = 0
    # 从第二行开始读
    for line in info:
        if row > 0:
            print(line)
            if line != "":
                pid = line.split(" ")[1]
                print(pid)
                if pid not in pid_list:
                    pid_list.append(pid)
        row += 1

# 杀死PID对应的进程
for pid in pid_list:
    cmd = "kill -9 {}".format(pid)
    output = os.popen(cmd, "r")
    info = output.readlines()
    print(info)


