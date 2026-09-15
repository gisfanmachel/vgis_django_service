# -*- coding: utf-8 -*-
"""
Stage C：表级缓存失效辅助。

按 plan 中的「11 张热表缓存策略」：
  在 view 的 create/update/destroy 末尾调 invalidate_table("table_name")，
  确保下次读路径能立即拿到新值（避免 30min 内看到旧数据）。

用法：
  from my_app.utils.cacheInvalidate import invalidate_table
  ...
  def destroy(self, request, ...):
      super().destroy(...)
      invalidate_table("sys_user")
"""
from __future__ import unicode_literals

from .cacheHelper import TableCacheHelper


# 表名 -> 哪个 ViewSet 负责让它失效（仅作文档参考，实际由 view 显式调用 invalidate_table）
TABLE_INVALIDATE_MAP = {
    "sys_dict": "SysDictViewSet",
    "sys_dict_catelog": "SysDictViewSet",
    "sys_menu": "SysMenuViewSet",
    "sys_role": "SysRoleViewSet",
    "sys_role_menu": "SysRoleViewSet",
    "sys_user_role": "AuthUserViewSet",
    "auth_user": "AuthUserViewSet",
    "sys_department": "SysDepartmentViewSet",
    "sys_param": "SysParamViewSet",
    "tm_district": "CommonOperator",
    "tm_region": "CommonOperator",
}


def invalidate_table(table_name, scope="all", suffix=None):
    """按表名失效 cache key（与 TABLE_INVALIDATE_MAP 配合）"""
    try:
        TableCacheHelper.invalidate(table_name, scope=scope, suffix=suffix)
    except Exception:
        # 缓存失效失败不影响业务
        pass