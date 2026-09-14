# -*- coding: utf-8 -*-
# user_manage 模块的中英文词条（登录 / Token / 验证码 / 忘记密码）
#
# 约定：类名固定 Enum，词条必须 <KEY>_CH / <KEY>_EN 成对；
#       取词 CommonHelper.get_local_str_from_module("user_manage", "KEY", request)。
#
# 说明：登录相关的多数词条目前在全局表 my_app/enum/localization_enum.py 里
#      （userManager 用的是 CommonHelper.get_local_str），这里放本模块新增/专有的补充词条。


class Enum:
    MODULE_TITLE_CH = '用户管理'
    MODULE_TITLE_EN = 'User Management'

    LOGIN_TITLE_CH = '用户登录'
    LOGIN_TITLE_EN = 'user login'

    LOGOUT_TITLE_CH = '用户退出'
    LOGOUT_TITLE_EN = 'user logout'
