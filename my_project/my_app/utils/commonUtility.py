#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
import logging

# python dict对象帮助类

logger = logging.getLogger('django')


class CommonHelper:
    def __init__(self):
        pass

    @staticmethod
    # 将POST,GET的参数输出到日志
    def logger_json_key_value(request, logger):
        if request.method == 'POST':
            json_data = request.data
        elif request.method == "GET":
            json_data = request.query_params
        for key, value in json_data.items():
            logger.info("{}:{}".format(key, value))

    # @staticmethod
    # # 去掉图片或文档的http头
    # def remove_url_head(file_url):
    #     if file_url is not None:
    #         # http://192.168.3.152:8683/my_static/sig/jichuan.png  转换为 /my_static/sig/jichuan.png
    #         url_head = "http://{}:{}".format(settings.PROJECT_SERVICE_IP, settings.PROJECT_SERVICE_PORT)
    #         file_url = file_url.replace(url_head, "")
    #         if ("http://") in file_url:
    #             file_url = settings.STATIC_URL + file_url.split(settings.STATIC_URL)[1]
    #     return file_url
    #
    # @staticmethod
    # # 增加图片或文档的http头
    # def add_url_head(file_url):
    #     if file_url is not None:
    #         if ("http://") in file_url:
    #             file_url = settings.STATIC_URL + file_url.split(settings.STATIC_URL)[1]
    #         # /my_static/sig/jichuan.png 转换为 http://192.168.3.152:8683/my_static/sig/jichuan.png
    #         url_head = "http://{}:{}".format(settings.PROJECT_SERVICE_IP, settings.PROJECT_SERVICE_PORT)
    #         file_url = url_head + file_url
    #     return file_url








# 单元测试
# 由于引入了django的settings，所以没法做单元测试了
if __name__ == '__main__':
    # date_text = "202338-43044-54"
    # CommonHelper.is_date_str(date_text)
    # date_text = "2023-4-15"
    # CommonHelper.is_date_str(date_text)
    # date_text = "2023 4 15"
    # CommonHelper.is_date_str(date_text)
    # date_text = "2023-2-23"
    # CommonHelper.convert_date(date_text)
    # date_text = "2月23日"
    # CommonHelper.convert_date(date_text)
    # date_text = "2015年2月23日"
    # CommonHelper.convert_date(date_text)
    # 133,988,250 USD 转为 133988250
    # $1,531,180.00 转换为 1531180.00

    # currency_text = "133,988,250 USD"
    # CommonHelper.parse_currency(currency_text)
    # currency_text = "$1,531,180.00"
    # CommonHelper.parse_currency(currency_text)
    # currency_text = "ww1,531,180.00"
    # CommonHelper.parse_currency(currency_text)
    # currency_text = "1,531,180.00oo"
    # CommonHelper.parse_currency(currency_text)
    # currency_text = "1,531,180.00"
    # CommonHelper.parse_currency(currency_text)
    # currency_text = "&1531180.00"
    # CommonHelper.parse_currency(currency_text)
    # currency_text = "1,531,180.00"
    # CommonHelper.deecimal_currency(currency_text)

    # currency_text = None
    # CommonHelper.parse_currency(currency_text)
    #
    # currency_text = ""
    # CommonHelper.parse_currency(currency_text)
    #
    # currency_value = 1531180.00
    # CommonHelper.thousand_sep_currency(currency_value)
    #
    # currency_value = 15311443480
    # CommonHelper.thousand_sep_currency(currency_value)
    #
    # currency_value = 15311443480
    # curreny_unit = "$"
    # unit_position = "head"
    # CommonHelper.thousand_sep_currency_add_unit(currency_value, curreny_unit, unit_position)
    #
    # currency_value = 1531144344580
    # curreny_unit = "USD"
    # unit_position = "end"
    # CommonHelper.thousand_sep_currency_add_unit(currency_value, curreny_unit, unit_position)
    #
    # currency_value = 1531147743480
    # curreny_unit = None
    # unit_position = None
    # CommonHelper.thousand_sep_currency_add_unit(currency_value, curreny_unit, unit_position)

    date_str = "2023年12月22日"
    print(CommonHelper.parse_date(date_str))
    date_str = "12月22日"
    print(CommonHelper.parse_date(date_str))
    date_str = "2023-12-22"
    print(CommonHelper.parse_date(date_str))
