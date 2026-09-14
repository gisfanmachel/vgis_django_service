# -*- coding: utf-8 -*-
# demo 模块的中英文词条
#
# 约定（各模块一致）：
#   1. 类名固定为 Enum
#   2. 每条词条必须是 <KEY>_CH / <KEY>_EN 成对，缺一个运行期就 AttributeError
#   3. 取词：CommonHelper.get_local_str_from_module("demo", "KEY", request)
#   4. 新增后跑 python my_app/tools/check_localization_keys.py 自检
#
# 注意：这里只放**本模块专用**的词条；跨模块通用的（如"请求成功"）放全局
#      my_app/enum/localization_enum.py，用 CommonHelper.get_local_str 取。


class Enum:
    # ---- 通用 ----
    MODULE_TITLE_CH = '演示数据'
    MODULE_TITLE_EN = 'Demo Item'

    QUERY_SUCCESS_CH = '查询成功'
    QUERY_SUCCESS_EN = 'query is successful'

    QUERY_FAIL_CH = '查询失败'
    QUERY_FAIL_EN = 'query is failed'

    # ---- 参数校验 ----
    PARAM_MISSING_CH = '缺少必填参数：{}'
    PARAM_MISSING_EN = 'missing required parameter: {}'

    PAGE_PARAM_INVALID_CH = 'page 与 size 必须是不小于 1 的整数'
    PAGE_PARAM_INVALID_EN = 'page and size must be integers not less than 1'

    SIZE_EXCEED_MAX_CH = 'size 不可以大于 {}'
    SIZE_EXCEED_MAX_EN = 'size cannot be greater than {}'

    # ---- 增删改 ----
    ADD_SUCCESS_CH = '新增{}成功'
    ADD_SUCCESS_EN = 'add {} is successful'

    ADD_EXIST_CH = '新增失败，业务编码 {} 已存在'
    ADD_EXIST_EN = 'add is failed: item code {} already exists'

    UPDATE_SUCCESS_CH = '修改{}成功'
    UPDATE_SUCCESS_EN = 'update {} is successful'

    UPDATE_NOT_EXIST_CH = '修改失败，编号 {} 的记录不存在'
    UPDATE_NOT_EXIST_EN = 'update is failed: record {} does not exist'

    DELETE_SUCCESS_CH = '删除{}成功'
    DELETE_SUCCESS_EN = 'delete {} is successful'

    DELETE_NOT_EXIST_CH = '删除失败，编号 {} 的记录不存在'
    DELETE_NOT_EXIST_EN = 'delete is failed: record {} does not exist'

    OPERATION_FAIL_REASON_CH = '{}失败：{}'
    OPERATION_FAIL_REASON_EN = '{} is failed: {}'

    # ---- Excel 导出 ----
    EXPORT_SUCCESS_CH = '导出成功，共 {} 条'
    EXPORT_SUCCESS_EN = 'export is successful, {} rows in total'

    EXPORT_NO_DATA_CH = '没有符合条件的数据可导出'
    EXPORT_NO_DATA_EN = 'no data to export'

    EXPORT_SHEET_NAME_CH = '演示数据'
    EXPORT_SHEET_NAME_EN = 'DemoItem'

    # ---- Excel 导入 ----
    IMPORT_SUCCESS_CH = '导入完成：共 {} 行，新增 {} 行，更新 {} 行'
    IMPORT_SUCCESS_EN = 'import is done: {} rows in total, {} created, {} updated'

    IMPORT_NO_FILE_CH = '导入失败，请上传 Excel 文件（form-data 字段名 file）或指定已上传的 file_id'
    IMPORT_NO_FILE_EN = 'import is failed: please upload an Excel file (form-data field "file") or pass an uploaded file_id'

    IMPORT_FILE_SUFFIX_INVALID_CH = '导入失败，只支持 .xlsx / .xls 格式，当前为 {}'
    IMPORT_FILE_SUFFIX_INVALID_EN = 'import is failed: only .xlsx / .xls are supported, got {}'

    IMPORT_HEADER_MISSING_CH = '导入失败，Excel 缺少必需列：{}'
    IMPORT_HEADER_MISSING_EN = 'import is failed: required columns missing: {}'

    IMPORT_ROW_LIMIT_CH = '导入失败，单次最多 {} 行，当前 {} 行，请拆分后重试'
    IMPORT_ROW_LIMIT_EN = 'import is failed: at most {} rows per import, got {}; please split the file'

    IMPORT_ROW_ERROR_CH = '第 {} 行「{}」{}'
    IMPORT_ROW_ERROR_EN = 'row {} [{}] {}'
