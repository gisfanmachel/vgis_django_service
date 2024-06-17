"""
#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
@Project :django初始化框架
@File    :generatorKey.py
@IDE     :PyCharm
@Author  :chenxw
@Date    :2024/4/28 17:51
@Descr:   生成setting.py配置的几个key
# # key1:fernet_key(fernet密钥),去掉b
# # key2:public_key(rsa公钥,从发布license的密钥管理工具获取)，用fernet加密
# # key3:private_key(rsa私钥,从发布license的密钥管理工具获取)，用fernet加密
# # key4:aes_key(aes密钥)，用ras加密
"""
from cryptography.fernet import Fernet
from vgis_encrption.encrptionTools import FernetEncryption, RSAEncryption, AESEncryption, StringHexMutualConvertion

from my_project.settings import WINDOWS_LICENSE_PATH, LINUX_LICENSE_PATH


def __read_lic_file(lic_path):
    f = open(lic_path, encoding="utf-8")
    line = f.readline()
    row = 0
    text_encrypted_base64 = ""
    private_key = ""
    is_over_half = False
    while line:
        row += 1
        if row > 6 and "------" not in line and is_over_half is False:
            text_encrypted_base64 += line.rstrip("\n")
        if row > 6 and "------" in line:
            is_over_half = True
        if row > 6 and is_over_half is True and "------" not in line and "#######" not in line:
            private_key += line.rstrip("\n")
        if row > 6 and is_over_half is True and "#######" in line:
            break
        line = f.readline()
    f.close()
    # private_key = "-----BEGIN RSA PRIVATE KEY-----\n" + private_key + "\n-----END RSA PRIVATE KEY-----"
    return text_encrypted_base64, private_key




# key1: Fernet key（未加密）
fernet_key = Fernet.generate_key()
key1 = fernet_key.decode()
# key2: RSA public key（Fernet加密）
# key3: RSA private key（Fernet加密）
# rsa公钥从密钥工具页面获取
rsa_public_key = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC15al8c+N5ZCEd89RwaxaZrwXQpRMmZ3ca2/pM3v1yZt4zioDe9nkmlO6nniMzid1aBAuLGvZ96cWbet/WckbWA2G0IAVqd0mosYHMxv/fIZjMk1JZQa0Ec4HRqxwkf2lVl4Dn4UdNFq17pV3YjXTkVsX8v4xp6XMlTL207NLRewIDAQAB"
# rsa_public_key = "-----BEGIN PUBLIC KEY-----\n" + rsa_public_key + "\n-----ND PUBLIC KEY-----"
# import platform
# platformType = platform.system().lower()
# lic_path = WINDOWS_LICENSE_PATH if platformType == 'windows' else LINUX_LICENSE_PATH
# # rsa私钥从license文件中读取，也可以从密钥工具页面获取
# _, rsa_private_key = __read_lic_file(lic_path)
rsa_private_key="MIICdwIBADANBgkqhkiG9w0BAQEFAASCAmEwggJdAgEAAoGBAK/oyFhlBavNXgetvALOp/CGw6bX5SJvMpTYR+przR+Yp2bQSJkt4rnQ3BWMoehmmo/Q023z7pyL3Wt8cgascVtenRsCFmkNKMdUK/KaxlzYdg+cUMxhRzW0WfatXKSwhsXM8IL+3DIJ2nU7W9YhPqLdSodCIeHm8fCTa1hJN2HhAgMBAAECgYAt5gNAbTuJlFBQmJhR8zIGpGMwiWyUC4ebJsO8+tvOvroPLZGDxmE+Mqz6QnOMfBkgJVDFg7xixGvFu/bUnvIEgnDNaXq11W9bjEAIi9wcMI5CGIGQjAQYTxVlhdNUXg5kU8/Usa2sckpfRDzN9lRfftBtUn0Kd6PoGXry7tHAAQJBANXCzMojXJnFHshqNrYH6zBT69rgHQyYgF/Sjy9ga2Vwj56apYhas9Kp0K/dgTX3R1FQY/gDEQsDwaktr4CakGECQQDSqz1bdU316p67IWpGSJfpfS6c6qafxCQ+8gwAoyUXi8lH190UvcNw4ARRleSIE9SzzOySmnXETQq5kffsLEGBAkEAir0sfeYFrCgsmpeVewAYvf06D412TT6N06OuG2nRSr2L+b0VwzJblFdzgzGZM5WTTEuJFuemoCeIAm4MgsPPAQJARF2157xFtIyTPn81keF1CxzIx7uOn0Jz0MmUA5DuNJn0lBAFevmqNzM7s45FP7PPzxmtnFXr6exmkppALrCeAQJBAJoE+ddoWz9LDASEvwfitmaN7jiYsgnml2sBEl6JoNwkvlhLt8FJUOdfJKkGGsr3x64NC2TWTeg4OiLhT+Si950="
fernetEncryption = FernetEncryption(key1)
key2 = fernetEncryption.encrypt(rsa_public_key)
key3 = fernetEncryption.encrypt(rsa_private_key)
# key4: AES key（RSA加密）
rSAEncryption = RSAEncryption(rsa_private_key, rsa_public_key)
# 定义aeskey,不要超过一定长度16
aes_key = "miyaovgis0704gis"
key4 = rSAEncryption.encryption(aes_key)

print("key1='{}'".format(key1))
print("key2='{}'".format(key2))
print("key3='{}'".format(key3))
print("key4='{}'".format(key4))



