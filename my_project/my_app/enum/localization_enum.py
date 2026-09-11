# 国际化
# 约定：每条提示语必须是成对的 <KEY>_CH / <KEY>_EN，CommonHelper.get_local_str(KEY, request)
#       会按请求头 Localization(CH/EN) 取对应值，缺一个就会 AttributeError。
# 新增提示语的写法：同时补 _CH 和 _EN 两行，再在业务里用 get_local_str("KEY", request)。


class SysInfoEnum:

    #成功
    SUCCESS_CH = '成功'
    SUCCESS_EN = ' is successful'

    #失败
    FAIL_CH = '失败'
    FAIL_EN = ' is fail'

    #请求成功
    REQUEST_SUCCESS_CH = '请求成功'
    REQUEST_SUCCESS_EN = 'request is successful'

    #新增失败
    ADD_FAIL_CH = '新增失败'
    ADD_FAIL_EN = 'add is fail'

    #操作失败
    OPERATE_FAIL_CH = '操作失败'
    OPERATE_FAIL_EN = 'operate is fail'

    #ID是必传参数
    ID_MUST_CH = "ID是必传参数"
    ID_MUST_EN = "ID is required parameter"


    #page 和size 都是必传参数
    PAGE_AND_SIZE_MUST_CH = "page 和size 都是必传参数"
    PAGE_AND_SIZE_MUST_EN = "page and size are required parameters"

    #size 不可以大于
    SIZE_NOT_MORE_THAN_CH = "size 不可以大于"
    SIZE_NOT_MORE_THAN_EN = "size cannot be greater than "

    #page 或者size 不可以大于0
    PAGE_OR_SIZE_NOT_MORE_THAN_CH = "page 或者size 不可以大于0 "
    PAGE_OR_SIZE_NOT_MORE_THAN_EN = "page or size cannot be greater than 0 "

    ##########################################################################################
    # 创建群组
    ADD_GROUP_CH="新增群组"
    ADD_GROUP_EN="add group"

    # 群组名称是必填参数
    GROUP_NAME_IS_REQUIRED_PARAMETER_CH="群组名称是必填参数"
    GROUP_NAME_IS_REQUIRED_PARAMETER_EN="group name is a required parameter"

    # 群组类型是必填参数
    GROUP_TYPE_IS_REQUIRED_PARAMETER_CH="群组类型是必填参数"
    GROUP_TYPE_IS_REQUIRED_PARAMETER_EN="group type is a required parameter"


    # 群组ID是必填参数
    GROUP_ID_IS_REQUIRED_PARAMETER_CH="群组ID是必填参数"
    GROUP_ID_IS_REQUIRED_PARAMETER_EN="group id is a required parameter"

    # 群组ID不能为空字符串
    GROUP_ID_CANNOT_BE_EMPTY_STRING_CH = "群组ID不能为空字符串"
    GROUP_ID_CANNOT_BE_EMPTY_STRING_EN = "group id cannot be empty string"

    # 至少需要传递一个可更新字段
    AT_LEAST_ONE_UPDATABLE_FIELD_MUST_BE_PROVIDED_CH = "至少需要传递一个可更新字段"
    AT_LEAST_ONE_UPDATABLE_FIELD_MUST_BE_PROVIDED_EN = "at least one updatable field must be provided"

    # 群组名称不能为空
    GROUP_NAME_CANNOT_BE_EMPTY_CH = "群组名称不能为空"
    GROUP_NAME_CANNOT_BE_EMPTY_EN = "group name cannot be empty"

    # 群组类型不能为空
    GROUP_TYPE_CANNOT_BE_EMPTY_CH = "群组类型不能为空"
    GROUP_TYPE_CANNOT_BE_EMPTY_EN = "group type cannot be empty"

    # 新增群组的名称:{}已存在，请换个名称
    ADD_GROUP_EXIST_CH = "新增群组的名称:{}已存在，请换个名称"
    ADD_GROUP_EXIST_EN = "the new group name '{}' already exists, please change the name"



    # 新增群组【{}】成功"
    ADD_GROUP_SUCCESS_CH = "新增群组【{}】成功"
    ADD_GROUP_SUCCESS_EN = "the new group '{}' is added successful"

    # 查询群组
    QUERY_GROUP_CH="查询群组"
    QUERY_GROUP_EN="query group"

    # 查询群组成功
    QUERY_GROUP_SUCCESS_CH="查询群组成功"
    QUERY_GROUP_SUCCESS_EN="query group success"

    # 查询群组失败
    QUERY_GROUP_FAILED_CH="查询群组失败"
    QUERY_GROUP_FAILED_EN="query group failed"


    # 更新群组
    UPDATE_GROUP_CH="更新群组"
    UPDATE_GROUP_EN="update group"

    # 更新群组成功
    UPDATE_GROUP_SUCCESS_CH="更新群组成功"
    UPDATE_GROUP_SUCCESS_EN="update group success"

    # 更新群组失败
    UPDATE_GROUP_FAILED_CH="查询群组失败"
    UPDATE_GROUP_FAILED_EN="query group failed"


    # 删除群组
    DEL_GROUP_CH="删除群组"
    DEL_GROUP_EN="delete group"

    # 删除失败：群组不存在（ID：{}）
    DELETE_GROUP_FAIL_NOT_EXIST_CH = "删除失败：群组不存在（ID：{}）"
    DELETE_GROUP_FAIL_NOT_EXIST_EN = "Deletion is failed: group does not exist (ID: {})"

    # 删除失败：无权限删除他人创建的群组（群组ID：{}，创建者ID：{}）
    DELETE_GROUP_FAIL_NO_PERMISSION_CH = "删除失败：无权限删除他人创建的群组（群组ID：{}，创建者ID：{}）"
    DELETE_GROUP_FAIL_NO_PERMISSION_EN = "Deletion is failed: no permission to delete groups created by others (Group ID: {}, Creator ID: {})"

    # 删除群组成功：ID【{}】，名称【{}】
    DELETE_GROUP_SUCCESS_CH = "删除群组成功：ID【{}】，名称【{}】"
    DELETE_GROUP_SUCCESS_EN = "Group is deleted successfully: ID【{}】, Name【{}】"

    ##########################################################################################

    # 创建基站
    ADD_BASE_STATION_CH = "新增基站"
    ADD_BASE_STATION_EN = "add base station"

    # 基站名称是必填参数
    BASE_STATION_NAME_IS_REQUIRED_PARAMETER_CH = "基站名称是必填参数"
    BASE_STATION_NAME_IS_REQUIRED_PARAMETER_EN = "base station name is a required parameter"

    # 基站类型是必填参数
    BASE_STATION_TYPE_IS_REQUIRED_PARAMETER_CH = "基站类型是必填参数"
    BASE_STATION_TYPE_IS_REQUIRED_PARAMETER_EN = "base station type is a required parameter"

    # 基站ID是必填参数
    BASE_STATION_ID_IS_REQUIRED_PARAMETER_CH = "基站ID是必填参数"
    BASE_STATION_ID_IS_REQUIRED_PARAMETER_EN = "base station id is a required parameter"

    # 基站ID不能为空字符串
    BASE_STATION_ID_CANNOT_BE_EMPTY_STRING_CH = "基站ID不能为空字符串"
    BASE_STATION_ID_CANNOT_BE_EMPTY_STRING_EN = "base station id cannot be empty string"


    # 基站名称不能为空
    BASE_STATION_NAME_CANNOT_BE_EMPTY_CH = "基站名称不能为空"
    BASE_STATION_NAME_CANNOT_BE_EMPTY_EN = "base station name cannot be empty"

    # 基站类型不能为空
    BASE_STATION_TYPE_CANNOT_BE_EMPTY_CH = "基站类型不能为空"
    BASE_STATION_TYPE_CANNOT_BE_EMPTY_EN = "base station type cannot be empty"

    # 新增基站的名称:{}已存在，请换个名称
    ADD_BASE_STATION_NAME_EXIST_CH = "新增基站的设备名称:{}已存在，请换个名称"
    ADD_BASE_STATION_NAME_EXIST_EN = "the new base station name '{}' already exists, please change the name"


    # 新增基站的ID:{}已存在，请换个名称
    ADD_BASE_STATION_ID_EXIST_CH = "新增基站的设备ID:{}已存在，请换个设备ID"
    ADD_BASE_STATION_ID_EXIST_EN = "the new base station id '{}' already exists, please change the device id"

    # 新增基站【{}】成功"
    ADD_BASE_STATION_SUCCESS_CH = "新增基站【{}】成功"
    ADD_BASE_STATION_SUCCESS_EN = "the new base station '{}' is added successful"

    # 查询基站
    QUERY_BASE_STATION_CH = "查询基站"
    QUERY_BASE_STATION_EN = "query base station"

    # 查询基站成功
    QUERY_BASE_STATION_SUCCESS_CH = "查询基站成功"
    QUERY_BASE_STATION_SUCCESS_EN = "query base station success"

    # 查询基站失败
    QUERY_BASE_STATION_FAILED_CH = "查询基站失败:"
    QUERY_BASE_STATION_FAILED_EN = "query base station failed:"

    # 查询基站的上报日志
    QUERY_BASE_STATION_UPLOAD_LOG_CH = "查询基站的上报日志"
    QUERY_BASE_STATION_UPLOAD_LOG_EN = "query base station upload log"

    # 更新基站
    UPDATE_BASE_STATION_CH = "更新基站"
    UPDATE_BASE_STATION_EN = "update base station"



    # 批量更新基站分组
    BATCH_UPDATE_BASE_STATION_GROUP_CH = "批量更新基站分组"
    BATCH_UPDATE_BASE_STATION_GROUP_EN = "batch update base station group"


    # 更新基站成功
    UPDATE_BASE_STATION_SUCCESS_CH = "更新基站成功"
    UPDATE_BASE_STATION_SUCCESS_EN = "update base station is successful"

    # 更新基站失败
    UPDATE_BASE_STATION_FAILED_CH = "查询基站失败"
    UPDATE_BASE_STATION_FAILED_EN = "query base station is failed"

    # 删除基站
    DEL_BASE_STATION_CH = "删除基站"
    DEL_BASE_STATION_EN = "delete base station"

    # 删除失败：基站不存在（ID：{}）
    DELETE_BASE_STATION_FAIL_NOT_EXIST_CH = "删除失败：基站不存在（ID：{}）"
    DELETE_BASE_STATION_FAIL_NOT_EXIST_EN = "Deletion is failed: base station does not exist (ID: {})"

    # 删除失败：无权限删除他人创建的基站（基站ID：{}，创建者ID：{}）
    DELETE_BASE_STATION_FAIL_NO_PERMISSION_CH = "删除失败：无权限删除他人创建的基站（基站ID：{}，创建者ID：{}）"
    DELETE_BASE_STATION_FAIL_NO_PERMISSION_EN = "Deletion is failed: no permission to delete base stations created by others (Group ID: {}, Creator ID: {})"

    # 删除基站成功：ID【{}】，名称【{}】
    DELETE_BASE_STATION_SUCCESS_CH = "删除基站成功：ID【{}】，名称【{}】"
    DELETE_BASE_STATION_SUCCESS_EN = "Group is deleted successfully: ID【{}】, Name【{}】"

    ##########################################################################################

    # 创建终端
    ADD_DRONE_CH = "新增终端"
    ADD_DRONE_EN = "add terminal"

    # 终端名称是必填参数
    DRONE_NAME_IS_REQUIRED_PARAMETER_CH = "终端名称是必填参数"
    DRONE_NAME_IS_REQUIRED_PARAMETER_EN = "terminal name is a required parameter"

    # 终端类型是必填参数
    DRONE_TYPE_IS_REQUIRED_PARAMETER_CH = "终端类型是必填参数"
    DRONE_TYPE_IS_REQUIRED_PARAMETER_EN = "terminal type is a required parameter"

    # 终端ID是必填参数
    DRONE_ID_IS_REQUIRED_PARAMETER_CH = "终端ID是必填参数"
    DRONE_ID_IS_REQUIRED_PARAMETER_EN = "terminal id is a required parameter"

    # 终端ID不能为空字符串
    DRONE_ID_CANNOT_BE_EMPTY_STRING_CH = "终端ID不能为空字符串"
    DRONE_ID_CANNOT_BE_EMPTY_STRING_EN = "terminal id cannot be empty string"



    # 终端名称不能为空
    DRONE_NAME_CANNOT_BE_EMPTY_CH = "终端名称不能为空"
    DRONE_NAME_CANNOT_BE_EMPTY_EN = "terminal name cannot be empty"

    # 终端类型不能为空
    DRONE_TYPE_CANNOT_BE_EMPTY_CH = "终端类型不能为空"
    DRONE_TYPE_CANNOT_BE_EMPTY_EN = "terminal type cannot be empty"

    #新增终端的设备ID:{}已存在，请换个ID
    ADD_DRONE_DEVICE_ID_EXIST_CH = "新增终端的设备ID:{}已存在，请换个ID"
    ADD_DRONE_DEVICE_ID_EXIST_EN = "The device ID '{}' for the new terminal already exists, please change the ID"

    # 新增终端的设备名称:{}已存在，请换个名称
    ADD_DRONE_DEVICE_NAME_EXIST_CH = "新增终端的设备名称:{}已存在，请换个名称"
    ADD_DRONE_DEVICE_NAME_EXIST_EN = "The device name '{}' for the new terminal already exists, please change the name"

    # 新增终端的名称:{}已存在，请换个名称
    ADD_DRONE_EXIST_CH = "新增终端的名称:{}已存在，请换个名称"
    ADD_DRONE_EXIST_EN = "the new terminal name '{}' already exists, please change the name"


    # 新增终端【{}】成功"
    ADD_DRONE_SUCCESS_CH = "新增终端【{}】成功"
    ADD_DRONE_SUCCESS_EN = "the new terminal '{}' is added successful"

    # 查询终端
    QUERY_DRONE_CH = "查询终端"
    QUERY_DRONE_EN = "query terminal"

    # 查询终端成功
    QUERY_DRONE_SUCCESS_CH = "查询终端成功"
    QUERY_DRONE_SUCCESS_EN = "query terminal is successful"

    # 查询终端失败
    QUERY_DRONE_FAILED_CH = "查询终端失败"
    QUERY_DRONE_FAILED_EN = "query terminal is failed"

    # 更新终端
    UPDATE_DRONE_CH = "更新终端"
    UPDATE_DRONE_EN = "update terminal"

    # 批量更新终端分组
    BATCH_UPDATE_DRONE_GROUP_CH = "批量更新终端分组"
    BATCH_UPDATE_DRONE_GROUP_EN = "batch update terminal group"

    # 更新终端成功
    UPDATE_DRONE_SUCCESS_CH = "更新终端成功"
    UPDATE_DRONE_SUCCESS_EN = "update terminal is successful"

    # 更新终端失败
    UPDATE_DRONE_FAILED_CH = "查询终端失败"
    UPDATE_DRONE_FAILED_EN = "query terminal is failed"

    # 历史轨迹
    HISTORY_TRACK_CH = "历史轨迹"
    HISTORY_TRACK_EN = "history track"

    # 删除终端
    DEL_DRONE_CH = "删除终端"
    DEL_DRONE_EN = "delete terminal"

    # 删除失败：终端不存在（ID：{}）
    DELETE_DRONE_FAIL_NOT_EXIST_CH = "删除失败：终端不存在（ID：{}）"
    DELETE_DRONE_FAIL_NOT_EXIST_EN = "Deletion is failed: terminal does not exist (ID: {})"

    # 删除失败：无权限删除他人创建的终端（终端ID：{}，创建者ID：{}）
    DELETE_DRONE_FAIL_NO_PERMISSION_CH = "删除失败：无权限删除他人创建的终端（终端ID：{}，创建者ID：{}）"
    DELETE_DRONE_FAIL_NO_PERMISSION_EN = "Deletion is failed: no permission to delete terminals created by others (terminal ID: {}, Creator ID: {})"

    # 删除终端成功：ID【{}】，名称【{}】
    DELETE_DRONE_SUCCESS_CH = "删除终端成功：ID【{}】，名称【{}】"
    DELETE_DRONE_SUCCESS_EN = "Group is deleted successfully: ID【{}】, Name【{}】"

    ##########################################################################################

    # 实时监控
    REAL_TIME_MONITORING_CH = "实时监控"
    REAL_TIME_MONITORING_EN = "real-time monitoring"

    # 获取实时监控数据成功
    OBTAIN_REAL_TIME_MONITORING_DATA_SUCCESS_CH = "获取实时监控数据成功"
    OBTAIN_REAL_TIME_MONITORING_DATA_SUCCESS_EN = "obtain real-time monitoring data is successful"

    # 获取实时监控数据失败
    OBTAIN_REAL_TIME_MONITORING_DATA_FAIL_CH = "获取实时监控数据失败"
    OBTAIN_REAL_TIME_MONITORING_DATA_FAIL_EN = "obtain real-time monitoring data is failed"

    # 查询终端的上报日志
    QUERY_TERMINAL_UPLOAD_LOG_CH = "查询终端的上报日志"
    QUERY_TERMINAL_UPLOAD_LOG_EN = "query terminal upload log"

    # 查询成功
    QUERY_SUCCESS_CH = "查询成功"
    QUERY_SUCCESS_EN = "query success"

    # 查询失败
    QUERY_FAILED_CH = "查询失败"
    QUERY_FAILED_EN = "query failed"

    # 更新的设备ID:{}已存在，请换个ID
    UPDATE_DEVICE_ID_EXIST_CH = "更新的设备ID:{}已存在，请换个ID"
    UPDATE_DEVICE_ID_EXIST_EN = "The updated device ID '{}' already exists, please change the ID"

    # 更新的设备名称:{}已存在，请换个名称
    UPDATE_DEVICE_NAME_EXIST_CH = "更新的设备名称:{}已存在，请换个名称"
    UPDATE_DEVICE_NAME_EXIST_EN = "The updated device name '{}' already exists, please change the name"

    # 批量更新失败：data必须为非空数组
    BATCH_UPDATE_FAILED_DATA_MUST_BE_NON_EMPTY_ARRAY_CH = "批量更新失败：data必须为非空数组"
    BATCH_UPDATE_FAILED_DATA_MUST_BE_NON_EMPTY_ARRAY_EN = "batch update is failed: data must be non-empty array"

    # 批量更新成功：共更新{}条数据
    BATCH_UPDATE_SUCCESS_CH = "批量更新成功：共更新{}条数据"
    BATCH_UPDATE_SUCCESS_EN = "Batch update is successful: {} records updated in total"

    # 批量更新部分成功：成功{}条，失败{}条
    BATCH_UPDATE_PARTIAL_SUCCESS_CH = "批量更新部分成功：成功{}条，失败{}条"
    BATCH_UPDATE_PARTIAL_SUCCESS_EN = "Batch update is partially successful: {} succeeded, {} failed"

    # 批量更新失败：{}
    BATCH_UPDATE_FAIL_CH = "批量更新失败：{}"
    BATCH_UPDATE_FAIL_EN = "Batch update is failed: {}"

    # 批量更新失败，原因：
    BATCH_UPDATE_FAIL_WITH_REASON_CH = "批量更新失败，原因："
    BATCH_UPDATE_FAIL_WITH_REASON_EN = "Batch update is failed, reason: "

    # 更新成功：ID【{}】，旧名称【{}】→ 新名称【{}】
    UPDATE_SUCCESS_CH = "更新成功：ID【{}】，旧名称【{}】→ 新名称【{}】"
    UPDATE_SUCCESS_EN = "Update is successful: ID【{}】, Old Name【{}】 → New Name【{}】"


    # 无ID数据
    NO_ID_DATA_CH = "无ID数据"
    NO_ID_DATA_EN = "no id data"

    # 验证失败
    VALIDATION_FAILED_CH = "验证失败"
    VALIDATION_FAILED_EN = "validation failed"

    # 数据不存在
    DATA_DOES_NOT_EXIST_CH = "数据不存在"
    DATA_DOES_NOT_EXIST_EN = "data does not exist"

    # 更新失败
    UPDATE_FAILED_CH = "更新失败"
    UPDATE_FAILED_EN = "update failed"

    # 更新成功
    UPDATE_SUCCESS2_CH = "更新成功"
    UPDATE_SUCCESS2_EN = "update success"

    # 更新失败，原因：
    UPDATE_FAILED_REASON_CH = "更新失败，原因："
    UPDATE_FAILED_REASON_EN = "update failed, reason:"

    # 数据验证失败
    DATA_VALIDATION_FAILED_CH = "数据验证失败"
    DATA_VALIDATION_FAILED_EN = "data validation is failed"

    # ID不能为空字符串
    ID_CANNOT_BE_EMPTY_STRING_CH = "ID不能为空字符串"
    ID_CANNOT_BE_EMPTY_STRING_EN = "id cannot be empty string"

    # ID是必填参数
    ID_IS_REQUIRED_PARAMETER_CH = "ID是必填参数"
    ID_IS_REQUIRED_PARAMETER_EN = "id is required parameter"

    # 设备ID不能为空
    DEVICE_ID_CANNOT_BE_EMPTY_CH = "设备ID不能为空"
    DEVICE_ID_CANNOT_BE_EMPTY_EN = "device id cannot be empty"

    # 设备ID是必填参数
    DEVICE_ID_IS_REQUIRED_PARAMETER_CH = "设备ID是必填参数"
    DEVICE_ID_IS_REQUIRED_PARAMETER_EN = "device id is a required parameter"

    # 设备名称不能为空
    DEVICE_NAME_CANNOT_BE_EMPTY_CH = "设备名称不能为空"
    DEVICE_NAME_CANNOT_BE_EMPTY_EN = "device name cannot be empty"

    # 设备名称是必填参数
    DEVICE_NAME_IS_REQUIRED_PARAMETER_CH = "设备名称是必填参数"
    DEVICE_NAME_IS_REQUIRED_PARAMETER_EN = "device name is a required parameter"

    # 删除失败：数据不存在（ID：{}）
    DELETE_FAIL_DATA_NOT_EXIST_CH = "删除失败：数据不存在（ID：{}）"
    DELETE_FAIL_DATA_NOT_EXIST_EN = "Deletion is failed: data does not exist (ID: {})"

    # 删除数据失败，原因：
    DELETE_DATA_FAILED_REASON_CH = "删除数据失败，原因："
    DELETE_DATA_FAILED_REASON_EN = "delete data is failed, reason:"

    # 删除成功：ID【{}】，名称【{}】
    DELETE_SUCCESS_CH = "删除成功：ID【{}】，名称【{}】"
    DELETE_SUCCESS_EN = "Delete data is successful: ID【{}】, Name【{}】"

    #{}失败，可能原因是{}
    FAIL_REASON_CH = "{}失败，可能原因是{}"
    FAIL_REASON_EN = "{} is failed, the possible reason is {}"

    ##########################################################################################
    #上传矢量文件
    UPLOAD_VECTOR_FILE_CH = "上传矢量文件"
    UPLOAD_VECTOR_FILE_EN = "upload vector file"

    #更新数据名称
    UPDATE_DATA_NAME_CH = "更新数据名称"
    UPDATE_DATA_NAME_EN = "update data name"

    # 更新的数据名称:{}已存在，请换个名称
    UPDATE_DATA_NAME_EXIST_CH = "更新的数据名称:{}已存在，请换个名称"
    UPDATE_DATA_NAME_EXIST_EN = "the updated data name '{}' already exists, please change the name"

    #更新数据里的主键ID号:{}不存在，请换个ID号
    UPDATE_DATA_ID_NOT_EXIST_CH = "更新数据里的主键ID号:{}不存在，请换个ID号"
    UPDATE_DATA_ID_NOT_EXIST_EN = "the primary key ID number '{}' in the updated data does not exist, please change the ID number"



    #上传文件
    UPLOAD_FILE_CH = "上传文件"
    UPLOAD_FILE_EN = "upload file"

    #上传TIF文件
    UPLOAD_TIF_FILE_CH = "上传TIF文件"
    UPLOAD_TIF_FILE_EN = "upload tif file"

    #请选择要上传的文件
    PLEASE_SELECT_FILE_TO_UPLOAD_CH = "请选择要上传的文件"
    PLEASE_SELECT_FILE_TO_UPLOAD_EN = "please select the file to upload"

    #上传文件成功
    UPLOAD_FILE_SUCCESS_CH = "上传文件成功"
    UPLOAD_FILE_SUCCESS_EN = "upload file success"

    #下载数据
    DOWNLOAD_DATA_CH = "下载数据"
    DOWNLOAD_DATA_EN = "download data"

    #删除数据
    DELETE_DATA_CH = "删除数据"
    DELETE_DATA_EN = "delete data"

    ##########################################################################################
    #获取全国的分地区分省数据失败
    GET_NATIONAL_DATA_BY_PROVINCE_FAILED_CH = "获取全国的分地区分省数据失败"
    GET_NATIONAL_DATA_BY_PROVINCE_FAILED_EN = "get national data by province failed"

    #通过省份获取地市数据失败
    GET_NATIONAL_DATA_BY_CITY_FAILED_CH = "通过省份获取地市数据失败"
    GET_NATIONAL_DATA_BY_CITY_FAILED_EN = "get national data by city failed"

    #通过地市获取区县数据失败
    GET_NATIONAL_DATA_BY_COUNTY_FAILED_CH = "通过地市获取区县数据失败"
    GET_NATIONAL_DATA_BY_COUNTY_FAILED_EN = "get national data by county failed"

    # 获取上传文件信息成功
    GET_UPLOAD_FILE_INFO_SUCCESS_CH = "获取上传文件信息成功"
    GET_UPLOAD_FILE_INFO_SUCCESS_EN = "get upload file info success"

    # 找不到该上传文件
    UPLOAD_FILE_NOT_FOUND_CH = "找不到该上传文件"
    UPLOAD_FILE_NOT_FOUND_EN = "upload file is not found"

 ##########################################################################################

    # 用户登录
    USER_LOGIN_CH = "用户登录"
    USER_LOGIN_EN = "user login"

    # 用户登录成功
    USER_LOGIN_SUCCESS_CH = "用户登录成功"
    USER_LOGIN_SUCCESS_EN = "User login successful"

    # 用户被禁用！
    USER_DEACTIVATED_CH = "用户被禁用！"
    USER_DEACTIVATED_EN = "User is deactivated!"

    # 账号已被锁定，请在{}后重试。
    ACCOUNT_LOCKED_RETRY_AFTER_CH = "账号已被锁定，请在{}后重试。"
    ACCOUNT_LOCKED_RETRY_AFTER_EN = "Account is locked, please try again after {}."

    # 用户名或密码不对
    INCORRECT_USERNAME_OR_PASSWORD_CH = "用户名或密码不对!"
    INCORRECT_USERNAME_OR_PASSWORD_EN = "Incorrect username or password!"

    # 验证码不对!
    INCORRECT_VERIFICATION_CODE_CH = "验证码不对!"
    INCORRECT_VERIFICATION_CODE_EN = "Incorrect verification code!"

    # 验证码匹配有问题
    VERIFICATION_CODE_MISMATCH_CH = "验证码匹配有问题"
    VERIFICATION_CODE_MISMATCH_EN = "Verification code mismatch issue"

    # 接口请求失败，缺少client_time!
    API_REQUEST_FAILED_MISSING_CLIENT_TIME_CH="接口请求失败，缺少client_time!"
    API_REQUEST_FAILED_MISSING_CLIENT_TIME_EN="api request failed, missing client_time!"

    # 没有找到许可文件，请联系管理员!
    LICENSE_FILE_NOT_FOUND_PLEASE_CONTACT_ADMIN_CH = "没有找到许可文件，请联系管理员!"
    LICENSE_FILE_NOT_FOUND_PLEASE_CONTACT_ADMIN_EN = "license file not found, please contact admin!"

    # 用户已在别处登录
    USER_LOGGED_IN_ELSEWHERE_CH = "用户已在别处登录!"
    USER_LOGGED_IN_ELSEWHERE_EN = "user logged in elsewhere!"

    # 没有这个用户
    NO_SUCH_USER_CH = "没有这个用户"
    NO_SUCH_USER_EN = "no such user"

    # 用户名不正确
    INCORRECT_USERNAME_CH = "用户名不正确"
    INCORRECT_USERNAME_EN = "incorrect username"

    # 许可已过期，请联系管理员!
    LICENSE_EXPIRED_PLEASE_CONTACT_ADMIN_CH = "许可已过期，请联系管理员!"
    LICENSE_EXPIRED_PLEASE_CONTACT_ADMIN_EN = "license expired, please contact admin!"

    # parent_id 是必填参数
    PARENT_ID_IS_REQUIRED_PARAMETER_CH="parent_id 是必填参数"
    PARENT_ID_IS_REQUIRED_PARAMETER_EN="parent_id is required parameter"

    # 新增部门:{}成功
    ADD_DEPARTMENT_SUCCESS_CH = "新增部门:{}成功"
    ADD_DEPARTMENT_SUCCESS_EN = "Department is added successfully: {}"


    # 新增部门:{}失败，原因是{}
    ADD_DEPARTMENT_FAIL_CH = "新增部门:{}失败，原因是{}"
    ADD_DEPARTMENT_FAIL_EN = "Failed to add department: {}, reason: {}"

    # 修改部门成功
    MODIFY_DEPARTMENT_SUCCESS_CH="修改部门成功"
    MODIFY_DEPARTMENT_SUCCESS_EN="modify department success"

    # 修改部门:{}失败，原因是{}
    UPDATE_DEPARTMENT_FAIL_CH = "修改部门:{}失败，原因是{}"
    UPDATE_DEPARTMENT_FAIL_EN = "Failed to update department: {}, reason: {}"

    # 获取部门列表数据
    GET_DEPARTMENT_LIST_DATA_CH = "获取部门列表数据"
    GET_DEPARTMENT_LIST_DATA_EN = "Get department list data"

    # 获取部门列表数据失败，原因是：
    GET_DEPARTMENT_LIST_DATA_FAIL_CH = "获取部门列表数据失败，原因是："
    GET_DEPARTMENT_LIST_DATA_FAIL_EN = "Failed to get department list data, reason:"

    # 正常
    NORMAL_CH = "正常"
    NORMAL_EN = "Normal"

    # 停用
    DEACTIVATED_CH = "停用"
    DEACTIVATED_EN = "Deactivated"

    # 设置部门状态成功
    SET_DEPARTMENT_STATUS_SUCCESS_CH = "设置部门状态成功"
    SET_DEPARTMENT_STATUS_SUCCESS_EN = "Department status is set successfully"

    # 设置部门状态失败
    SET_DEPARTMENT_STATUS_FAIL_CH = "设置部门状态失败"
    SET_DEPARTMENT_STATUS_FAIL_EN = "Department status is set failed"

    # 删除成功，包括本级及下级部门：{}
    DELETE_DEPARTMENT_SUCCESS_CH = "删除成功，包括本级及下级部门：{}"
    DELETE_DEPARTMENT_SUCCESS_EN = "Successfully deleted, including this level and subordinate departments: {}"

    # 删除部门失败
    DELETE_DEPARTMENT_FAIL_CH = "删除部门失败"
    DELETE_DEPARTMENT_FAIL_EN = "Failed to delete department"

    # {}(编号为{})成功
    OPERATION_SUCCESS_WITH_ID_CH = "{}(编号为{})成功"
    OPERATION_SUCCESS_WITH_ID_EN = "{}(ID: {}) is successful"

    # {}(编号为{})失败，原因为：{}
    OPERATION_FAIL_WITH_ID_CH = "{}(编号为{})失败，原因为：{}"
    OPERATION_FAIL_WITH_ID_EN = "{}(ID: {}) is failed, reason: {}"

    # 删除日志
    DELETE_LOG_CH = "删除日志"
    DELETE_LOG_EN = "Delete logs"

    # 新增的菜单名:{}已存在，请换个名称
    ADD_MENU_NAME_EXIST_CH = "新增的菜单名:{}已存在，请换个名称"
    ADD_MENU_NAME_EXIST_EN = "The new menu name '{}' already exists, please use a different name"

    # 创建菜单成功
    CREATE_MENU_SUCCESS_CH = "创建菜单成功"
    CREATE_MENU_SUCCESS_EN = "Menu is created successfully"

    # 新增菜单
    ADD_MENU_CH = "新增菜单"
    ADD_MENU_EN = "Add menu"

    # 修改菜单
    UPDATE_MENU_CH = "修改菜单"
    UPDATE_MENU_EN = "Update menu"

    # 更新的菜单名:{}已存在，请换个名称
    UPDATE_MENU_NAME_EXIST_CH = "更新的菜单名:{}已存在，请换个名称"
    UPDATE_MENU_NAME_EXIST_EN = "The updated menu name '{}' already exists, please change the name"

    # 更新菜单成功
    UPDATE_MENU_SUCCESS_CH = "更新菜单成功"
    UPDATE_MENU_SUCCESS_EN = "Menu is updated successfully"

    # 删除菜单
    DELETE_MENU_CH = "删除菜单"
    DELETE_MENU_EN = "Delete menu"

    # 新增的角色名:{}已存在，请换个名称
    ADD_ROLE_NAME_EXIST_CH = "新增的角色名:{}已存在，请换个名称"
    ADD_ROLE_NAME_EXIST_EN = "The new role name '{}' already exists, please use a different name"

    # 新增角色:{}成功
    ADD_ROLE_SUCCESS_CH = "新增角色:{}成功"
    ADD_ROLE_SUCCESS_EN = "Role is added successfully: {}"

    # 新增角色:{}失败，原因是{}
    ADD_ROLE_FAIL_CH = "新增角色:{}失败，原因是{}"
    ADD_ROLE_FAIL_EN = "Failed to add role: {}, reason: {}"

    # 更新的角色名:{}已存在，请换个名称
    UPDATE_ROLE_NAME_EXIST_CH = "更新的角色名:{}已存在，请换个名称"
    UPDATE_ROLE_NAME_EXIST_EN = "The updated role name '{}' already exists, please change the name"

    # 修改角色成功
    UPDATE_ROLE_SUCCESS_CH = "修改角色成功"
    UPDATE_ROLE_SUCCESS_EN = "Role is updated successfully"

    # 修改角色:{}失败，原因是{}
    UPDATE_ROLE_FAIL_CH = "修改角色:{}失败，原因是{}"
    UPDATE_ROLE_FAIL_EN = "Failed to update role '{}', reason: {}"

    # 删除角色
    DELETE_ROLE_CH = "删除角色"
    DELETE_ROLE_EN = "Delete role"

    # 获取角色列表数据失败
    GET_ROLE_LIST_DATA_FAIL_CH = "获取角色列表数据失败"
    GET_ROLE_LIST_DATA_FAIL_EN = "Failed to get role list data"

    # 删除用户
    DELETE_USER_CH = "删除用户"
    DELETE_USER_EN = "Delete user"

    # 新增的用户名:{}已存在，请换个名称
    ADD_USERNAME_EXIST_CH = "新增的用户名:{}已存在，请换个名称"
    ADD_USERNAME_EXIST_EN = "The new username '{}' already exists, please use a different name"

    # 新增用户:{}成功
    ADD_USER_SUCCESS_CH = "新增用户:{}成功"
    ADD_USER_SUCCESS_EN = "User added successfully: {}"

    # 新增用户:{}失败，原因是{}
    ADD_USER_FAIL_CH = "新增用户:{}失败，原因是{}"
    ADD_USER_FAIL_EN = "Failed to add user '{}', reason: {}"

    # 更新的用户名:{}已存在，请换个名称
    UPDATE_USERNAME_EXIST_CH = "更新的用户名:{}已存在，请换个名称"
    UPDATE_USERNAME_EXIST_EN = "The updated username '{}' already exists, please change the name"

    # 修改用户成功
    UPDATE_USER_SUCCESS_CH = "修改用户成功"
    UPDATE_USER_SUCCESS_EN = "User is updated successfully"

    # 修改用户:{}失败，原因是{}
    UPDATE_USER_FAIL_CH = "修改用户:{}失败，原因是{}"
    UPDATE_USER_FAIL_EN = "Failed to update user: {}, reason: {}"

    # 获取用户列表数据
    GET_USER_LIST_DATA_CH = "获取用户列表数据"
    GET_USER_LIST_DATA_EN = "Get user list data"

    # 获取上传文件的信息
    GET_UPLOADED_FILE_INFO_CH = "获取上传文件的信息"
    GET_UPLOADED_FILE_INFO_EN = "Get uploaded file information"

    # 获取用户详情
    GET_USER_DETAILS_CH = "获取用户详情"
    GET_USER_DETAILS_EN = "Get user details"

    # 通过用户token获取用户信息
    GET_USER_INFO_BY_TOKEN_CH = "通过用户token获取用户信息"
    GET_USER_INFO_BY_TOKEN_EN = "Get user information by user token"

    # 设置用户状态
    SET_USER_STATUS_CH = "设置用户状态"
    SET_USER_STATUS_EN = "Set user status"

    # 设置用户状态成功
    SET_USER_STATUS_SUCCESS_CH = "设置用户状态成功"
    SET_USER_STATUS_SUCCESS_EN = "User status is set successfully"

    # 添加数据字典
    ADD_DATA_DICTIONARY_CH = "添加数据字典"
    ADD_DATA_DICTIONARY_EN = "Add data dictionary"

    # 添加数据字典失败
    ADD_DATA_DICTIONARY_FAIL_CH = "添加数据字典失败"
    ADD_DATA_DICTIONARY_FAIL_EN = "Failed to add data dictionary"

    # 修改数据字典
    UPDATE_DATA_DICTIONARY_CH = "修改数据字典"
    UPDATE_DATA_DICTIONARY_EN = "Update data dictionary"

    # 修改数据字典失败
    UPDATE_DATA_DICTIONARY_FAIL_CH = "修改数据字典失败"
    UPDATE_DATA_DICTIONARY_FAIL_EN = "Failed to update data dictionary"

    # 删除数据字典
    DELETE_DATA_DICTIONARY_CH = "删除数据字典"
    DELETE_DATA_DICTIONARY_EN = "Delete data dictionary"

    # 删除数据字典失败
    DELETE_DATA_DICTIONARY_FAIL_CH = "删除数据字典失败"
    DELETE_DATA_DICTIONARY_FAIL_EN = "Failed to delete data dictionary"

    # 通过编号获取数据字典详情
    GET_DATA_DICTIONARY_DETAILS_BY_ID_CH = "通过编号获取数据字典详情"
    GET_DATA_DICTIONARY_DETAILS_BY_ID_EN = "Get data dictionary details by ID"

    # 通过编号获取数据字典详情失败
    GET_DATA_DICTIONARY_DETAILS_BY_ID_FAIL_CH = "通过编号获取数据字典详情失败"
    GET_DATA_DICTIONARY_DETAILS_BY_ID_FAIL_EN = "Failed to get data dictionary details by ID"

    # 获取数据字典类别下拉
    GET_DATA_DICTIONARY_CATEGORY_DROPDOWN_CH = "获取数据字典类别下拉"
    GET_DATA_DICTIONARY_CATEGORY_DROPDOWN_EN = "Get data dictionary category dropdown"

    # 获取数据字典类别下拉失败
    GET_DATA_DICTIONARY_CATEGORY_DROPDOWN_FAIL_CH = "获取数据字典类别下拉失败"
    GET_DATA_DICTIONARY_CATEGORY_DROPDOWN_FAIL_EN = "Failed to get data dictionary category dropdown"

    # 查询获取数据字典列表
    QUERY_DATA_DICTIONARY_LIST_CH = "查询获取数据字典列表"
    QUERY_DATA_DICTIONARY_LIST_EN = "Query and get data dictionary list"

    # 查询获取数据字典列表失败
    QUERY_DATA_DICTIONARY_LIST_FAIL_CH = "查询获取数据字典列表失败"
    QUERY_DATA_DICTIONARY_LIST_FAIL_EN = "Failed to query and get data dictionary list"

    # 删除用户消息
    DELETE_USER_MESSAGE_CH = "删除用户消息"
    DELETE_USER_MESSAGE_EN = "Delete user message"

    # 删除用户消息失败
    DELETE_USER_MESSAGE_FAIL_CH = "删除用户消息失败"
    DELETE_USER_MESSAGE_FAIL_EN = "Failed to delete user message"

    # 查询获取消息列表
    QUERY_MESSAGE_LIST_CH = "查询获取消息列表"
    QUERY_MESSAGE_LIST_EN = "Query and get message list"

    # 查询获取消息列表失败
    QUERY_MESSAGE_LIST_FAIL_CH = "查询获取消息列表失败"
    QUERY_MESSAGE_LIST_FAIL_EN = "Failed to query and get message list"

    # 新增参数
    ADD_PARAMETER_CH = "新增参数"
    ADD_PARAMETER_EN = "Add parameter"

    # 新增参数成功
    ADD_PARAMETER_SUCCESS_CH = "新增参数成功"
    ADD_PARAMETER_SUCCESS_EN = "Parameter is added successfully"

    # 新增的参数英文名:{}已存在，请换个名称
    ADD_PARAMETER_EN_NAME_EXIST_CH = "新增的参数英文名:{}已存在，请换个名称"
    ADD_PARAMETER_EN_NAME_EXIST_EN = "The new parameter English name '{}' already exists, please use a different name"

    # 修改参数
    UPDATE_PARAMETER_CH = "修改参数"
    UPDATE_PARAMETER_EN = "Update parameter"

    # 修改参数成功
    UPDATE_PARAMETER_SUCCESS_CH = "修改参数成功"
    UPDATE_PARAMETER_SUCCESS_EN = "Parameter updated successfully"


    # 更新的参数英文名:{}已存在，请换个名称
    UPDATE_PARAMETER_EN_NAME_EXIST_CH = "更新的参数英文名:{}已存在，请换个名称"
    UPDATE_PARAMETER_EN_NAME_EXIST_EN = "The updated parameter English name '{}' already exists, please change the name"

    # 删除参数
    DELETE_PARAMETER_CH = "删除参数"
    DELETE_PARAMETER_EN = "Delete parameter"

    # 获取终端显示的地图范围失败
    GET_TERMINAL_MAP_RANGE_FAILED_CH = "获取终端显示的地图范围失败"
    GET_TERMINAL_MAP_RANGE_FAILED_EN = "Failed to get the map range displayed by the terminal"

    # 获取终端显示的地图范围成功
    GET_TERMINAL_MAP_RANGE_SUCCESS_CH = "获取终端显示的地图范围成功"
    GET_TERMINAL_MAP_RANGE_SUCCESS_EN = "Successfully obtained the map range displayed by the terminal"

    # 获取群组下的所有终端显示的地图范围失败
    GET_GROUP_TERMINAL_MAP_RANGE_FAILED_CH = "获取群组下的所有终端显示的地图范围失败"
    GET_GROUP_TERMINAL_MAP_RANGE_FAILED_EN = "Failed to get the map range displayed by all terminals in the group"

    # 获取群组下的所有终端显示的地图范围成功
    GET_GROUP_TERMINAL_MAP_RANGE_SUCCESS_CH = "获取群组下的所有终端显示的地图范围成功"
    GET_GROUP_TERMINAL_MAP_RANGE_SUCCESS_EN = "Successfully obtained the map range displayed by all terminals in the group"

    # 获取基站显示的地图范围失败
    GET_BASE_STATION_MAP_RANGE_FAILED_CH = "获取基站显示的地图范围失败"
    GET_BASE_STATION_MAP_RANGE_FAILED_EN = "Failed to get the map range displayed by the base station"

    # 获取基站显示的地图范围成功
    GET_BASE_STATION_MAP_RANGE_SUCCESS_CH = "获取基站显示的地图范围成功"
    GET_BASE_STATION_MAP_RANGE_SUCCESS_EN = "Successfully obtained the map range displayed by the base station"

    # 获取群组下的所有基站显示的地图范围失败
    GET_GROUP_BASE_STATION_MAP_RANGE_FAILED_CH = "获取群组下的所有基站显示的地图范围失败"
    GET_GROUP_BASE_STATION_MAP_RANGE_FAILED_EN = "Failed to get the map range displayed by all base stations in the group"

    # 获取群组下的所有基站显示的地图范围成功
    GET_GROUP_BASE_STATION_MAP_RANGE_SUCCESS_CH = "获取群组下的所有基站显示的地图范围成功"
    GET_GROUP_BASE_STATION_MAP_RANGE_SUCCESS_EN = "Successfully obtained the map range displayed by all base stations in the group"

    # 获取所有设备的地图显示范围成功
    GET_ALL_DEVICE_MAP_RANGE_SUCCESS_CH = "获取所有设备的地图显示范围成功"
    GET_ALL_DEVICE_MAP_RANGE_SUCCESS_EN = "Successfully obtained the map display range of all devices"
    # 获取所有设备的地图显示范围失败
    GET_ALL_DEVICE_MAP_RANGE_FAILED_CH = "获取所有设备的地图显示范围失败"
    GET_ALL_DEVICE_MAP_RANGE_FAILED_EN = "Failed to get the map display range of all devices"

    #获取所有终端的地图显示范围成功
    GET_ALL_TERMINAL_MAP_RANGE_SUCCESS_CH = "获取所有终端的地图显示范围成功"
    GET_ALL_TERMINAL_MAP_RANGE_SUCCESS_EN = "Successfully obtained the map display range of all terminals"

    #获取所有终端的地图显示范围失败
    GET_ALL_TERMINAL_MAP_RANGE_FAILED_CH = "获取所有终端的地图显示范围失败"
    GET_ALL_TERMINAL_MAP_RANGE_FAILED_EN = "Failed to get the map display range of all terminals"

    #获取所有基站的地图显示范围成功
    GET_ALL_BASE_STATION_MAP_RANGE_SUCCESS_CH = "获取所有基站的地图显示范围成功"
    GET_ALL_BASE_STATION_MAP_RANGE_SUCCESS_EN = "Successfully obtained the map display range of all base stations"
    #获取所有基站的地图显示范围失败
    GET_ALL_BASE_STATION_MAP_RANGE_FAILED_CH = "获取所有基站的地图显示范围失败"
    GET_ALL_BASE_STATION_MAP_RANGE_FAILED_EN = "Failed to get the map display range of all base stations"


    # 获取终端参数
    GET_TERMINAL_PARAMETER_CH = "获取终端参数"
    GET_TERMINAL_PARAMETER_EN = "Get terminal parameters"

    # 导出基站的上报日志
    EXPORT_BASE_STATION_REPORT_LOG_CH = "导出基站的上报日志"
    EXPORT_BASE_STATION_REPORT_LOG_EN = "Export base station report log"

    # 导出基站的上报日志成功
    EXPORT_BASE_STATION_REPORT_LOG_SUCCESS_CH = "导出基站的上报日志成功"
    EXPORT_BASE_STATION_REPORT_LOG_SUCCESS_EN = "Successfully exported base station report log"

    # 导出基站的上报日志失败
    EXPORT_BASE_STATION_REPORT_LOG_FAIL_CH = "导出基站的上报日志失败"
    EXPORT_BASE_STATION_REPORT_LOG_FAIL_EN = "Failed to export base station report log"

    #基站上报数据
    BASE_STATION_REPORT_DATA_CH = "基站上报数据"
    BASE_STATION_REPORT_DATA_EN = "Base station report data"

    #基站位置上报数据
    BASE_STATION_LOCATION_REPORT_DATA_CH = "基站位置上报数据"
    BASE_STATION_LOCATION_REPORT_DATA_EN = "Base station location report data"

    # 导出终端的上报日志
    EXPORT_TERMINAL_REPORT_LOG_CH = "导出终端的上报日志"
    EXPORT_TERMINAL_REPORT_LOG_EN = "Export terminal report log"

    # 导出终端的上报日志成功
    EXPORT_TERMINAL_REPORT_LOG_SUCCESS_CH = "导出终端的上报日志成功"
    EXPORT_TERMINAL_REPORT_LOG_SUCCESS_EN = "Successfully exported terminal report log"

    # 导出终端的上报日志失败
    EXPORT_TERMINAL_REPORT_LOG_FAIL_CH = "导出终端的上报日志失败"
    EXPORT_TERMINAL_REPORT_LOG_FAIL_EN = "Failed to export terminal report log"

    # 终端上报数据(报文5）
    TERMINAL_REPORT_DATA_CH = "终端上报数据"
    TERMINAL_REPORT_DATA_EN = "Terminal report data"


    # 终端上报数据（报文6)
    LATSI_TERMINAL_REPORT_DATA_CH = "LATSI终端上报数据"
    LATSI_TERMINAL_REPORT_DATA_EN = "Lasti terminal report data"


    # 获取终端弹窗信息
    GET_TERMINAL_POPUP_INFO_CH = "获取终端弹窗信息"
    GET_TERMINAL_POPUP_INFO_EN = "Get terminal popup information"

   # 获取基站弹窗信息
    GET_BASE_STATION_POPUP_INFO_CH = "获取基站弹窗信息"
    GET_BASE_STATION_POPUP_INFO_EN = "Get base station popup information"

    ##########################################################################################
    # 飞行任务
    CREATE_FLY_TASK_CH = "创建飞行任务"
    CREATE_FLY_TASK_EN = "create fly task"
    QUERY_FLY_TASK_CH = "查询飞行任务"
    QUERY_FLY_TASK_EN = "query fly task"
    UPDATE_FLY_TASK_CH = "更新飞行任务"
    UPDATE_FLY_TASK_EN = "update fly task"
    DELETE_FLY_TASK_CH = "删除飞行任务"
    DELETE_FLY_TASK_EN = "delete fly task"

    TASK_NAME_IS_REQUIRED_PARAMETER_CH = "任务名称是必填参数"
    TASK_NAME_IS_REQUIRED_PARAMETER_EN = "task name is a required parameter"
    TERMINAL_NUMBER_IS_REQUIRED_PARAMETER_CH = "终端编号是必填参数"
    TERMINAL_NUMBER_IS_REQUIRED_PARAMETER_EN = "terminal number is a required parameter"
    BASE_STATION_NUMBER_IS_REQUIRED_PARAMETER_CH = "基站编号是必填参数"
    BASE_STATION_NUMBER_IS_REQUIRED_PARAMETER_EN = "base station number is a required parameter"
    TASK_NAME_CANNOT_BE_EMPTY_CH = "任务名称不能为空"
    TASK_NAME_CANNOT_BE_EMPTY_EN = "task name cannot be empty"
    TERMINAL_NUMBER_CANNOT_BE_EMPTY_CH = "终端编号不能为空"
    TERMINAL_NUMBER_CANNOT_BE_EMPTY_EN = "terminal number cannot be empty"
    BASE_STATION_NUMBER_CANNOT_BE_EMPTY_CH = "基站编号不能为空"
    BASE_STATION_NUMBER_CANNOT_BE_EMPTY_EN = "base station number cannot be empty"

    CREATE_SUCCESS_CH = "创建成功"
    CREATE_SUCCESS_EN = "created successfully"
    CREATE_TASK_SUCCESS_CH = "【{}】成功"
    CREATE_TASK_SUCCESS_EN = "【{}】created successfully"
    ADD_FAILED_REASON_CH = "新增数据失败，原因：{}"
    ADD_FAILED_REASON_EN = "failed to add data, reason: {}"
    DATA_NOT_EXIST_CH = "数据不存在（ID：{}）"
    DATA_NOT_EXIST_EN = "data does not exist (ID: {})"
    DELETE_SUCCESS_SHORT_CH = "删除成功"
    DELETE_SUCCESS_SHORT_EN = "deleted successfully"
    UPDATE_FAILED_REASON2_CH = "更新失败，原因：{}"
    UPDATE_FAILED_REASON2_EN = "failed to update data, reason: {}"

    ##########################################################################################
    # token 登录 / 校验 / 退出 / 找回重置密码
    LOGIN_BY_TOKEN_CH = "通过token登录"
    LOGIN_BY_TOKEN_EN = "login by token"
    TOKEN_LOGIN_SUCCESS_CH = "{}成功！"
    TOKEN_LOGIN_SUCCESS_EN = "{} is successful!"
    TOKEN_EXPIRED_CH = "{}失败：输入的token已失效"
    TOKEN_EXPIRED_EN = "{} failed: the input token has expired"
    TOKEN_NOT_EXIST_CH = "{}失败：输入的token不存在"
    TOKEN_NOT_EXIST_EN = "{} failed: the input token does not exist"
    VERIFY_TOKEN_EXPIRED_CH = "验证token是否过期"
    VERIFY_TOKEN_EXPIRED_EN = "verify whether the token is expired"
    SUCCESS_SUFFIX_CH = "{}成功"
    SUCCESS_SUFFIX_EN = "{} is successful"
    FAIL_SUFFIX_CH = "{}失败"
    FAIL_SUFFIX_EN = "{} is failed"
    LOGOUT_CH = "用户退出"
    LOGOUT_EN = "user logout"
    LOGOUT_SUCCESS_CH = "用户退出成功！"
    LOGOUT_SUCCESS_EN = "user logout successful!"
    RETRIEVE_PASSWORD_SUCCESS_CH = "密码找回成功"
    RETRIEVE_PASSWORD_SUCCESS_EN = "password retrieved successfully"
    SECURITY_QUESTION_OR_ANSWER_WRONG_CH = "密保问题或答案错误"
    SECURITY_QUESTION_OR_ANSWER_WRONG_EN = "security question or answer is wrong"
    USERNAME_NOT_EXIST_CH = "用户名不存在"
    USERNAME_NOT_EXIST_EN = "username does not exist"
    RESET_PASSWORD_SUCCESS_CH = "重置密码成功"
    RESET_PASSWORD_SUCCESS_EN = "password reset successfully"
    RESET_PASSWORD_FAIL_CH = "重置密码失败"
    RESET_PASSWORD_FAIL_EN = "failed to reset password"

    ##########################################################################################
    # 群组更新 / 数据字典 / 表字段查询 / 行政区划
    UPDATE_GROUP_NAME_EXIST_CH = "更新的群组名称:{}已存在，请换个名称"
    UPDATE_GROUP_NAME_EXIST_EN = "the updated group name '{}' already exists, please use a different name"
    GROUP_NOT_EXIST_CH = "群组不存在（ID：{}）"
    GROUP_NOT_EXIST_EN = "group does not exist (ID: {})"
    UPDATE_GROUP_SUCCESS_DETAIL_CH = "更新群组成功：ID【{}】，旧名称【{}】→ 新名称【{}】"
    UPDATE_GROUP_SUCCESS_DETAIL_EN = "group update is successful: ID【{}】, old name【{}】 → new name【{}】"
    UPDATE_GROUP_FAIL_REASON_CH = "更新群组失败，原因：{}"
    UPDATE_GROUP_FAIL_REASON_EN = "failed to update group, reason: {}"
    ADD_DATA_DICTIONARY_EXIST_CH = "添加数据字典失败，该字典类别下已存在该字典信息"
    ADD_DATA_DICTIONARY_EXIST_EN = "failed to add data dictionary: the dictionary already exists under this category"
    ADD_DATA_DICTIONARY_SUCCESS_CH = "添加数据字典成功"
    ADD_DATA_DICTIONARY_SUCCESS_EN = "data dictionary added successfully"
    UPDATE_DATA_DICTIONARY_EXIST_CH = "更新数据字典失败，该字典类别下已存在该字典信息"
    UPDATE_DATA_DICTIONARY_EXIST_EN = "failed to update data dictionary: the dictionary already exists under this category"
    UPDATE_DATA_DICTIONARY_SUCCESS_CH = "更新数据字典成功"
    UPDATE_DATA_DICTIONARY_SUCCESS_EN = "data dictionary updated successfully"
    DELETE_DATA_DICTIONARY_SUCCESS_CH = "删除数据字典成功"
    DELETE_DATA_DICTIONARY_SUCCESS_EN = "data dictionary deleted successfully"
    OPERATION_FAIL_REASON_CH = "{}失败：{}"
    OPERATION_FAIL_REASON_EN = "{} is failed: {}"
    OPERATION_SUCCESS_SUFFIX_CH = "{}成功"
    OPERATION_SUCCESS_SUFFIX_EN = "{} is successful"
    GET_NATIONAL_DATA_BY_PROVINCE_FAIL_REASON_CH = "获取全国的分地区分省数据失败：{}"
    GET_NATIONAL_DATA_BY_PROVINCE_FAIL_REASON_EN = "get national data by province failed: {}"
    GET_LOG_LIST_DATA_CH = "获取日志列表数据"
    GET_LOG_LIST_DATA_EN = "get log list data"
    SET_DEPARTMENT_STATUS2_CH = "设置部门状态"
    SET_DEPARTMENT_STATUS2_EN = "set department status"
    DELETE_DEPARTMENT_DATA_CH = "逻辑删除部门数据"
    DELETE_DEPARTMENT_DATA_EN = "logically delete department data"
    GET_ROLE_LIST_DATA2_CH = "获取角色列表数据"
    GET_ROLE_LIST_DATA2_EN = "get role list data"
    # 以下为系统名称/版本，属于项目定制项，新建项目时请替换
    SYSTEM_NAME_CH = "系统名称：my_app"
    SYSTEM_NAME_EN = "System name: my_app"
    SYSTEM_VERSION_CH = "系统版本号：1.00.00"
    SYSTEM_VERSION_EN = "System version: 1.00.00"

    ##########################################################################################
    # 行政区划（businessViews.TmDdistrictViewSet）
    GET_REGION_PROVINCE_DATA_CH = "获取全国的分地区分省数据"
    GET_REGION_PROVINCE_DATA_EN = "get regional and provincial data of the whole country"

    ##########################################################################################
    # 通用 ViewSet 基类（CustomModelViewSet）使用
    QUERY_LIST_FAIL_CH = "查询列表失败：{}"
    QUERY_LIST_FAIL_EN = "query list failed: {}"
    QUERY_DETAIL_FAIL_CH = "查询详情失败：{}"
    QUERY_DETAIL_FAIL_EN = "query detail failed: {}"
    DELETE_DATA_FAIL_CH = "删除数据失败：{}"
    DELETE_DATA_FAIL_EN = "delete data failed: {}"






