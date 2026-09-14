# -*- coding: utf-8 -*-
# 裸 SQL 查询的分页工具（框架原先只有 DRF 对 queryset 的分页，没有这一层）
#
# 用法（两段式：先 count 再取当前页）：
#     page, size, err = PaginationHelper.parse_page_params(request)
#     if err:
#         return Result.fail(err, err)
#     total = PaginationHelper.count(connection, base_sql, params)
#     rows = PaginationHelper.fetch_page(connection, base_sql, params, page, size)
#
# 注意：
#   - base_sql 里**不能**带 order by / limit，排序在 fetch_page 里追加
#   - 值一律 %s 参数化；order_by 字段必须来自白名单（见 check_order_by），
#     因为它无法参数化，直接拼字符串会有注入风险
import logging

from my_project import settings

logger = logging.getLogger("django")


class PaginationHelper:
    """裸 SQL 分页：两段式（count + limit/offset）"""

    DEFAULT_SIZE = 10

    # 参数非法的错误码（调用方据此选择本地化文案）
    ERR_INVALID_PARAM = "invalid_param"

    @staticmethod
    def parse_page_params(request, max_size=None):
        """
        从请求里取 page / size（POST body 优先，兼容 URL 参数）。
        返回 (page, size, error)。

        error 的取值：
          None            —— 参数合法
          ERR_INVALID_PARAM —— page/size 不是正整数
          其他字符串       —— size 超上限时，返回的是**上限值**（此时调用方按"超上限"提示，
                             也可以像 demo 模块那样选择直接截断而不报错）

        说明：本工具是共享的、拿不到 request，所以不产出面向用户的文案，
              只回错误码，文案由调用方按自己的多语言词表组装。
        """
        max_size = max_size or getattr(settings, "PAGE_MAX_SIZE", 200)
        raw_page = request.data.get("page", request.query_params.get("page", 1)) \
            if hasattr(request, "query_params") else request.data.get("page", 1)
        raw_size = request.data.get("size", request.query_params.get("size", PaginationHelper.DEFAULT_SIZE)) \
            if hasattr(request, "query_params") else request.data.get("size", PaginationHelper.DEFAULT_SIZE)

        try:
            page = int(raw_page)
            size = int(raw_size)
        except (ValueError, TypeError):
            return 0, 0, PaginationHelper.ERR_INVALID_PARAM

        if page < 1 or size < 1:
            return 0, 0, PaginationHelper.ERR_INVALID_PARAM
        if size > max_size:
            # 超过上限时截断而不是报错，避免前端传个大数就失败
            logger.warning("size=%s 超过上限 %s，已截断", size, max_size)
            size = max_size
        return page, size, None

    @staticmethod
    def count(connection, base_sql, params=None):
        """取总数。base_sql 是 select ... from ... where ...（不含 order by / limit）"""
        count_sql = "select count(*) from ({}) t_count".format(base_sql)
        with connection.cursor() as cursor:
            cursor.execute(count_sql, params or [])
            row = cursor.fetchone()
            return int(row[0]) if row and row[0] is not None else 0

    @staticmethod
    def fetch_page(connection, base_sql, params, page, size, order_by=None):
        """
        取指定页。order_by 必须是通过 check_order_by 校验过的字段名，为空则不排序。
        返回 list[tuple]。
        """
        sql = base_sql
        if order_by:
            sql += " order by {}".format(order_by)
        sql += " limit %s offset %s"
        offset = (page - 1) * size
        with connection.cursor() as cursor:
            cursor.execute(sql, list(params or []) + [size, offset])
            return cursor.fetchall()

    @staticmethod
    def check_order_by(order_by, allowed_fields, default=None):
        """
        order_by 无法参数化，必须白名单校验后才可拼进 SQL。
        允许 'field' 或 'field desc' / 'field asc' 形式；不合规时回落到 default。
        """
        if not order_by or not str(order_by).strip():
            return default
        parts = str(order_by).strip().split()
        field = parts[0]
        direction = parts[1].lower() if len(parts) > 1 else "asc"
        if field not in allowed_fields or direction not in ("asc", "desc"):
            logger.warning("order_by=%s 未通过白名单校验，回落到 %s", order_by, default)
            return default
        return "{} {}".format(field, direction)
