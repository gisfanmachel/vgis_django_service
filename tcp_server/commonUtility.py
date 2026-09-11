#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 通用帮助类（TCP/WebSocket 服务共用同一套写法）
# @Software: PyCharm
import binascii
import logging
import os
import time
from datetime import datetime

import config
from localization_enum import SysInfoEnum

logger = logging.getLogger(__name__)


class CommonHelper:
    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # 多语言
    # 说明：非 Django 服务没有 request.META，语言标识从三处取，按优先级：
    #       1) 请求头 Localization
    #       2) JSON body 里的 localization 字段
    #       3) 表单里的 localization 字段
    #       都取不到默认 CH
    # ------------------------------------------------------------------
    @staticmethod
    def get_local_str(STR_KEY, request):
        """从请求头取语言标识后返回提示语（Flask request 对象）"""
        local = CommonHelper.get_local_flag(request)
        return CommonHelper.get_local_str2(STR_KEY, local)

    @staticmethod
    def get_local_str2(STR_KEY, local):
        """已知语言标识时直接取提示语（manager/工具类拿不到 request 时用）"""
        return getattr(SysInfoEnum, "{}_{}".format(STR_KEY, local))

    @staticmethod
    def get_local_str3(STR_KEY, request):
        """从 JSON body 的 localization 字段取语言标识"""
        local = CommonHelper.get_local_flag2(request)
        return CommonHelper.get_local_str2(STR_KEY, local)

    @staticmethod
    def get_local_str4(STR_KEY, request):
        """从表单的 localization 字段取语言标识"""
        local = CommonHelper.get_local_flag3(request)
        return CommonHelper.get_local_str2(STR_KEY, local)

    @staticmethod
    def get_local_flag(request):
        """取请求头 Localization 的值，缺省 CH"""
        try:
            local = request.headers.get(config.LOCAL_KEY)
        except Exception:
            local = None
        if local is None or str(local).strip() == "":
            return "CH"
        return str(local).strip()

    @staticmethod
    def get_local_flag2(request):
        """取 JSON body 里 localization 的值，缺省 CH"""
        try:
            data = request.get_json(silent=True) or {}
            local = data.get("localization")
        except Exception:
            local = None
        if local is None or str(local).strip() == "":
            return "CH"
        return str(local).strip()

    @staticmethod
    def get_local_flag3(request):
        """取表单里 localization 的值，缺省 CH"""
        try:
            local = request.form.get("localization")
        except Exception:
            local = None
        if local is None or str(local).strip() == "":
            return "CH"
        return str(local).strip()

    # ------------------------------------------------------------------
    # 文件
    # ------------------------------------------------------------------
    @staticmethod
    def allowed_upload_file(filename):
        """检查文件扩展名是否在允许列表内"""
        return "." in filename and \
            filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS

    @staticmethod
    def bin_to_hex_and_count(filepath):
        """读 bin 文件，返回 (十六进制字符串, 字节数)"""
        try:
            with open(filepath, "rb") as f:
                bin_data = f.read()
            hex_str = binascii.hexlify(bin_data).decode("utf-8")
            return hex_str, len(bin_data)
        except FileNotFoundError:
            logger.error("找不到文件：%s", filepath)
            return None, 0
        except Exception as e:
            logger.error("读取bin文件失败 %s：%s", filepath, e)
            return None, 0

    # ------------------------------------------------------------------
    # 时间
    # ------------------------------------------------------------------
    @staticmethod
    def get_curent_time_str():
        """当前时间的字符串格式"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_last_hour_time(time_str):
        """取给定时间所在的上一整点，如 11:23 → 11:00、11:00 → 10:00"""
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        if dt.minute == 0:
            last_hour = dt.replace(hour=dt.hour - 1, minute=0, second=0, microsecond=0)
        else:
            last_hour = dt.replace(minute=0, second=0, microsecond=0)
        return last_hour.strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------------------------------------------
    # 其他
    # ------------------------------------------------------------------
    @staticmethod
    def is_valid_str(input_str):
        """判断字符串是否有效：None、空串、字符串'null'/'none' 都算无效"""
        if input_str is None:
            return False
        s = str(input_str).strip()
        if s == "" or s.lower() in ("null", "none"):
            return False
        return True

    @staticmethod
    def format_file_size(size_byte):
        """把字节数格式化成易读字符串"""
        size = float(size_byte)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return "{:.2f}{}".format(size, unit)
            size /= 1024

    @staticmethod
    def wait_until(condition_func, timeout=5, interval=0.05):
        """轮询等待某个条件成立，超时返回 False"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if condition_func():
                return True
            time.sleep(interval)
        return False

    @staticmethod
    def ensure_dir(path):
        """确保目录存在"""
        if path and not os.path.exists(path):
            os.makedirs(path)
        return path
