# -*- coding: utf-8 -*-
"""
Stage D：SQL 标识符白名单 + safe format helper。

背景：
  框架里很多 manager 用裸 SQL 拼装 where 子句、order by、表名。
  值参数化（%s）已经被前几轮打掉，但 order by / 表名是 SQL 标识符，
  无法用 %s 占位，必须在 Python 侧白名单校验后才能拼进 SQL。

使用：
  from my_app.utils.safeSQL import assert_table_allowed, safe_order_by, UnsafeIdentifierError
  ...
  try:
      direction = safe_order_by(field, direction, allowed_columns=ORDER_BY_WHITELIST)
  except UnsafeIdentifierError as exp:
      logger.warning(...)
"""
from __future__ import unicode_literals

from psycopg2 import sql as pg_sql


class UnsafeIdentifierError(ValueError):
    """白名单外的标识符直接 raise，调用方应回退到默认值或返回 400。"""


# 表名白名单：所有 .format("...from {table}") 拼装都能用 assert_table_allowed() 校验。
# 与 django models 实际建表保持一致（少量 PG 内部表加进来便于做维护 SQL）。
ALLOWED_TABLES = frozenset({
    "sys_param", "sys_dict", "sys_dict_catelog", "sys_menu", "sys_role", "sys_role_menu",
    "sys_user", "sys_user_role", "sys_user_token", "sys_department", "sys_log", "sys_message",
    "sys_config", "sys_oss", "auth_user", "auth_group", "auth_group_permissions",
    "auth_permission", "auth_user_groups", "auth_user_user_permissions",
    "tt_userpass_question", "tt_retrivepass_token",
    "tm_district", "tm_region", "tt_demo_item", "tt_upload_file_data",
    # 系统级表（运维脚本会用）
    "pg_stat_activity", "pg_stat_statements",
})

ALLOWED_DIRECTIONS = frozenset({"asc", "desc", "ASC", "DESC"})


def assert_table_allowed(table_name, allowed=ALLOWED_TABLES):
    """断言 table_name 在白名单；不在则 raise。"""
    if table_name not in allowed:
        raise UnsafeIdentifierError("table name {!r} not in ALLOWED_TABLES".format(table_name))
    return table_name


def safe_format_table(template, table_name, allowed=ALLOWED_TABLES):
    """format(..., table_name) 的安全封装：先 assert_table_allowed 再 format。"""
    assert_table_allowed(table_name, allowed=allowed)
    return template.format(table_name)


def safe_order_by(field, direction, allowed_columns):
    """
    校验 order by 字段名 + 方向，返回 "field direction" 字符串。
    任一不合法都 raise UnsafeIdentifierError，调用方负责回退。
    """
    if field not in set(allowed_columns or []):
        raise UnsafeIdentifierError("order by field {!r} not in allowed_columns".format(field))
    if direction not in ALLOWED_DIRECTIONS:
        raise UnsafeIdentifierError(
            "order by direction {!r} not in ALLOWED_DIRECTIONS".format(direction))
    return "{} {}".format(field, direction)


def safe_ident(table_name, allowed=ALLOWED_TABLES):
    """返回 psycopg2.sql.Identifier，标识符在 PG 端会被正确转义（极少使用，主要给动态 schema）。"""
    assert_table_allowed(table_name, allowed=allowed)
    return pg_sql.Identifier(table_name)