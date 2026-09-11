#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   ：全局分页类
# @Software: PyCharm
from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    """
    自定义分页类，继承自 PageNumberPagination。
    settings.REST_FRAMEWORK.DEFAULT_PAGINATION_CLASS 指向本类。
    """
    page_size = 10  # 默认每页显示的条目数
    page_size_query_param = 'size'  # URL 中控制每页显示条目数的参数名称
    page_query_param = 'page'  # URL 中控制页码的参数名称
    max_page_size = 100  # 每页显示的最大条目数
