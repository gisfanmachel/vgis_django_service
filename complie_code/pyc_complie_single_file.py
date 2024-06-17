#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/10/20 13:44
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : complie_single_file.py
# @Descr   : 编译单个文件
# @Software: PyCharm
import json
import os
import py_compile
import shutil

if __name__ == '__main__':
    with open('config.json', 'r') as configfile:
        config = json.load(configfile)
    root_path = config['root_path']
    project_name = config['project_name']
    python_v = config['python_version']
    project_sub_dir_name = config['project_sub_dir_name']
    sub_project_name = config['sub_project_name']
    sub_sub_project_name = config['sub_sub_project_name']

    dest_settingfile = os.path.join(root_path, "complie_pyc", project_name, project_sub_dir_name, sub_project_name,
                                    sub_sub_project_name,
                                    "settings.py")
    if os.path.exists(dest_settingfile):
        # 编译单个文件setting.py
        py_compile.compile(dest_settingfile)

        # 删除原来的setting.py，将__pycache__里的settings.cpython-39.pyc拷贝到上级目录，并重命名，去掉.cpython-39
        python_str = python_v.replace(".", "")
        os.remove(dest_settingfile)
        dest_settingfile2 = os.path.join(root_path, "complie_pyc", project_name, project_sub_dir_name, sub_project_name,
                                         sub_sub_project_name, "__pycache__",
                                         "settings.cpython-{}.pyc".format(python_str))
        (file_pre_path, temp_filename) = os.path.split(dest_settingfile2)
        destfile_origin_path = os.path.abspath(os.path.dirname(file_pre_path)) + "\\" + temp_filename
        destfile_rename_path = os.path.abspath(os.path.dirname(file_pre_path)) + "\\" + temp_filename.replace(
            ".cpython-{}".format(python_str), "")
        shutil.move(dest_settingfile2, destfile_origin_path)
        os.rename(destfile_origin_path, destfile_rename_path)
        shutil.rmtree(
            os.path.join(root_path, "complie_pyc", project_name, project_sub_dir_name, sub_project_name, sub_sub_project_name,
            "__pycache__"))
