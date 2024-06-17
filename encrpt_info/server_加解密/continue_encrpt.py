"""
#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
@Project :django初始化框架
@File    :continue_encrpt.py
@IDE     :PyCharm
@Author  :chenxw
@Date    :2023/7/31 13:59
@Descr:  综合加解密
"""
from vgis_encrption.encrptionTools import AESEncryption, RSAEncryption, FernetEncryption, StringHexMutualConvertion


# 客户端请求加密
# AES加密、字符串转十六进制
def two_layers_encrpt_content(client_request, aes_key):
    # 测试AES加解密
    aESEncryption = AESEncryption(aes_key)
    print("客户端原始字符串:{}".format(client_request))
    client_request_encrpt = aESEncryption.AES_en(client_request)
    print("客户端加密后字符串:{}".format(client_request_encrpt))
    data = aESEncryption.AES_de(client_request_encrpt)
    print("解密后客户端字符串:{}".format(data))
    client_request_encrpt = StringHexMutualConvertion.convert_str_to_hex(client_request_encrpt)
    return client_request_encrpt


if __name__ == "__main__":


    print(
        "---------------------------------------------------------------------------------------------------------------------")
    # 项目中用到的加解密
    # 第一次生成key使用
    # fernet_key = Fernet.generate_key()
    fernet_key = b'uNl-LfGm6NKDQ1Uz9azZIEEzYnaLz68gz0UzaQvYFIY='
    print("生成新的fernet_key:{}".format(fernet_key))
    # 从密钥工具获取该项目的RSA的公钥，私钥
    rsa_public_key = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC15al8c+N5ZCEd89RwaxaZrwXQpRMmZ3ca2/pM3v1yZt4zioDe9nkmlO6nniMzid1aBAuLGvZ96cWbet/WckbWA2G0IAVqd0mosYHMxv/fIZjMk1JZQa0Ec4HRqxwkf2lVl4Dn4UdNFq17pV3YjXTkVsX8v4xp6XMlTL207NLRewIDAQAB"
    rsa_private_key = "MIICeAIBADANBgkqhkiG9w0BAQEFAASCAmIwggJeAgEAAoGBALXlqXxz43lkIR3z1HBrFpmvBdClEyZndxrb+kze/XJm3jOKgN72eSaU7qeeIzOJ3VoEC4sa9n3pxZt639ZyRtYDYbQgBWp3SaixgczG/98hmMyTUllBrQRzgdGrHCR/aVWXgOfhR00WrXulXdiNdORWxfy/jGnpcyVMvbTs0tF7AgMBAAECgYBkyrUG1ESZMGW1bjYqcPyd/kDvo3kgD7cM+BYTYID6UowP7VCJu/PX8DDqSpNg7KTuS02GMFOj49Tu2cCM2NfssT8Lj5BKWud0zzEkXa7tNieH24hOCxJ6/P5E/jFa+YUEWanl48K9vx9ri9o82jKmzwlYQAe/1+gdO2n4AVkpuQJBAOf0HJ6oTlWeUgNiAi/Iz6GbIeCb/xY+1kDHyRtZHalmQTvFvK4YEw3kxphG5W+R7rEqYmwLdchK5wwuqcLMxP0CQQDIwRYsFntz2IcHEv/xJk4HH4oJoz6E5eaF9R1jreX8jSLuhtRzu01km9NrC8Op+e8AYdoV63/k17PVOtQDpTXXAkEAqXJHRhAlyZ4yw43hkw7bv28YvIC5RIL6+a/5ViUv6gRtO0EkqPmlUc0C11NTYMH24S3ZYJyumnc9ekTMdyYn8QJBAK006sxfGWR6DQYtfmWxhuDedVqbXfWL5bjuIs093JBptRnXerXfhIapa1+QZuDgozTRODhxV4c6FA6FEyeSA0ECQQDi90iUV4Igmx381NSvKx9/XOyZe7R7AikoD+f0Of7sCbXyN0pMtbsIu3NB5W1yReM8t759mbbX0uZhl4X8qf3Q"
    # 设置aes的密钥# aes密钥长度在16位
    aes_key = "myaovgis0713wxgz"

    fernetEncryption = FernetEncryption(fernet_key)
    # RSA的公钥和私钥，用fernet加密
    rsa_public_key_encrypt = fernetEncryption.encrypt(rsa_public_key)
    print("加密后的rsa公钥:{}".format(rsa_public_key_encrypt))
    rsa_private_key_encrypt = fernetEncryption.encrypt(rsa_private_key)
    print("加密后的rsa私钥:{}".format(rsa_private_key_encrypt))
    rSAEncryption = RSAEncryption(rsa_private_key, rsa_public_key)
    # AES的密钥，用RSA加密
    aes_key_encrypt = rSAEncryption.encryption(aes_key)
    print("加密后的aes密钥:{}".format(aes_key_encrypt))

    # 服务端 修改配置文件里的四个key
    # key1:fernet_key(fernet密钥),去掉b
    # key2:public_key(rsa公钥,从发布license的密钥管理工具获取)，用fernet加密
    # key3:private_key(rsa私钥,从发布license的密钥管理工具获取)，用fernet加密
    # key4:aes_key(aes密钥)，用ras加密

    # 客户端修改key
    # input.html 里的pk1用加密后的aes密钥, pk2用rsa的私钥

    print(
        "---------------------------------------------------------------------------------------------------------------------")
    # 对postman客户端提交内容进行加密
    # 服务端加密：AES加密、不转十六进制了，因为服务端返回极加密结果在POSTMAN没法写脚本解密存TOKEN
    # 客户端解密： AES解密
    # 客户端加密：AES加密、字符串转十六进制，主要是为解决get请求的url会自动进行特殊字符的转义
    # 服务端解密：十六进制转字符串---AES解密
    data = "{\"username\":\"chenxw\",\"password\":\"admin\",\"verifcation\":\"2418H1\",\"client_time\":1684489627117}"
    client_request_encrpt = two_layers_encrpt_content(data, aes_key)
    print("综合加密后的客户端请求内容:{}".format(client_request_encrpt))
