"""
#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
@Project :zwbx_fzcd_service
@File    :encryptionUtility.py
@IDE     :PyCharm
@Author  :chenxw
@Date    :2023/8/16 15:43
@Descr:
"""
from vgis_encrption.encrptionTools import FernetEncryption, RSAEncryption, AESEncryption, StringHexMutualConvertion

from my_project.settings import ENCRPTION

# 阶段 4.2：AES 加密对象模块级单例懒加载。
# 原实现每个请求都重建 FernetEncryption + RSAEncryption + AESEncryption 三个对象，
# RSA 解密私钥耗时显著，50 并发时直接占满 CPU。
# 改为：进程首次调用时构建一次，之后复用。
_AES_SINGLETON = None


class encryptionHelper:
    def __int__(self):
        pass

    @staticmethod
    def get_aes_encrytion_object():
        global _AES_SINGLETON
        if _AES_SINGLETON is None:
            fernetEncryption = FernetEncryption(ENCRPTION["key1"].encode())
            rSAEncryption = RSAEncryption(fernetEncryption.decrypt(ENCRPTION["key3"]),
                                          fernetEncryption.decrypt(ENCRPTION["key2"]))
            _AES_SINGLETON = AESEncryption(rSAEncryption.decryption(ENCRPTION["key4"]))
        return _AES_SINGLETON

    @staticmethod
    def two_layers_encrpt_content(content, aESEncryption):
        content_encrpt = aESEncryption.AES_en(content)
        content_encrpt = StringHexMutualConvertion.convert_str_to_hex(content_encrpt)
        return content_encrpt

    @staticmethod
    def two_layers_descrpt_content(content_encrpt, aESEncryption):
        content_descrpt = StringHexMutualConvertion.convert_hex_to_str(content_encrpt)
        content_descrpt = aESEncryption.AES_de(content_descrpt)
        return content_descrpt