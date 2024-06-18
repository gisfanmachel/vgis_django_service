import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from rest_framework.response import Response


@dataclass
class ResultCodeMsgEnum(Enum):
    REQUEST_SUCCESS = {"code": 200, "msg": "Request successful"}
    CREATE_ERROR = {'code': 1000, 'msg': '新增失败'}

    OPERATION_ERROR = {'code': 1001, 'msg': '操作失败'}

    ID_IS_A_MUST = {'code': 1002, 'msg': 'ID是必传参数'}
    # Add more enums as needed


@dataclass
class PageResult(dict):
    count: Optional[int] = None
    next: Optional[str] = None
    previous: Optional[str] = None
    results: Optional[any] = None

    def set_count_result(self, count, results):
        self.count = count
        self.results = results


@dataclass
class Result(dict):
    success: bool = True
    code: Optional[int] = None
    msg: Optional[str] = None
    date: datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    request_id: Optional[str] = None
    obj: Optional[any] = None

    @staticmethod
    def ok():
        return Response(Result().code_msg(ResultCodeMsgEnum.REQUEST_SUCCESS).__dict__)

    @staticmethod
    def cres_ures(cres, id_name=None):
        data = cres.data
        if id_name:
            id = data[id_name]
        else:
            id = data['id']
        json_data = json.dumps(data)
        if id is not None:
            # 新增
            return Response(Result().code_msg(ResultCodeMsgEnum.REQUEST_SUCCESS).set_obj(id).__dict__)
        else:
            return Result.fail(ResultCodeMsgEnum.CREATE_ERROR.value['msg'], json_data)

    @staticmethod
    def cres_ures_data(data):
        id = data.id
        if id is not None:
            # 新增
            return Response(Result().code_msg(ResultCodeMsgEnum.REQUEST_SUCCESS).set_obj(id).__dict__)
        else:
            json_data = json.dumps(data)
            return Result.fail(ResultCodeMsgEnum.CREATE_ERROR.value['msg'], json_data)

    @staticmethod
    def cres_ures_update(count):
        if count > 0:
            return Result().ok()
        else:
            msg = "更新失败"
            return Result.fail(msg, msg)

    @staticmethod
    def list(obj):
        return Result().code_msg(ResultCodeMsgEnum.REQUEST_SUCCESS).set_obj(obj).__dict__

    @staticmethod
    def page_list(obj=[], page_count=0):
        if obj == 0:
            obj = []
        pageResult = PageResult()
        pageResult.set_count_result(page_count, obj)
        return Result().code_msg(ResultCodeMsgEnum.REQUEST_SUCCESS).set_obj(pageResult.__dict__).__dict__

    @staticmethod
    def list_response(response):
        data = response.data
        res = Result.list(data)
        return Response(res)

    @staticmethod
    def fail(msg, obj):
        if isinstance(obj, str):
            obj = json.dumps(obj)
        return Response(Result()
                        .set_success(False)
                        .set_msg(msg)
                        .set_obj(json.loads(obj))
                        .set_code(ResultCodeMsgEnum.OPERATION_ERROR.value['code'])
                        .__dict__)

    @staticmethod
    def sucess(msg, obj=None):
        return Response(Result()
                        .set_success(True)
                        .set_msg(msg)
                        .set_obj(obj)
                        .set_code(ResultCodeMsgEnum.REQUEST_SUCCESS.value['code'])
                        .__dict__)

    @staticmethod
    def sucess_obj(obj):
        return Response(Result()
                        .set_success(True)
                        .set_msg(ResultCodeMsgEnum.REQUEST_SUCCESS.value['msg'])
                        .set_obj(obj)
                        .set_code(ResultCodeMsgEnum.REQUEST_SUCCESS.value['code'])
                        .__dict__)

    @staticmethod
    def fail_no_response(msg, obj):
        if isinstance(obj, str):
            obj = json.dumps(obj)
        return Result().set_success(False).set_msg(msg).set_obj(json.loads(obj)).set_code(
            ResultCodeMsgEnum.OPERATION_ERROR.value['code']).__dict__

    def fail_response(resultCodeMsgEnum, obj):
        return Response(Result().set_success(False).set_code_msg(resultCodeMsgEnum).set_obj(json.loads(obj)).__dict__)

    def set_code_msg(self, resultCodeMsgEnum):
        self.set_msg(resultCodeMsgEnum.value['msg'])
        self.set_code(resultCodeMsgEnum.value['code'])
        return self

    @staticmethod
    def fail_dick(resultCodeMsgEnum, obj):

        return Result().set_success(False).set_msg(resultCodeMsgEnum.value['msg']).set_code(
            resultCodeMsgEnum.value['code']).set_obj(obj)

    def api_name(self, api_name):
        self.api_name = api_name
        return self

    def set_obj(self, obj):
        self.obj = obj
        return self

    def code_msg(self, result_code):
        self.msg = result_code.value['msg']
        self.code = result_code.value['code']
        return self

    def set_code(self, code):
        self.code = code
        return self

    def set_msg(self, msg):
        self.msg = msg
        return self

    def set_obj(self, obj):
        self.obj = obj
        return self

    def set_success(self, success):
        self.success = success
        return self
