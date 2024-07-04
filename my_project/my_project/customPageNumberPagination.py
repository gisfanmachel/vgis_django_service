"""
#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
@Project :dzgyyq_service
@File    :riskAnlysisAlarmManager.py
@IDE     :PyCharm
@Author  :chenxw
@Date    :2024/7/4 11:24
@Descr:
"""
import json

from django.http import QueryDict
from rest_framework.response import Response

from t231_app.models import TtAlarmAnlysisReport
from t231_app.serializers import TtAlarmAnlysisReportSerializer
from t231_app.views.response.baseRespone import Result
from t231_project import settings
from t231_project.customPageNumberPagination import CustomPageNumberPagination


class TtAlarmAnlysisReportOperator:

    def __init__(self, connection):
        self.connection = connection

    '''
        查询预警分析报告列表
    '''

    def query_list(self, request):
        data = request.data
        page = data.get('page')
        size = data.get('size')

        if page is None or size is None:
            msg = "page 和size 都是必传参数"
            json_data = json.dumps(msg)
            return Result.fail(msg, json_data)
        if size > settings.PAGE_MAX_SIZE:
            msg = "size 不可以大于" + str(settings.PAGE_MAX_SIZE)
            json_data = json.dumps(msg)
            return Result.fail(msg, json_data)
        if page == 0 or size == 0:
            msg = "page 或者size 不可以大于0 "
            json_data = json.dumps(msg)
            return Result.fail(msg, json_data)

        company_id = data.get('company_id')
        sql = '''
        select
            t1.id,t1.report_name,t2.company_risk_level,t3.fullname,t1.create_time
        from
            tt_alarm_anlysis_report t1
            left join tt_risk_alarm_manage t2 on t2.company_id = t1.company_id
            left join auth_user t3 on t3.id=t1.create_user_id
        where
            t1.company_id ={}
        '''.format(company_id)
        results = TtAlarmAnlysisReport.objects.raw(sql)

        if results:
            page_count = len(results)
            customPageNumberPagination = CustomPageNumberPagination()
            customPageNumberPagination.page = page
            customPageNumberPagination.page_size = size
            new_query_params = QueryDict(mutable=True)
            new_query_params.update({'page': page})
            # 将新的 QueryDict 赋值给 request 的 GET 属性
            request._request.GET = new_query_params
            r_page = customPageNumberPagination.paginate_queryset(results, request, self)
            data_serializer = TtAlarmAnlysisReportSerializer(r_page, many=True)  # 将当前页数据序列化

            # 过滤掉不需要的字段
            # for d in data_serializer.data:
            #     d.pop('handle_status')
            #     d.pop('handle_detail')

            res = Result.page_list(data_serializer.data, page_count)
            return Response(res)

        else:
            return Response(Result.page_list(0))


class TtRiskAlarmManageOperator:

    def __init__(self, connection):
        self.connection = connection
