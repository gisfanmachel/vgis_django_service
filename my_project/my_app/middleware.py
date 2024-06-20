#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Time    : 2021/2/20 22:40
# @Author  : gisfan_ai
# @Email   : gisfanmachel@gmail.com
# @File    : middleware.py
# @Desc    ：中间件
# @Software: PyCharm

import base64
import binascii
import json

from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad
from cryptography.fernet import Fernet
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from vgis_utils.vgis_string.stringTools import StringHelper
from vgis_encrption.encrptionTools import AESEncryption, RSAEncryption, FernetEncryption, StringHexMutualConvertion

from my_app.models import SysParam
from my_app.utils.encryptionUtility import encryptionHelper
from my_project import settings
import logging

from my_project.settings import ENCRPTION

logger = logging.getLogger('django')

class DisableCSRF(MiddlewareMixin):
    def process_request(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)


class CORSMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # 添加响应头

        # 允许你的域名来获取我的数据
        response['Access-Control-Allow-Origin'] = "*"
        print("allow orgin")
        # 允许你携带Content-Type请求头
        # response['Access-Control-Allow-Headers'] = "Content-Type"

        # 允许你发送DELETE,PUT
        # response['Access-Control-Allow-Methods'] = "DELETE,PUT"
        return response


# 对接接口请求和响应内容进行加解密
# 需要修改init初始化函数里的fernet_key(fernet密钥),
# 需要修改read_rsa_public_key函数里的public_key(rsa公钥,从发布license的密钥管理工具获取)，用fernet加密
# 需要修改read_rsa_private_key函数里的private_key(rsa私钥,从发布license的密钥管理工具获取)，用fernet加密
# 需要修改init初始化函数里的aes_key(aes密钥)，用ras加密
# RSA加解密有长度限制，因此采用AES加解密
class EncryptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        pass

    def get_IS_ENCRYPTION(self):
        obj = SysParam.objects.get(param_en_key='IS_ENCRYPTION')
        if obj is not None:
            return True if obj.param_value == "是" else False
        else:
            return False

    def __call__(self, request):
        aESEncryption=encryptionHelper.get_aes_encrytion_object()
        # 双重加解密：
        # 服务端加密：AES加密、不转十六进制了，因为服务端返回极加密结果在POSTMAN没法写脚本解密存TOKEN
        # 客户端解密： AES解密
        # 客户端加密：AES加密、字符串转十六进制，主要是为解决get请求的url会自动进行特殊字符的转义
        # 服务端解密：十六进制转字符串---AES解密
        # AES的密钥，用RSA加密
        # RAS的公钥和私钥，用fernet加密
        if self.get_IS_ENCRYPTION():
            logger.info("request.method:{}".format(request.method))
            logger.info("request.path:{}".format(request.path))
            # 这里的reqeust是 django.core.handlers.wsgi.WGSIRequest，不是rest_framework.request.Request
            # 解密请求参数
            # POST和PUT的body不为空
            # 如果是form-data里的file/files不加密，其他key的value要对加密参数解密（针对文件上传，同时还要传其他变量的）
            # 如果是application/json，需要对加密参数解密
            if request.method == 'POST' or request.method == "PUT":
                # 针对post里的json
                if request.content_type == "application/json":
                    encrypted_data = json.loads(request.body.decode('utf-8')).get('data')
                    if encrypted_data:
                        logger.info("加密的请求参数（客户端传入）：{}".format(encrypted_data))
                        encrypted_data = StringHexMutualConvertion.convert_hex_to_str(encrypted_data)
                        decrypted_data = aESEncryption.AES_de(encrypted_data)
                        logger.info("解密后的请求参数：{}".format(decrypted_data))
                        request._body = decrypted_data.encode('utf-8')
                        # 得到调用的每个接口返回的内容
                        response = self.get_response(request)
                    else:
                        logger.info("加密后的{}请求参数不对".format(request.method))
                        res = {
                            'success': False,
                            'code': -1,
                            'message': '加密后的{}请求参数不对'.format(request.method)
                        }
                        response = HttpResponse(content=json.dumps(res, ensure_ascii=False),
                                                content_type="application/json,charset=utf-8")
                # 针对post里上传文件的相关变量
                if request.content_type == "multipart/form-data":
                    if request.POST is not None and len(request.POST) > 0:
                        encrypted_data = request.POST.get('data')
                        if encrypted_data:
                            logger.info("加密的请求参数（客户端传入）：{}".format(encrypted_data))
                            encrypted_data = StringHexMutualConvertion.convert_hex_to_str(encrypted_data)
                            decrypted_data = aESEncryption.AES_de(encrypted_data)
                            logger.info("解密后的请求参数：{}".format(decrypted_data))
                            decrypted_dict = json.loads(decrypted_data)
                            request.POST = request.POST.copy()
                            for key in decrypted_dict:
                                request.POST[key] = decrypted_dict[key]
                            del request.POST['data']
                    response = self.get_response(request)
                # 针对post的请求参数处理，将原来的get改成了post,注意参数的问号前有个斜杆
                # POST {{service_host}}/ttSatellitePolicy/searchSatelliteAndPolilcy/?data=7069366667554b4b66767939424638594255554d4e546137446a6c3355546269662b364c7a72713244635339756c426b35544d697667592f65424d373542624e4f484c4d7a7932796a4f6d565837704838584b644e6e576568756b513769746a6d36696b3537764d6a384434327537346c54366d545557755958344b59353972436c474b674
                if request.content_type == "text/plain":
                    # 后面有请求参数
                    if request.GET is not None and len(request.GET) > 0:
                        encrypted_data = request.GET.get('data')
                        if encrypted_data:
                            print("加密的请求参数（客户端传入）：{}".format(encrypted_data))
                            encrypted_data = StringHexMutualConvertion.convert_hex_to_str(encrypted_data)
                            decrypted_data = aESEncryption.AES_de(encrypted_data)
                            print("解密后的请求参数：{}".format(decrypted_data))
                            request.GET = request.GET.copy()
                            keyvalue_array = decrypted_data.split("&")
                            for keyvalue in keyvalue_array:
                                keyvalue_array = keyvalue.split("=")
                                key = keyvalue_array[0]
                                value = None if len(keyvalue_array) == 1 else keyvalue_array[1]
                                request.GET[key] = value
                            del request.GET['data']
                            # 得到调用的每个接口返回的内容
                            response = self.get_response(request)
                        else:
                            print("加密后的POST请求参数不对")
                            res = {
                                'success': False,
                                'code': -1,
                                'message': '加密后的POST请求参数不对'
                            }
                            response = HttpResponse(content=json.dumps(res, ensure_ascii=False),
                                                    content_type="application/json,charset=utf-8")
                    # 后面没有请求参数
                    else:
                        response = self.get_response(request)

            # GET，需要判断后面有没有参数，若有参数需要对加密参数解密
            if request.method == 'GET':
                if request.GET is not None and len(request.GET) > 0:
                    encrypted_data = request.GET.get('data')
                    if encrypted_data:
                        logger.info("加密的请求参数（客户端传入）：{}".format(encrypted_data))
                        encrypted_data = StringHexMutualConvertion.convert_hex_to_str(encrypted_data)
                        decrypted_data = aESEncryption.AES_de(encrypted_data)
                        logger.info("解密后的请求参数：{}".format(decrypted_data))
                        request.GET = request.GET.copy()
                        keyvalue_array = decrypted_data.split("&")
                        for keyvalue in keyvalue_array:
                            keyvalue_array = keyvalue.split("=")
                            key = keyvalue_array[0]
                            value = None if len(keyvalue_array) == 1 else keyvalue_array[1]
                            request.GET[key] = value
                        del request.GET['data']
                        # 得到调用的每个接口返回的内容
                        response = self.get_response(request)
                    else:
                        logger.info("加密后的GET请求参数不对")
                        res = {
                            'success': False,
                            'code': -1,
                            'message': '加密后的GET请求参数不对'
                        }
                        response = HttpResponse(content=json.dumps(res, ensure_ascii=False),
                                                content_type="application/json,charset=utf-8")
                else:
                    response = self.get_response(request)

            # DELETE操作不加密
            if request.method == "DELETE":
                response = self.get_response(request)

            # DELETE返回status_code为204，不能再改写response.content，否则会报错，远程主机连接中断，导致没有响应到前端
            # 因此对非DELETE操作进行响应内容的加密,，验证码接口返回图片的二进制数据也不加密
            if request.method != "DELETE" and "user/verfication/" not in request.path:
                # 加密响应内容
                content = response.content.decode('utf-8')
                logger.info("正常的响应内容：{}".format(content))
                if content is None or content.strip() == "":
                    res = {
                        'success': True,
                        'code': 0,
                        'message': '执行成功'
                    }
                    content = json.dumps(res, ensure_ascii=False)
                # content = self.convert_str_to_hex(content)
                encrypted_content = aESEncryption.AES_en(content)
                response.content = "{\"data\":\"" + encrypted_content + "\"}"
                logger.info("加密后的响应内容（返回到客户端）：{}".format(response.content.decode('utf-8')))

                # 打印验证加密响应内容的解密
                decrypted_data = aESEncryption.AES_de(encrypted_content)
                logger.info("验证加密响应内容的解密：{}".format(decrypted_data))
        else:
            logger.info("没有加解密")
            response = self.get_response(request)
        return response
