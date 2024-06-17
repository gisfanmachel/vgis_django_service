#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2023/6/28 11:07
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : init_dir.py
# @Descr   : 
# @Software: PyCharm
import json
import os

with open('config.json', 'r') as configfile:
    config = json.load(configfile)
# 获取配置项的值
python_version = config['python_version']
all_versions = config['all_versions']
root_path = config['root_path']
project_name = config['project_name']

python_version_list = all_versions
# https://106.13.81.105:8443/r/django_service.git
for python_version in python_version_list:
    dir = os.path.join(root_path, python_version, "source")
    if not os.path.exists(dir):
        os.makedirs(dir)
    dir = os.path.join(root_path, python_version, "complie_pyc")
    if not os.path.exists(dir):
        os.makedirs(dir)
    dir = os.path.join(root_path, python_version, "complie_pyc", project_name)
    if not os.path.exists(dir):
        os.makedirs(dir)
    dir = os.path.join(root_path, python_version, "complie_pyd")
    if not os.path.exists(dir):
        os.makedirs(dir)
    dir = os.path.join(root_path, python_version, "complie_pyd", project_name)
    if not os.path.exists(dir):
        os.makedirs(dir)
