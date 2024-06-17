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


    source_dir_path = os.path.join(root_path, python_v, "source", project_name, project_name, project_sub_dir_name, sub_project_name)
    dist_dir_path = os.path.join(root_path, python_v, "source", project_name, project_name, project_sub_dir_name, sub_project_name, "dist")
    source_settingfile = os.path.join(source_dir_path,
                                      "settings.py")
    if os.path.exists(source_settingfile):

        if os.path.exists(dist_dir_path):
            shutil.rmtree(dist_dir_path)
        # 编译单个文件setting.py
        os.system("jmpy -i {}".format(source_settingfile))
        # 删除原来的setting.py，将dist里的settings.pyd拷贝到上级目录
        # os.remove(dest_settingfile)
        dest_settingfile2 = os.path.join(dist_dir_path,
                                         "settings.pyd")
        dest_settingfile3 = os.path.join(source_dir_path,
                                         "settings.pyd")

        (file_pre_path, temp_filename) = os.path.split(source_settingfile)
        if os.path.exists(dest_settingfile3):
            os.remove(dest_settingfile3)
        shutil.move(dest_settingfile2, file_pre_path)
        shutil.rmtree(dist_dir_path)
