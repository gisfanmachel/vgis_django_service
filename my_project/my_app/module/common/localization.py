# -*- coding: utf-8 -*-
# common 模块的中英文词条
#
# 约定：类名固定 Enum，词条必须 <KEY>_CH / <KEY>_EN 成对；
#       取词 CommonHelper.get_local_str_from_module("common", "KEY", request)。
#
# 说明：本模块目前主要复用全局词条（SUCCESS / FAIL / GET_REGION_PROVINCE_DATA 等，
#       在 my_app/enum/localization_enum.py），这里只放本模块专有的补充词条。


class Enum:
    MODULE_TITLE_CH = '公共数据'
    MODULE_TITLE_EN = 'Common Data'

    REGION_PROVINCE_TITLE_CH = '获取全国的分地区分省数据'
    REGION_PROVINCE_TITLE_EN = 'get region and province data'

    CITY_BY_PROVINCE_TITLE_CH = '通过省份获取地市数据'
    CITY_BY_PROVINCE_TITLE_EN = 'get city data by province'

    COUNTY_BY_CITY_TITLE_CH = '通过地市获取区县数据'
    COUNTY_BY_CITY_TITLE_EN = 'get county data by city'

    UPLOAD_TITLE_CH = '上传文件'
    UPLOAD_TITLE_EN = 'upload file'
