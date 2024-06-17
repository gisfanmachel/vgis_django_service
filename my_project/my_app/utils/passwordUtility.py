#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    :  2023/1/4 11:09
# @Author  : chenxw
# @Email   : gisfanmachel@gmail.com
# @File    : passwordUtility.py
# @Descr   :
# @Software: PyCharm
from django.contrib.auth.hashers import make_password, check_password


class PasswordHelper:
    def __init__(self):
        pass

    # django加密的用户密码
    # 每次产生的密码均不同
    # make_password(原始密码,固定字串)：产生相同密码。
    # make_password(原始密码，固定字串，加密方式) pbkdf2_sha256
    @staticmethod
    def getEncrptPassword(password):
        upwd = make_password(password)
        return upwd

    # 核对加密密码
    @staticmethod
    def checkPassword(password, encPass):
        check = check_password(password, encPass)
        return check

    # 无法解密


if __name__ == '__main__':
    import os

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project.settings')
    passwd = "admin"
    encPass = PasswordHelper.getEncrptPassword(passwd)
    print(encPass)
    check = PasswordHelper.checkPassword(passwd, encPass)
    print(check)
