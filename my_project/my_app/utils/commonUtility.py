#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
import datetime
import importlib
import logging

from my_app.enum.localization_enum import SysInfoEnum
from my_project import settings

# 通用帮助类

logger = logging.getLogger('django')


class CommonHelper:
    def __init__(self):
        pass

    # ---------------- 多语言相关 ----------------
    # 说明：请求头里带 Localization: CH / EN，缺省按 CH 处理
    #       STR_KEY 必须同时存在 <STR_KEY>_CH 和 <STR_KEY>_EN，见 enum/localization_enum.py
    @staticmethod
    def get_local_str(STR_KEY, request):
        Header_LOCAL_KEY = str("http_" + settings.LOCAL_KEY).upper()
        # 没有传入local参数或local参数为空，默认为CH
        if Header_LOCAL_KEY not in request.META:
            local = "CH"
        else:
            local = request.META.get(Header_LOCAL_KEY)
            if local is None or local == "":
                local = "CH"
        return getattr(SysInfoEnum, "{}_{}".format(STR_KEY, local))

    # 已知语言标识时直接取提示语（用于 manager 层拿不到 request 的场景）
    @staticmethod
    def get_local_str2(STR_KEY, local):
        return getattr(SysInfoEnum, "{}_{}".format(STR_KEY, local))

    # 取当前请求的语言标识（CH / EN），供 Result.xxx(localization=...) 使用
    @staticmethod
    def get_local_flag(request):
        Header_LOCAL_KEY = str("http_" + settings.LOCAL_KEY).upper()
        if Header_LOCAL_KEY not in request.META:
            local = "CH"
        else:
            local = request.META.get(Header_LOCAL_KEY)
            if local is None or local == "":
                local = "CH"
        return local

    # 分模块取词：从 my_app/module/<模块名>/localization.py 的 Enum 类里取 KEY_CH / KEY_EN
    #
    # 约定：每个模块自带一个 localization.py，内含类名固定为 Enum 的一组 CH/EN 词条，
    #       不需要注册，按模块名动态 import 即可。
    # 用法：CommonHelper.get_local_str_from_module("demo", "ADD_SUCCESS", request)
    #
    # 与 get_local_str 的区别：那个查全局词表 my_app/enum/localization_enum.py，
    # 这个查指定模块自己的词表，避免所有模块的词条挤在一个文件里。
    @staticmethod
    def get_local_str_from_module(MODULE_NAME, STR_KEY, request):
        if not MODULE_NAME or not isinstance(MODULE_NAME, str):
            raise ValueError("MODULE_NAME 必须是非空字符串")
        if not STR_KEY or not isinstance(STR_KEY, str):
            raise ValueError("STR_KEY 必须是非空字符串")

        local = CommonHelper.get_local_flag(request)
        module_path = "my_app.module.{}.localization".format(MODULE_NAME)
        try:
            localization_module = importlib.import_module(module_path)
        except ImportError as e:
            raise ImportError("无法导入模块词表 {}: {}".format(module_path, e))
        if not hasattr(localization_module, "Enum"):
            raise AttributeError("模块 {} 中没有找到 Enum 类".format(module_path))
        attr_name = "{}_{}".format(STR_KEY, local)
        enum_class = localization_module.Enum
        if not hasattr(enum_class, attr_name):
            raise AttributeError("模块 {} 的 Enum 中不存在词条 {}".format(MODULE_NAME, attr_name))
        return getattr(enum_class, attr_name)

    # ---------------- 参数/时间相关 ----------------
    # 判断字符串是否有效（None、空串、字符串"null"/"none" 都算无效）
    @staticmethod
    def is_valid_str(input_str):
        if input_str is None or str(input_str).strip() == "" or str(input_str).strip().lower() == "null" or str(
                input_str).strip().lower() == "none":
            return False
        else:
            return True

    # 获取当前时间的字符串格式
    @staticmethod
    def get_curent_time_str():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 统一设置新增记录的创建人/创建时间/修改人/修改时间
    @staticmethod
    def set_cre_mod_user_time(data, request):
        data["create_user_id"] = request.auth.user_id
        data["create_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data["modify_user_id"] = request.auth.user_id
        data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 统一设置修改记录的修改人/修改时间
    @staticmethod
    def set_mod_user_time(data, request):
        data["modify_user_id"] = request.auth.user_id
        data["modify_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # ---------------- 日志/URL 相关 ----------------
    # 将POST,GET的参数输出到日志
    @staticmethod
    def logger_json_key_value(request, logger):
        if request.method == 'POST':
            json_data = request.data
        elif request.method == "GET":
            json_data = request.query_params
        for key, value in json_data.items():
            logger.info("{}:{}".format(key, value))

    # 获取图片或文档的HTTP头信息，用于拼接完整的资源访问URL
    @staticmethod
    def get_url_head():
        url_head = "{}://{}:{}{}".format(settings.PROJECT_WEB_PROTOCOL, settings.PROJECT_SERVICE_IP,
                                         settings.PROJECT_SERVICE_PORT, settings.STATIC_URL)
        return url_head


# 单元测试
# 由于引入了django的settings，所以没法做单元测试了
if __name__ == '__main__':
    pass
