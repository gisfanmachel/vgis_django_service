#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2022/10/20 9:53
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : update_complie_package.py
# @Descr   : 获取最新代码，并编译
# @Software: PyCharm
# -*- coding: utf-8 -*-
import json
import os
import py_compile
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
sub_app_name = config["sub_app_name"]
sub_project_name = config['sub_project_name']
sub_sub_project_name = config['sub_sub_project_name']
jmpy_exe_path = config["jmpy_exe_dir_path"]


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


# 为不能pyd编译通过的类增加后缀
def handle_error_complie_files(error_complie_files):
    new_error_complie_files = ""
    error_complie_file_list = error_complie_files.split(",")
    for error_complie_file in error_complie_file_list:
        new_error_complie_file = error_complie_file + "tmp"
        os.rename(error_complie_file, new_error_complie_file)
        new_error_complie_files += new_error_complie_file + ","
    new_error_complie_files = new_error_complie_files.rstrip(",")
    return new_error_complie_files


# 将修改后缀的文件还原后缀
def recovery_error_complie_files(new_error_complie_files):
    recovery_error_complie_files = ""
    new_error_complie_file_list = new_error_complie_files.split(",")
    for new_error_complie_file in new_error_complie_file_list:
        error_complie_file = new_error_complie_file.rstrip("tmp")
        os.rename(new_error_complie_file, error_complie_file)
        recovery_error_complie_files += error_complie_file + ","
    recovery_error_complie_files = recovery_error_complie_files.rstrip(",")
    return recovery_error_complie_files


# 获取在编译目录内的pyd编译不能通过类的文件名连接字符串
def get_new_error_complie_files_in_complie(new_error_complie_files_in_source, source_path_complie, complie_path):
    new_error_complie_files_in_complie = ""
    error_complie_file_list_in_source = new_error_complie_files_in_source.split(",")
    for error_complie_file_in_source in error_complie_file_list_in_source:
        new_error_complie_file = error_complie_file_in_source.replace(source_path_complie, complie_path)
        new_error_complie_files_in_complie += new_error_complie_file + ","
    new_error_complie_files_in_complie = new_error_complie_files_in_complie.rstrip(",")
    return new_error_complie_files_in_complie


# 对跳过pyd编译和不能pyd编译的类进行pyc编译
def pyc_no_complie_files(all_no_complie_files):
    for no_complie_file in all_no_complie_files.split(","):
        py_compile.compile(no_complie_file)
        splitinfo = os.path.split(no_complie_file)
        dir_path = splitinfo[0]
        file_name = splitinfo[1]
        # 删除原来的py文件，将__pycache__里的*.cpython-39.pyc拷贝到上级目录，并重命名，去掉.cpython-39
        python_str = python_version.replace(".", "")
        os.remove(no_complie_file)
        pyc_file = os.path.join(dir_path, "__pycache__",
                                "{}.cpython-{}.pyc".format(file_name.split(".")[0], python_str))
        (file_pre_path, temp_filename) = os.path.split(pyc_file)
        destfile_origin_path = os.path.abspath(os.path.dirname(file_pre_path)) + "\\" + temp_filename
        destfile_rename_path = os.path.abspath(os.path.dirname(file_pre_path)) + "\\" + temp_filename.replace(
            ".cpython-{}".format(python_str), "")
        shutil.move(pyc_file, destfile_origin_path)
        os.rename(destfile_origin_path, destfile_rename_path)
        shutil.rmtree(os.path.join(dir_path, "__pycache__"))


if __name__ == '__main__':

    path = os.path.dirname(os.path.abspath(__file__))

    git_code_wait_second = 5
    source_path = os.path.join(root_path, python_version, "source", project_name)
    # 要编译的源代码目录
    source_path_complie = os.path.join(source_path, project_sub_dir_name, sub_project_name)
    # 编译代码存放目录
    complie_path = os.path.join(root_path, python_version, "complie_pyd", project_name)
    # 不编译的文件及文件夹(这个先编译再还原)/
    # 这个目录结构是最终的编译后的目录结构，不是现在复制源代码的结构
    exclude_complie_files = ""
    exclude_complie_files += os.path.join(complie_path, sub_sub_project_name, "asgi.py") + ","
    exclude_complie_files += os.path.join(complie_path, sub_sub_project_name, "urls.py") + ","
    exclude_complie_files += os.path.join(complie_path, sub_sub_project_name, "wsgi.py") + ","
    exclude_complie_files += os.path.join(complie_path, sub_sub_project_name, "settings.py") + ","
    exclude_complie_files += os.path.join(complie_path, sub_sub_project_name, "log.py") + ","
    exclude_complie_files += os.path.join(complie_path, "manage.py") + ","
    exclude_complie_files += os.path.join(complie_path, "run.py")
    print(exclude_complie_files)

    # 编译通不过的特殊处理
    error_complie_files_in_source = ""
    # error_complie_files_in_source += os.path.join(source_path_complie, sub_app_name, "manage", "xinxiManager.py") + ","
    error_complie_files_in_source += os.path.join(source_path_complie, sub_sub_project_name, "ws", "ws_comsumers.py")

    # git_complie_need_path=os.path.join(complie_need_path, ".git")
    new_error_complie_files_in_source = ""
    new_error_complie_files_in_complie = ""
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
        # 将编译失败的类，重命名后缀
        new_error_complie_files_in_source = handle_error_complie_files(error_complie_files_in_source)
        new_error_complie_files_in_complie = get_new_error_complie_files_in_complie(new_error_complie_files_in_source,
                                                                                    source_path_complie, complie_path)


        if os.path.exists(complie_path):
            print("开始编译代码")
            source_path_complie = source_path_complie.replace("\\", "/")
            complie_path = complie_path.replace("\\", "/")
            exclude_complie_files = exclude_complie_files.replace("\\", "/")
            cmd = "{}\\jmpy -i {} -o {} -I {} -m 0".format(jmpy_exe_path, source_path_complie, complie_path,
                                                           exclude_complie_files)
            print(cmd)
            os.system(cmd)
            print("编译完成")
            # 保留setting.py文件

        # 如果要setting.py被编译，需要手工配置里面setting.py的参数为现场参数，然后在 complie_single_file.py文件里单独编译，再拷贝到相应位置
        delete_blank_pycache_dir(complie_path)
        # 将编译失败的类，还原后缀
        recovery_error_complie_files(new_error_complie_files_in_source)
        recovery_error_complie_files = recovery_error_complie_files(new_error_complie_files_in_complie)
        # 将跳过编译的类，编译失败的类，编译成pyc
        all_no_complie_files = exclude_complie_files + "," + recovery_error_complie_files
        pyc_no_complie_files(all_no_complie_files)



    except Exception as exp:
        if new_error_complie_files_in_source.strip() != "":
            recovery_error_complie_files(new_error_complie_files_in_source)
        if new_error_complie_files_in_complie.strip() != "":
            recovery_error_complie_files(new_error_complie_files_in_complie)
        print(exp)
        print(exp.__traceback__.tb_frame.f_globals["__file__"])  # 发生异常所在的文件
        print(exp.__traceback__.tb_lineno)  # 发生异常所在的行数
        exit(-1)
    finally:
        exit(2)
