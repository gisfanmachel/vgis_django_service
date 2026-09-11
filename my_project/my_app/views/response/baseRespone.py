import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from rest_framework.response import Response

from my_app.enum.localization_enum import SysInfoEnum


# 统一的返回码和消息枚举类
# 约定：需要国际化的消息一律引用 SysInfoEnum，并成对提供 _EN 变体，
#       由 Result.xxx(localization="EN") 选择。
@dataclass
class ResultCodeMsgEnum(Enum):
    REQUEST_SUCCESS = {"code": 200, "msg": SysInfoEnum.REQUEST_SUCCESS_CH}
    REQUEST_SUCCESS_EN = {"code": 200, "msg": SysInfoEnum.REQUEST_SUCCESS_EN}

    CREATE_ERROR = {'code': 1000, 'msg': SysInfoEnum.ADD_FAIL_CH}
    CREATE_ERROR_EN = {'code': 1000, 'msg': SysInfoEnum.ADD_FAIL_EN}

    OPERATION_ERROR = {'code': 1001, 'msg': SysInfoEnum.OPERATE_FAIL_CH}
    OPERATION_ERROR_EN = {'code': 1001, 'msg': SysInfoEnum.OPERATE_FAIL_EN}

    ID_IS_A_MUST = {'code': 1002, 'msg': SysInfoEnum.ID_MUST_CH}
    ID_IS_A_MUST_EN = {'code': 1002, 'msg': SysInfoEnum.ID_MUST_EN}


# 分页结果类
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
    def ok(localization=None):
        success_msg = ResultCodeMsgEnum.REQUEST_SUCCESS_EN if localization == "EN" \
            else ResultCodeMsgEnum.REQUEST_SUCCESS
        return Response(Result().code_msg(success_msg).__dict__)

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
    def create_enum(name, values):
        return Enum(name, values)

    @staticmethod
    def list(obj, **kwargs):
        message = ResultCodeMsgEnum.REQUEST_SUCCESS
        if kwargs.get("localization") == "EN":
            message = ResultCodeMsgEnum.REQUEST_SUCCESS_EN
        if "message" in kwargs:
            MyEnum = Result.create_enum('MyEnum', {'LIST_SUCCESS': {"code": 200, "msg": kwargs["message"]}})
            message = MyEnum.LIST_SUCCESS
        return Result().code_msg(message).set_obj(obj).__dict__

    @staticmethod
    def page_list(obj=[], page_count=0, **kwargs):
        if obj == 0:
            obj = []
        pageResult = PageResult()
        pageResult.set_count_result(page_count, obj)
        req_success = ResultCodeMsgEnum.REQUEST_SUCCESS
        if kwargs.get("localization") == "EN":
            req_success = ResultCodeMsgEnum.REQUEST_SUCCESS_EN
        return Result().code_msg(req_success).set_obj(pageResult.__dict__).__dict__

    @staticmethod
    def list_response(response):
        data = response.data
        res = Result.list(data)
        return Response(res)

    @staticmethod
    def fail(msg, obj=None, **kwargs):
        op_fail = ResultCodeMsgEnum.OPERATION_ERROR
        if kwargs.get("localization") == "EN":
            op_fail = ResultCodeMsgEnum.OPERATION_ERROR_EN
        if isinstance(obj, str):
            obj = json.dumps(obj)
        if obj is None:
            obj = json.dumps(msg)
        return Response(Result()
                        .set_success(False)
                        .set_msg(msg)
                        .set_obj(json.loads(obj) if isinstance(obj, str) else obj)
                        .set_code(op_fail.value['code'])
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

    def set_success(self, success):
        self.success = success
        return self
