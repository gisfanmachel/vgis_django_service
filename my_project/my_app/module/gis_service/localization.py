# -*- coding: utf-8 -*-
# gis_service 模块的中英文词条
#
# 约定（与其它模块一致）：
#   1. 类名固定为 Enum
#   2. 每条词条必须是 <KEY>_CH / <KEY>_EN 成对，缺一个运行期就 AttributeError
#   3. 取词：CommonHelper.get_local_str_from_module("gis_service", "KEY", request)


class Enum:
    MODULE_TITLE_CH = 'GIS 服务'
    MODULE_TITLE_EN = 'GIS Service'

    # ---- 通用 ----
    SUCCESS_CH = '操作成功'
    SUCCESS_EN = 'operation is successful'

    FAIL_CH = '操作失败'
    FAIL_EN = 'operation is failed'

    # ---- Vector ----
    VECTOR_LOAD_SUCCESS_CH = 'Vector 灌库成功'
    VECTOR_LOAD_SUCCESS_EN = 'vector load is successful'

    VECTOR_TABLE_NOT_EXIST_CH = '表 {} 不存在'
    VECTOR_TABLE_NOT_EXIST_EN = 'table {} does not exist'

    VECTOR_TABLE_EXISTS_CH = '表 {} 已存在，先确认删除'
    VECTOR_TABLE_EXISTS_EN = 'table {} already exists, please confirm deletion'

    VECTOR_BAD_TABLE_NAME_CH = '表名 {} 不合法（仅允许字母数字下划线，且以字母下划线开头）'
    VECTOR_BAD_TABLE_NAME_EN = 'invalid table name {}'

    VECTOR_DELETE_CONFIRM_MISSING_CH = '删除表需要 header X-Confirm: true'
    VECTOR_DELETE_CONFIRM_MISSING_EN = 'deletion requires X-Confirm: true header'

    # ---- MVT ----
    MVT_BAD_TABLE_NAME_CH = '非法的表名'
    MVT_BAD_TABLE_NAME_EN = 'invalid table name'

    MVT_Z_OUT_OF_RANGE_CH = 'z 超出范围 [0,22]'
    MVT_Z_OUT_OF_RANGE_EN = 'z out of range [0,22]'

    MVT_TILE_OUT_OF_RANGE_CH = '瓦片坐标超出范围'
    MVT_TILE_OUT_OF_RANGE_EN = 'tile coordinates out of range'

    # ---- PMTiles / COG / STAC ----
    TASK_DISPATCHED_CH = '任务已派发'
    TASK_DISPATCHED_EN = 'task dispatched'

    TASK_TYPE_INVALID_CH = '不支持的任务类型 {}'
    TASK_TYPE_INVALID_EN = 'unsupported task type {}'

    TASK_NOT_FOUND_CH = '任务 {} 不存在'
    TASK_NOT_FOUND_EN = 'task {} does not exist'

    PARAM_REQUIRED_CH = '缺少必填参数：{}'
    PARAM_REQUIRED_EN = 'missing required parameter: {}'

    # ---- Health ----
    HEALTH_OK_CH = '健康'
    HEALTH_OK_EN = 'healthy'

    HEALTH_DEGRADED_CH = '降级'
    HEALTH_DEGRADED_EN = 'degraded'