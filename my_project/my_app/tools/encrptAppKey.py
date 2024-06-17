"""
#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
@Project :django初始化框架
@File    :encrptAppKey.py
@IDE     :PyCharm
@Author  :chenxw
@Date    :2024/4/28 18:12
@Descr:  对代码中引用的各种appkey进行加解密
"""
import base64
import re

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from vgis_encrption.encrptionTools import FernetEncryption, RSAEncryption

from my_project.settings import ENCRPTION


# 将明文用AES加密
def AES_en(key, data):
    # 将长度不足16字节的字符串补齐
    # if len(data) < 16:
    #     data = pad(data)
    data = pad(data.encode("utf-8"), 16, style='pkcs7')
    # 创建加密对象
    # AES_obj = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
    AES_obj = AES.new(key.encode("utf-8"), AES.MODE_ECB)
    # 完成加密
    AES_en_str = AES_obj.encrypt(data)
    # 用base64编码一下
    AES_en_str = base64.b64encode(AES_en_str)
    # 最后将密文转化成字符串
    AES_en_str = AES_en_str.decode("utf-8")
    return AES_en_str


# 解密是加密的逆过程，按着加密代码的逆序很容易就能写出
#
# 将密文字符串重新编码成bytes类型
# 将base64编码解开
# 创建AES解密对象
# 用解密对象对密文解密
# 将补齐的空格用strip（）函数除去
# 将明文解码成字符串

def AES_de(key, data):
    # 解密过程逆着加密过程写
    # 将密文字符串重新编码成二进制形式
    data = data.encode("utf-8")
    # 将base64的编码解开
    data = base64.b64decode(data)
    # 创建解密对象
    # AES_de_obj = AES.new(key.encode("utf-8"), AES.MODE_CBC, iv.encode("utf-8"))
    AES_de_obj = AES.new(key.encode("utf-8"), AES.MODE_ECB)
    # 完成解密
    AES_de_str = AES_de_obj.decrypt(data)
    # 对明文解码
    # AES_de_str = AES_de_str.decode("utf-8").strip().strip(b'\x02'.decode())
    # AES_de_str = AES_de_str.decode("utf-8").strip().strip(b'\x06'.decode()).strip(b'\x02'.decode())
    AES_de_str = handle_x_str(AES_de_str.decode("utf-8"))
    return AES_de_str


# 去掉字符串里的\x开头的特殊字符
def handle_x_str(content):
    # 使用unicode-escape编码集，将unicode内存编码值直接存储
    content = content.encode('unicode_escape').decode('utf-8')
    # 利用正则匹配\x开头的特殊字符
    result = re.findall(r'\\x[a-f0-9]{2}', content)
    for x in result:
        # 替换找的的特殊字符
        content = content.replace(x, '')
    # 最后再解码
    content = content.encode('utf-8').decode('unicode_escape')
    return content

# 从配置文件中
# key1 = ENCRPTION["key1"]
# key2 = ENCRPTION["key2"]
# key3 = ENCRPTION["key3"]
# key4 = ENCRPTION["key4"]

# 或者从generatorSetKey.py中生成key读取
key1 = 'RTq4tbEPNfYjTYKiSVuVDCsmMSr_LztbQE2v21HKg_s='
key2 = 'Z0FBQUFBQm1MaTlEbTZHWlY3MkwwLUFycENWUGt2YW0yUzBoNmpXV1l0SXZRQXliNXg3NUFGZUxoT2lfMTc2WS05R0p3UU9ST250bjk3QVhvdjNIbkZ3OThLYWRvZUU3ZlBBWndXMEpYbnlTOWhpeTlvcUFYOFJxTHNqaGVvVHVxQXh1TE1OWC1VcVdqLW5UZUt6X2p1V25kdjdhSWdGeFNZMGtwbEEyZWRLczhwWW5XVFZKcjBaMTBmS1RzSlJTdzkzTXpYeldpMHVoTTNhblJkYmxYakI4RlMzMjVlNm1FNlp3YUJ1UHZpWGtrODFqbTJMUjRnMTliQ1JJYUdJWUo0V3B4b0ZWWjJqa3BibkJqX3hKSXAtZ2NYMUxGYkhQRHFydDlhbmduQWVrd242d3pWNmFMMElDSG9KZGRoRDVMZTZEUGhxX1pkemtmcWxDTWhfQ19kX3F5cHF1aFI0ampzLWVWcFF0SXNMOWlSejFOVjRrSGIwPQ=='
key3 = 'Z0FBQUFBQm1MaTlEU1cyemw5R1haNU1YNGtvR1FKeExoTEVNYnloTUFQM3RvRF8zVFNFZGJCV3VOTVVnUVhIdWk5bDlQaXlpbkdBUV85Rk5GN3BGNkNGeWY0ajkyTEpIVDRuZHk1WGozTTdKeEZHaTIwbnRCTDJLd3gxbXRzR0hvZDFFMHluc1kyR19ZWEU2WmNsQzQ1ZG5WSm1PWkhwSEJmbkpLdHVFMC1ZUW5oMm94UXliNXZ3ZjIwbzRUaEVFT2JlWlBaSEdXVVMzdzRBUjRKbEZZNXV1bmROdFM5MnVPV0YtSEt6Y09OSjhSZzJIcXctaDI4YlRqdV81blNyNWJMZzA0N0JxRDZlVEJsT3hCckRyblpDdlhWazNxWmY3UG9HNUdqY3V1M0ctQzBQcndKR1plNGViNVVwc1Q2ZkROYU10b2xxUTlYaUNCczdabGlGeldGbUROX2E4cFpvZFFyQUs0QUpFMm5vR3JvMWxLd3N0OWZsZDJpY3NDQnR5Ny12anVpZVZmU2g2cTJIUFI2dzRqcy12a19ET3h3N1ZVNk1zX25nS1RfMFdVdFAyUXlTM0JIUzBGazJWTE9kY0U4M1pHXzF4TGRGR1h3ZXUtM19LUkxIRFNMd0p0dW5BTlhZWUo4UWVjbW5xc2hzeTRzXy1BUDYyVGliaFQ4WXNMUkI2S0xuTXlaZEFpV28xRF9icWpubDZabldua2JnN3hpRDRKN3lkLUpkUkVfcTM1b0VmV000emhiUkpVVTEtemw1ZWFERFdlQjB0Z0xNRkMwZnVGSk5GSDlXd3ExdEZBdHVIRTFmSXVhSlhkRlUwZmdfaXZZWnJ3NDFsOHVnQUF1dW9LUzVoUDl6aVNPTXA4RFZoc0xTdHBEZlR4N0swWVVVUlpCOXVhTC1MU3Jtal9NOXg5VVMtWFh3VUNOSHY5MVMtNWhrdzRPMHVkU3UyTDN0aHU1SWM5XzZuNDQ4OGEzRjdxVmhRTGpKcnRCc0dfRURWTkxQQzd6NU9ZVFRxRTlpWXJDM2lFRFgzUDQ2Yk02WUxKUE5ndTBwaDRtWkUtbEo0Q255Zm9kcmFCUmtHaWI2RzFFWW9jZ2YyUktQUl9uUlhiaHh0VTVyMktNbHdCNWRxOVk1a2xTVTZxZlJfSnBWS01zOXBZUEVxNHAtc2ZjSHlDUGVjakc0MFBYZFZwTVVFcUQzT2YyZ0hYUlliMkVXOHV0OHI2UTZld3UxUTZiS3pvSUo1eVBWUG4waklXdHVKWnhTOGlHMS01VW9vaVpTRUpTVmFuMHQwb2pKVUdjY0pSV0ppR3NES01hYnVRcmRUWXhOTUp1UF9SUGc1X2hRaGRfR0xuZHhfOXMzV2l3N05BSThqWXdoV3JOcTRnOWlHWXVNak0zeEJIek5mY3ZnV1EySkwwREtFTmZsMVNNSXo1bmFoV0MxeVdPaVl1Yml4MUx5YXRnSlBuclJxZHZENTlNUlJPSXRhdGxQVGRvblloUFFPbWZjaGlia0lpSFNuMkgxNTBqS0ZHcEdMc3d4NW5wd1Y4Y2JHbTJIbDd3SWJrbFh5TDU4UWh1VkdWV3BSODNtaERINXpfZXM0YTRzNE5ycDRTOU1SdjVYczg5SEdEdlpwcDJyQQ=='
key4 = 'QidOnmqZ6iiC3ywJdf0eVh+8A/kJTMeOjGQQBklIe+0oDoWWl6wP2kbi1E6YOuq5rUPBzkPyG2eDegvRR6ffOvqj0A3fsLyKjtyKdDxCtux+S3Q2akSIz4aPWn4mwzZF00UmjMYDLC0SO+xM5mqM0ZQpVL4VKAu0xdnrfyMg2Pc='

fernetEncryption = FernetEncryption(key1.encode())
rSAEncryption = RSAEncryption(fernetEncryption.decrypt(key3), fernetEncryption.decrypt(key2))
aes_key = rSAEncryption.decryption(key4)



app_key = "m6NKDQ1Uz9azZIEEzYnaLz68gz0Uza"
print("app_key----->{}".format(app_key))
encrpt_app_key = AES_en(aes_key, app_key)
print("encrpt_app_key----->{}".format(encrpt_app_key))
descpt_app_key = AES_de(aes_key, encrpt_app_key)
print("descpt_app_key----->{}".format(descpt_app_key))
