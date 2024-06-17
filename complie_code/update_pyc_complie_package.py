#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/10/20 9:53
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : update_complie_package.py
# @Descr   : 获取最新代码，并编译
# @Software: PyCharm
# -*- coding: utf-8 -*-
import compileall
import json
import os
import shutil
import subprocess
import time

with open('config.json', 'r') as configfile:
    config = json.load(configfile)
# 获取配置项的值
python_version = config['python_version']
root_path = config['root_path']
project_name = config['project_name']
project_sub_dir_name = config['project_sub_dir_name']
sub_project_name = config['sub_project_name']
sub_sub_project_name = config['sub_sub_project_name']


# 对目录及子目录的py文件进行编译生成pyc文件
def complie_py_file(dir, python_v):
    # 对目录下的所有py文件进行编译，包括子目录
    compileall.compile_dir(dir)
    # 删除py，重命名pyc文件并移动到上级目录
    handle_pyc_file_in_dir(dir, python_v)
    # 删除空白的__pycache__目录
    delete_blank_pycache_dir(dir)


# 基于pycharm自动编译目录进行处理
def posthandle_py_file(dir, python_v):
    # 删除py，重命名pyc文件并移动到上级目录
    handle_pyc_file_in_dir(dir, python_v)
    # 删除空白的__pycache__目录
    delete_blank_pycache_dir(dir)


# 删除原来的py文件，将pyc文件移动到上级目录，并重命名
def handle_pyc_file_in_dir(filepath, python_v):
    python_str = python_v.replace(".", "")
    # 遍历filepath下所有文件，包括子目录
    files = os.listdir(filepath)
    for file in files:
        file_path = os.path.join(filepath, file)
        if os.path.isdir(file_path):
            handle_pyc_file_in_dir(file_path, python_v)
        else:
            # print(file_path)
            (file_pre_path, temp_filename) = os.path.split(file_path)
            (shot_name, file_ext) = os.path.splitext(file_path)
            if file_ext == ".py":
                os.remove(file_path)
            if file_ext == ".pyc" and (".cpython-" + python_str in temp_filename):
                destfile_origin_path = os.path.abspath(os.path.dirname(file_pre_path)) + "\\" + temp_filename
                destfile_rename_path = os.path.abspath(os.path.dirname(file_pre_path)) + "\\" + temp_filename.replace(
                    ".cpython-" + python_str, "")
                shutil.move(file_path, destfile_origin_path)
                os.rename(destfile_origin_path, destfile_rename_path)


# 删除空白的__pycache__文件夹
def delete_blank_pycache_dir(filepath):
    files = os.listdir(filepath)
    for file in files:
        file_path = os.path.join(filepath, file)
        if os.path.isdir(file_path):
            if file == "__pycache__":
                os.rmdir(file_path)
            else:
                delete_blank_pycache_dir(file_path)


if __name__ == '__main__':

    path = os.path.dirname(os.path.abspath(__file__))

    git_code_wait_second = 5
    source_path = os.path.join(root_path, python_version, "source", project_name)
    complie_path = os.path.join(root_path, python_version, "complie_pyc", project_name)
    # git_complie_need_path=os.path.join(complie_need_path, ".git")
    try:

        # 第一次先线下手动拉取代码，后面用程序做更新拉取代码
        # source_path这个是线下克隆好的代码
        os.chdir(source_path)
        print(os.getcwd())
        print("从git上更新获取最新代码")
        # 执行git pull命令获取最新代码
        subprocess.Popen("git pull origin master", stdout=subprocess.PIPE, shell=True)
        # 执行等待
        time.sleep(git_code_wait_second)
        # 将最新代码拷贝到complie目录（需要先清空）
        if os.path.exists(complie_path):
            print("清空编译目录")
            shutil.rmtree(complie_path)
        print("将获取到的最新代码拷贝到编译目录")
        Ignore_Pattern = '*.*'
        shutil.copytree(source_path, complie_path, ignore=shutil.ignore_patterns(".git"))
        if os.path.exists(complie_path):
            print("开始编译代码")
            complie_py_file(complie_path, python_version)
            print("编译完成")
            # 保留setting.py文件
            souce_settingfile = os.path.join(source_path, project_sub_dir_name, sub_project_name, sub_sub_project_name,
                                             "settings.py")
            dest_settingfile = os.path.join(complie_path, project_sub_dir_name, sub_project_name, sub_sub_project_name,
                                            "settings.py")
            shutil.copyfile(souce_settingfile, dest_settingfile)
            os.remove(os.path.join(complie_path, project_sub_dir_name, sub_project_name, sub_sub_project_name, "settings.pyc"))
        # 如果要setting.py被编译，需要手工配置里面setting.py的参数为现场参数，然后在 complie_single_file.py文件里单独编译，再拷贝到相应位置


    except Exception as exp:
        print(exp)
        print(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
        print(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
        exit(-1)
    finally:
        exit(2)
