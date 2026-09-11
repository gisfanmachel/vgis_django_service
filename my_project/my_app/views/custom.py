#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 统一的 ViewSet 基类，把 list/retrieve/destroy 的返回收敛到 Result 里
# @Software: PyCharm
import logging

from rest_framework import viewsets
from rest_framework.response import Response

from my_app.utils.commonUtility import CommonHelper
from my_app.views.response.baseRespone import Result

logger = logging.getLogger('django')


class CustomModelViewSet(viewsets.ModelViewSet):
    """
    自定义 ModelViewSet 基类。

    用途：把 list / retrieve / destroy 三个动作的返回体统一成 Result 结构，
         并统一按请求头 Localization 返回中英文提示，避免每个 ViewSet 各写一套。

    用法：业务 ViewSet 继承本类即可；若某个动作有自己的返回约定（例如前端依赖
         {"results": [...]} 这种裸结构），在该 ViewSet 里显式重写那个方法。
    """

    def list(self, request, *args, **kwargs):
        local = CommonHelper.get_local_flag(request)
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                page_response = self.get_paginated_response(serializer.data)
                data = Result.list(page_response.data, localization=local)
                return Response(data)

            # 未配置分页时，退化为全量列表
            serializer = self.get_serializer(queryset, many=True)
            data = Result.list(serializer.data, localization=local)
            return Response(data)

        except Exception as exp:
            logger.exception("查询列表失败")
            msg = CommonHelper.get_local_str2("QUERY_LIST_FAIL", local).format(str(exp))
            return Result.fail(msg, msg, localization=local)

    def retrieve(self, request, *args, **kwargs):
        local = CommonHelper.get_local_flag(request)
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as exp:
            logger.exception("查询详情失败")
            msg = CommonHelper.get_local_str2("QUERY_DETAIL_FAIL", local).format(str(exp))
            return Result.fail(msg, msg, localization=local)

    def destroy(self, request, *args, **kwargs):
        local = CommonHelper.get_local_flag(request)
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Result.ok(localization=local)
        except Exception as exp:
            logger.exception("删除数据失败")
            msg = CommonHelper.get_local_str2("DELETE_DATA_FAIL", local).format(str(exp))
            return Result.fail(msg, msg, localization=local)
