# -*- coding: utf-8 -*-
# 国际化
# 约定：每条提示必须是成对的 <KEY>_CH / <KEY>_EN，缺一个运行期就会 AttributeError。
#       新增后跑一下自检：python check_localization_keys.py
#       业务自己的提示语建议单独放在本文件末尾的「业务提示语」区，便于版本升级时合并。


class SysInfoEnum:
    # ------------------------------------------------------------------
    # 通用（与 Django 框架模板保持一致，便于跨服务复用）
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
    # 框架内部使用：协议解析
    # ------------------------------------------------------------------
    PKT_HEADER_ERROR_CH = "报文包头错误，已跳过1字节重新对齐"
    PKT_HEADER_ERROR_EN = "packet header error, skipped 1 byte to realign"

    PKT_LENGTH_INSUFFICIENT_CH = "报文长度不足，等待更多数据"
    PKT_LENGTH_INSUFFICIENT_EN = "packet length is insufficient, waiting for more data"

    PKT_VERIFY_FAILED_CH = "报文校验失败，已丢弃"
    PKT_VERIFY_FAILED_EN = "packet verification failed, discarded"

    PKT_PARSE_FAILED_CH = "报文解析失败"
    PKT_PARSE_FAILED_EN = "packet parse failed"

    PKT_UNKNOWN_MSG_ID_CH = "未知的报文ID"
    PKT_UNKNOWN_MSG_ID_EN = "unknown message id"

    # ------------------------------------------------------------------
    # 框架内部使用：连接与线程
    # ------------------------------------------------------------------
    CLIENT_CONNECTED_CH = "客户端已连接"
    CLIENT_CONNECTED_EN = "client connected"

    CLIENT_DISCONNECTED_CH = "客户端已断开"
    CLIENT_DISCONNECTED_EN = "client disconnected"

    CLIENT_FORCED_DISCONNECT_MAX_TIME_CH = "客户端连接时间超过上限，强制断开"
    CLIENT_FORCED_DISCONNECT_MAX_TIME_EN = "client connection exceeded the time limit, forced disconnect"

    CLIENT_FORCED_DISCONNECT_MAX_IDLE_CH = "客户端空闲时间超过上限，强制断开"
    CLIENT_FORCED_DISCONNECT_MAX_IDLE_EN = "client idle time exceeded the limit, forced disconnect"

    DEVICE_NOT_CONNECTED_CH = "设备未连接"
    DEVICE_NOT_CONNECTED_EN = "device not connected"

    # ------------------------------------------------------------------
    # 框架内部使用：Web 控制接口
    # ------------------------------------------------------------------
    SERVER_NOT_STARTED_CH = "服务器未启动"
    SERVER_NOT_STARTED_EN = "server is not started"

    REQUEST_PARAMETER_DOES_NOT_HAVE_FILE_OBJECT_CH = "请求参数中没有文件对象"
    REQUEST_PARAMETER_DOES_NOT_HAVE_FILE_OBJECT_EN = "the request parameter does not have a file object"

    NO_FILE_SELECTED_FOR_UPLOAD_CH = "没有选择要上传的文件"
    NO_FILE_SELECTED_FOR_UPLOAD_EN = "no file selected for upload"

    FILE_TYPE_NOT_ALLOWED_CH = "不允许的文件类型"
    FILE_TYPE_NOT_ALLOWED_EN = "file type is not allowed"

    FILE_UPLOAD_SUCCESS_CH = "文件上传成功"
    FILE_UPLOAD_SUCCESS_EN = "file uploaded successfully"

    FILE_UPLOAD_FAILED_CH = "文件上传失败"
    FILE_UPLOAD_FAILED_EN = "file upload failed"

    FILE_NOT_EXIST_CH = "文件不存在"
    FILE_NOT_EXIST_EN = "file does not exist"

    LOG_FILE_NOT_EXIST_CH = "日志文件不存在"
    LOG_FILE_NOT_EXIST_EN = "log file does not exist"

    COMMAND_NOT_SUPPORTED_CH = "不支持的命令"
    COMMAND_NOT_SUPPORTED_EN = "command is not supported"

    COMMAND_EXECUTE_SUCCESS_CH = "命令执行成功"
    COMMAND_EXECUTE_SUCCESS_EN = "command executed successfully"

    COMMAND_EXECUTE_FAILED_CH = "命令执行失败"
    COMMAND_EXECUTE_FAILED_EN = "command execution failed"

    SEND_MESSAGE_SUCCESS_CH = "消息发送成功"
    SEND_MESSAGE_SUCCESS_EN = "message sent successfully"

    SEND_MESSAGE_FAILED_CH = "消息发送失败"
    SEND_MESSAGE_FAILED_EN = "message sending failed"

    # ------------------------------------------------------------------
    # 系统信息（项目定制项，新建项目时替换）
    # ------------------------------------------------------------------
    SYSTEM_NAME_CH = "系统名称：通用TCP服务"
    SYSTEM_NAME_EN = "System name: generic TCP service"

    SYSTEM_VERSION_CH = "系统版本号：1.00.00"
    SYSTEM_VERSION_EN = "System version: 1.00.00"

    # ------------------------------------------------------------------
    # 业务提示语（示例，按项目保留或删除）
    # 下面是原北斗项目在用的词条，保留作为「业务提示语该怎么加」的样例
    # ------------------------------------------------------------------
    # 参数查询
    PARAM_QUERY_FAIL_CH = "参数查询失败"
    PARAM_QUERY_FAIL_EN = "parameter query failed"

    # 参数设置
    CONFIG_SUCCESS_CH = "参数设置成功"
    CONFIG_SUCCESS_EN = "parameter configuration succeeded"

    CONFIG_FAILED_CH = "参数设置失败"
    CONFIG_FAILED_EN = "parameter configuration failed"

    # 系统复位
    RESET_SUCCESS_CH = "系统复位成功"
    RESET_SUCCESS_EN = "system reset succeeded"

    RESET_FAILED_CH = "系统复位失败"
    RESET_FAILED_EN = "system reset failed"

    # 固件升级
    ENTER_FIRMWARE_UPDATE_MODE_SUCCESS_CH = "进入固件更新模式成功"
    ENTER_FIRMWARE_UPDATE_MODE_SUCCESS_EN = "entered firmware update mode successfully"

    ENTER_FIRMWARE_UPDATE_MODE_FAILED_CH = "进入固件更新模式失败"
    ENTER_FIRMWARE_UPDATE_MODE_FAILED_EN = "failed to enter firmware update mode"

    DOWNLOAD_FIRMWARE_SUCCESS_CH = "固件数据下载成功"
    DOWNLOAD_FIRMWARE_SUCCESS_EN = "firmware data downloaded successfully"

    DOWNLOAD_FIRMWARE_FAILED_CH = "固件数据下载失败"
    DOWNLOAD_FIRMWARE_FAILED_EN = "firmware data download failed"

    UPDATE_FIRMWARE_SUCCESS_CH = "固件更新成功"
    UPDATE_FIRMWARE_SUCCESS_EN = "firmware updated successfully"

    UPDATE_FIRMWARE_FAILED_CH = "固件更新失败"
    UPDATE_FIRMWARE_FAILED_EN = "firmware update failed"

    FILE_TYPE_MUST_BE_BIN_CH = "文件类型必须是bin"
    FILE_TYPE_MUST_BE_BIN_EN = "file type must be bin"

    FIRMWARE_BIN_FILE_SIZE_CANNOT_EXCEED_CH = "固件bin文件大小不能超过"
    FIRMWARE_BIN_FILE_SIZE_CANNOT_EXCEED_EN = "firmware bin file size cannot exceed"
