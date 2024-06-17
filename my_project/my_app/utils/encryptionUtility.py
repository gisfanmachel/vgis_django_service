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


class encryptionHelper:
    def __int__(self):
        pass

    @staticmethod
    def get_aes_encrytion_object():
        fernetEncryption = FernetEncryption(ENCRPTION["key1"].encode())
        rSAEncryption = RSAEncryption(fernetEncryption.decrypt(ENCRPTION["key3"]), fernetEncryption.decrypt(ENCRPTION["key2"]))
        aESEncryption = AESEncryption(rSAEncryption.decryption(ENCRPTION["key4"]))
        return aESEncryption

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