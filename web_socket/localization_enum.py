# -*- coding: utf-8 -*-
# 国际化
# 约定：每条提示必须是成对的 <KEY>_CH / <KEY>_EN，缺一个运行期就会 AttributeError。
#       新增后跑一下自检：python check_localization_keys.py
#       业务自己的提示语建议单独放在本文件末尾的「业务提示语」区，便于版本升级时合并。


class SysInfoEnum:
    # ------------------------------------------------------------------
    # 通用（与 Django 框架模板保持一致的公共词条）
    # ------------------------------------------------------------------
    SUCCESS_CH = '成功'
    SUCCESS_EN = ' is successful'

    FAIL_CH = '失败'
    FAIL_EN = ' is fail'

    REQUEST_SUCCESS_CH = '请求成功'
    REQUEST_SUCCESS_EN = 'request is successful'

    ADD_FAIL_CH = '新增失败'
    ADD_FAIL_EN = 'add is fail'

    OPERATE_FAIL_CH = '操作失败'
    OPERATE_FAIL_EN = 'operate is fail'

    ID_MUST_CH = "ID是必传参数"
    ID_MUST_EN = "ID is required parameter"

    PAGE_AND_SIZE_MUST_CH = "page 和size 都是必传参数"
    PAGE_AND_SIZE_MUST_EN = "page and size are required parameters"

    MISSING_REQUIRED_FIELD_CH = "缺少必填字段"
    MISSING_REQUIRED_FIELD_EN = "missing required field"

    INVALID_JSON_FORMAT_CH = "无效的JSON格式"
    INVALID_JSON_FORMAT_EN = "invalid JSON format"

    GET_DATA_FAIL_CH = "获取数据失败"
    GET_DATA_FAIL_EN = "get data fail"

    NO_RESPONSE_RECEIVED_CH = "未接收到响应信息"
    NO_RESPONSE_RECEIVED_EN = "no response received"

    NO_RESPONSE_OBTAINED_CH = "没有获取到响应"
    NO_RESPONSE_OBTAINED_EN = "no response obtained"

    # ------------------------------------------------------------------
    # 框架内部使用：连接与会话
    # ------------------------------------------------------------------
    CLIENT_CONNECTED_CH = "客户端已连接"
    CLIENT_CONNECTED_EN = "client connected"

    CLIENT_DISCONNECTED_CH = "客户端已断开"
    CLIENT_DISCONNECTED_EN = "client disconnected"

    CLIENT_LIMIT_EXCEEDED_CH = "连接数已达上限，拒绝新连接"
    CLIENT_LIMIT_EXCEEDED_EN = "connection limit reached, new connection rejected"

    HANDLE_CLIENT_MESSAGE_FAIL_CH = "处理客户端消息失败"
    HANDLE_CLIENT_MESSAGE_FAIL_EN = "handle client message fail"

    UNKNOWN_MESSAGE_TYPE_CH = "未知的消息类型"
    UNKNOWN_MESSAGE_TYPE_EN = "unknown message type"

    NO_DEVICE_SELECTED_CH = "没有选中设备"
    NO_DEVICE_SELECTED_EN = "no device selected"

    DEVICE_DATA_TOO_MUCH_CH = "设备数据过多"
    DEVICE_DATA_TOO_MUCH_EN = "device data too much"

    # ------------------------------------------------------------------
    # 框架内部使用：订阅与推送
    # ------------------------------------------------------------------
    SUBSCRIBE_SUCCESS_CH = "订阅成功"
    SUBSCRIBE_SUCCESS_EN = "subscribed successfully"

    SUBSCRIBE_FAIL_CH = "订阅失败"
    SUBSCRIBE_FAIL_EN = "subscription failed"

    UNSUBSCRIBE_SUCCESS_CH = "取消订阅成功"
    UNSUBSCRIBE_SUCCESS_EN = "unsubscribed successfully"

    BROADCAST_INTERVAL_INVALID_CH = "推送间隔不合法"
    BROADCAST_INTERVAL_INVALID_EN = "broadcast interval is invalid"

    BROADCAST_INTERVAL_UPDATED_CH = "推送间隔已更新"
    BROADCAST_INTERVAL_UPDATED_EN = "broadcast interval updated"

    PUSH_DATA_SUCCESS_CH = "数据推送成功"
    PUSH_DATA_SUCCESS_EN = "data pushed successfully"

    PUSH_DATA_FAIL_CH = "数据推送失败"
    PUSH_DATA_FAIL_EN = "data push failed"

    NO_DATA_FOUND_CH = "未查询到数据"
    NO_DATA_FOUND_EN = "no data found"

    # ------------------------------------------------------------------
    # 系统信息（项目定制项，新建项目时替换）
    # ------------------------------------------------------------------
    SYSTEM_NAME_CH = "系统名称：通用WebSocket推送服务"
    SYSTEM_NAME_EN = "System name: generic WebSocket push service"

    SYSTEM_VERSION_CH = "系统版本号：1.00.00"
    SYSTEM_VERSION_EN = "System version: 1.00.00"

    # ------------------------------------------------------------------
    # 业务提示语（示例，按项目保留或删除）
    # 下面是原无人机项目的「数据回放」词条，保留作为「业务提示语该怎么加」的样例
    # ------------------------------------------------------------------
    REVIEW_DATA_PUSH_START_CH = "回放数据开始推送"
    REVIEW_DATA_PUSH_START_EN = "review data push started"

    REVIEW_DATA_PUSH_COMPLETED_CH = "回放数据推送完成"
    REVIEW_DATA_PUSH_COMPLETED_EN = "review data push completed"

    REVIEW_DATA_PAUSE_CH = "回放已暂停"
    REVIEW_DATA_PAUSE_EN = "review paused"

    REVIEW_DATA_CONTINUE_CH = "回放已继续"
    REVIEW_DATA_CONTINUE_EN = "review continued"

    REVIEW_DATA_STOP_CH = "回放已停止"
    REVIEW_DATA_STOP_EN = "review stopped"

    NO_REVIEW_DATA_FOUND_CH = "未查询到回放数据"
    NO_REVIEW_DATA_FOUND_EN = "no review data found"

    SEEK_OUT_OF_RANGE_CH = "跳转位置超出范围"
    SEEK_OUT_OF_RANGE_EN = "seek position is out of range"

    REVIEW_DATA_SEEK_SUCCESS_CH = "回放跳转成功"
    REVIEW_DATA_SEEK_SUCCESS_EN = "review seek succeeded"

    REVIEW_DATA_SEEK_FAIL_CH = "回放跳转失败"
    REVIEW_DATA_SEEK_FAIL_EN = "review seek failed"

    MISSING_SEEK_TO_PARAM_CH = "缺少seek_to参数"
    MISSING_SEEK_TO_PARAM_EN = "missing seek_to parameter"

    INVALID_SEEK_TO_PARAM_CH = "seek_to参数不合法"
    INVALID_SEEK_TO_PARAM_EN = "seek_to parameter is invalid"

    REVIEW_PLAYBACK_RATE_SUCCESS_CH = "回放倍数调整成功"
    REVIEW_PLAYBACK_RATE_SUCCESS_EN = "playback rate adjusted successfully"

    REVIEW_PLAYBACK_RATE_FAIL_CH = "回放倍数调整失败"
    REVIEW_PLAYBACK_RATE_FAIL_EN = "failed to adjust playback rate"

    REVIEW_PLAYBACK_RATE_ADJUSTED_CH = "回放倍数已调整"
    REVIEW_PLAYBACK_RATE_ADJUSTED_EN = "playback rate has been adjusted"
