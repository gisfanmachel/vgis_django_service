# -*- coding: utf-8 -*-
# demo 模块内部的工具与常量
from rest_framework.pagination import PageNumberPagination


# ===========================================================================
# 字段映射表 —— Excel 导入与导出的**唯一**数据源
#
# 每条：(Excel 中文表头, 数据库/接口字段名, 值类型, 是否必填)
#   值类型：str / int / decimal / date
#
# 为什么必须只有一份：参考项目（保险OCR）把导入和导出各写了一套字段映射，
# 导出是两条平行数组、导入是散落的 40+ 个 if，改一个字段名要改两处，
# 漏改就是静默丢字段。这里导入和导出都从 FIELD_MAP 派生，不会漂移。
#
# 新增字段只需在这里加一行，导入/导出/模板下载三处自动跟上。
# ===========================================================================
FIELD_MAP = [
    ("业务编码",   "item_code",     "str",     True),
    ("名称",       "item_name",     "str",     True),
    ("类别id",     "category_id",   "int",     True),
    ("部门id",     "department_id", "int",     True),
    ("金额",       "amount",        "decimal", False),
    ("状态",       "item_status",   "int",     False),
    ("发生日期",   "occur_date",    "date",    False),
    ("备注",       "remark",        "str",     False),
]

# 仅用于导出的附加列：来自多表联合查询，不参与导入
EXPORT_EXTRA = [
    ("类别名称", "category_name"),
    ("部门名称", "department_name"),
]

# 导入单次行数上限
IMPORT_MAX_ROWS = 5000


def get_import_field_names():
    """导入用到的英文字段名（按 FIELD_MAP 顺序）"""
    return [f[1] for f in FIELD_MAP]


def get_required_cn_headers():
    """必填列的中文表头"""
    return [f[0] for f in FIELD_MAP if f[3]]


def get_export_cn_headers():
    """导出表头 = 字段映射的中文表头 + 附加列"""
    return [f[0] for f in FIELD_MAP] + [e[0] for e in EXPORT_EXTRA]


def get_export_en_fields():
    """导出取的字段名 = 字段映射的英文名 + 附加列"""
    return [f[1] for f in FIELD_MAP] + [e[1] for e in EXPORT_EXTRA]


class PagePagination(PageNumberPagination):
    """
    DRF 风格的分页参数（供走 queryset 的接口用）。
    裸 SQL 的分页不靠它，见 my_app/utils/paginationUtility.py。
    """
    page_query_param = 'page'
    page_size_query_param = 'size'
    max_page_size = 200
    page_size = 10

    def get_page_number(self, request, paginator):
        try:
            return int(request.data.get('page', request.query_params.get(self.page_query_param, 1)))
        except (ValueError, TypeError):
            return 1

    def get_page_size(self, request):
        try:
            size = int(request.data.get('size',
                                        request.query_params.get(self.page_size_query_param, self.page_size)))
            return min(size, self.max_page_size)
        except (ValueError, TypeError):
            return self.page_size
