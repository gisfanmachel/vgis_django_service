# -*- coding: utf-8 -*-
# demo 模块的业务逻辑层
#
# 这是框架「SQL 方式 CRUD + 裸 SQL 分页 + 多表联合查询 + Excel 导入导出」的完整模板。
# 分层约定（与其它模块一致）：
#   ViewSet 只做参数接收与日志壳，真正的逻辑都在这里；每个方法 (self, request) 返回 dict，
#   内部吞掉异常、绝不向上抛（外层 try/finally: return res）。
import datetime
import decimal
import logging
import os
import time

from django.db import transaction
from django.utils import timezone
from vgis_log.logTools import LoggerHelper
from vgis_utils.vgis_http.httpTools import HttpHelper

from my_app.module.demo.localization import Enum
from my_app.module.demo.models import TtDemoItem
from my_app.module.demo.utility import (
    EXPORT_EXTRA, FIELD_MAP, IMPORT_MAX_ROWS,
    get_export_cn_headers, get_export_en_fields, get_import_field_names,
    get_required_cn_headers,
)
from my_app.models import SysLog
from my_app.tasks import insert_log_info_async
from my_app.utils.commonUtility import CommonHelper
from my_app.utils.excelUtility import build_excel_file, build_template_file, read_excel_rows, XLS_SUFFIXES
from my_app.utils.paginationUtility import PaginationHelper
from my_app.utils.safeSQL import UnsafeIdentifierError, assert_table_allowed
from my_project import settings

# 注意：本模块的取词统一用 get_local_str_from_module（查本模块 localization.py）
MODULE = "demo"

# 联合查询的基础 SQL —— 分页的 count 与取页共用同一段（不能带 order by / limit）
BASE_JOIN_SQL = """
    select t.id, t.item_code, t.item_name, t.category_id, t.department_id,
           t.amount, t.item_status, t.occur_date, t.remark,
           t.create_user_id, t.create_time, t.modify_user_id, t.modify_time,
           c.dict_catelog_name as category_name,
           d.department_name   as department_name
      from tt_demo_item t
      left join sys_dict_catelog c on c.id = t.category_id
      left join sys_department   d on d.department_id = t.department_id
     where 1 = 1
"""

# order_by 白名单：它无法参数化，必须校验后才能拼进 SQL
ORDER_BY_WHITELIST = {
    "id", "item_code", "item_name", "category_id", "department_id",
    "amount", "item_status", "occur_date", "create_time",
}

# Stage D：update 字段白名单（UPDATE ... SET {field}=%s 也无法参数化，
# 这里做一道防御性 assert，挡掉未来谁不小心把 data 的 key 直接 format 进去的可能）
UPDATE_FIELD_WHITELIST = frozenset({
    "item_code", "item_name", "category_id", "department_id",
    "amount", "item_status", "occur_date", "remark",
})


class Operator:
    def __init__(self, connection):
        self.connection = connection

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------
    def _t(self, request, key):
        """取本模块词条"""
        return CommonHelper.get_local_str_from_module(MODULE, key, request)

    def _fail(self, request, title, msg):
        return {'success': False, 'info': "{}：{}".format(title, msg)}

    def _build_filters(self, request):
        """把请求里的筛选条件拼成 (where_sql, params)。值全部 %s 参数化。"""
        data = request.data
        sql, params = "", []
        if CommonHelper.is_valid_str(data.get("item_code")):
            sql += " and t.item_code like %s"
            params.append("%{}%".format(data["item_code"].strip()))
        if CommonHelper.is_valid_str(data.get("item_name")):
            sql += " and t.item_name like %s"
            params.append("%{}%".format(data["item_name"].strip()))
        if CommonHelper.is_valid_str(data.get("category_id")):
            sql += " and t.category_id = %s"
            params.append(data["category_id"])
        if CommonHelper.is_valid_str(data.get("department_id")):
            sql += " and t.department_id = %s"
            params.append(data["department_id"])
        if CommonHelper.is_valid_str(data.get("item_status")):
            sql += " and t.item_status = %s"
            params.append(data["item_status"])
        if CommonHelper.is_valid_str(data.get("occur_date_start")):
            sql += " and t.occur_date >= %s"
            params.append(data["occur_date_start"])
        if CommonHelper.is_valid_str(data.get("occur_date_end")):
            sql += " and t.occur_date <= %s"
            params.append(data["occur_date_end"])
        return sql, params

    @staticmethod
    def _row_to_dict(record):
        """
        逐字段手工映射成 dict。
        Decimal -> 字符串（避免 JSON 序列化丢精度/前端拿到不规范数字）；
        date/datetime -> 字符串。
        """
        def s(v):
            if v is None:
                return None
            if isinstance(v, (datetime.date, datetime.datetime)):
                return v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v, datetime.datetime) else v.strftime('%Y-%m-%d')
            if isinstance(v, decimal.Decimal):
                return str(v)
            return v

        keys = ["id", "item_code", "item_name", "category_id", "department_id",
                "amount", "item_status", "occur_date", "remark",
                "create_user_id", "create_time", "modify_user_id", "modify_time",
                "category_name", "department_name"]
        return {k: s(v) for k, v in zip(keys, record)}

    # ==================================================================
    # 一、增删改
    # ==================================================================
    def create_data(self, request):
        title = self._t(request, "MODULE_TITLE")
        start = time.perf_counter()
        try:
            data = request.data
            item_code = data.get("item_code")
            item_name = data.get("item_name")
            if not CommonHelper.is_valid_str(item_code):
                return self._fail(request, title, self._t(request, "PARAM_MISSING").format("item_code"))
            if not CommonHelper.is_valid_str(item_name):
                return self._fail(request, title, self._t(request, "PARAM_MISSING").format("item_name"))

            with self.connection.cursor() as cursor:
                cursor.execute("select count(*) from tt_demo_item where item_code = %s", [item_code])
                if cursor.fetchone()[0] > 0:
                    return self._fail(request, title, self._t(request, "ADD_EXIST").format(item_code))

                now = timezone.now()
                cursor.execute(
                    """insert into tt_demo_item
                       (item_code, item_name, category_id, department_id, amount,
                        item_status, occur_date, remark, create_user_id, create_time)
                       values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id""",
                    [item_code, item_name, data.get("category_id"), data.get("department_id"),
                     data.get("amount"), data.get("item_status", 1), data.get("occur_date") or None,
                     data.get("remark"), request.auth.user_id, now])
                new_id = cursor.fetchone()[0]
            self.connection.commit()

            t = time.perf_counter() - start
            info = self._t(request, "ADD_SUCCESS").format(title)
            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, info, request.path,
                                         HttpHelper.get_params_request(request), t,
                                         HttpHelper.get_ip_request(request))
            return {'success': True, 'info': info, 'id': new_id}
        except Exception as exp:
            self.connection.rollback()
            return self._on_exception(request, start, title, exp)

    def update_data(self, request):
        title = self._t(request, "MODULE_TITLE")
        start = time.perf_counter()
        try:
            data = request.data
            data_id = data.get("id")
            if not CommonHelper.is_valid_str(data_id):
                return self._fail(request, title, self._t(request, "PARAM_MISSING").format("id"))

            with self.connection.cursor() as cursor:
                cursor.execute("select count(*) from tt_demo_item where id = %s", [data_id])
                if cursor.fetchone()[0] == 0:
                    return self._fail(request, title, self._t(request, "UPDATE_NOT_EXIST").format(data_id))

                # 只更新请求里显式给出的字段
                sets, params = [], []
                for field in ["item_code", "item_name", "category_id", "department_id",
                              "amount", "item_status", "occur_date", "remark"]:
                    if field in data:
                        # Stage D：防御性白名单 —— 即便 field 已经来自硬编码列表，
                        # 还是走一遍 assert，挡住未来误把 data 直接拼进来的可能
                        if field not in UPDATE_FIELD_WHITELIST:
                            continue
                        sets.append("{} = %s".format(field))
                        params.append(data.get(field) or None)
                if not sets:
                    return self._fail(request, title, self._t(request, "PARAM_MISSING").format("待更新字段"))
                sets.append("modify_user_id = %s")
                params.append(request.auth.user_id)
                sets.append("modify_time = %s")
                params.append(timezone.now())
                params.append(data_id)
                cursor.execute("update tt_demo_item set {} where id = %s".format(", ".join(sets)), params)
            self.connection.commit()

            t = time.perf_counter() - start
            info = self._t(request, "UPDATE_SUCCESS").format(title)
            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, info, request.path,
                                         HttpHelper.get_params_request(request), t,
                                         HttpHelper.get_ip_request(request))
            return {'success': True, 'info': info}
        except Exception as exp:
            self.connection.rollback()
            return self._on_exception(request, start, title, exp)

    def delete_data(self, request):
        title = self._t(request, "MODULE_TITLE")
        start = time.perf_counter()
        try:
            data_id = request.data.get("id")
            if not CommonHelper.is_valid_str(data_id):
                return self._fail(request, title, self._t(request, "PARAM_MISSING").format("id"))
            with self.connection.cursor() as cursor:
                cursor.execute("select count(*) from tt_demo_item where id = %s", [data_id])
                if cursor.fetchone()[0] == 0:
                    return self._fail(request, title, self._t(request, "DELETE_NOT_EXIST").format(data_id))
                cursor.execute("delete from tt_demo_item where id = %s", [data_id])
            self.connection.commit()

            t = time.perf_counter() - start
            info = self._t(request, "DELETE_SUCCESS").format(title)
            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, info, request.path,
                                         HttpHelper.get_params_request(request), t,
                                         HttpHelper.get_ip_request(request))
            return {'success': True, 'info': info}
        except Exception as exp:
            self.connection.rollback()
            return self._on_exception(request, start, title, exp)

    # ==================================================================
    # 二、多表联合查询 + 裸 SQL 分页
    # ==================================================================
    def query_data(self, request):
        title = self._t(request, "QUERY_FAIL")
        start = time.perf_counter()
        try:
            page, size, err = PaginationHelper.parse_page_params(request)
            if err:
                # PaginationHelper 是共享工具、拿不到 request，所以它只回一个错误码；
                # 面向用户的文案在本模块按多语言组装
                msg = self._t(request, "PAGE_PARAM_INVALID") if err == PaginationHelper.ERR_INVALID_PARAM \
                    else self._t(request, "SIZE_EXCEED_MAX").format(err)
                return self._fail(request, title, msg)

            where_sql, params = self._build_filters(request)
            base_sql = BASE_JOIN_SQL + where_sql
            order_by = PaginationHelper.check_order_by(
                request.data.get("order_by"), ORDER_BY_WHITELIST, default="t.id asc")
            if order_by and not order_by.startswith("t."):
                order_by = "t." + order_by

            total = PaginationHelper.count(self.connection, base_sql, params)
            rows = PaginationHelper.fetch_page(self.connection, base_sql, params, page, size, order_by)
            data_list = [self._row_to_dict(r) for r in rows]

            t = time.perf_counter() - start
            info = self._t(request, "QUERY_SUCCESS")
            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, info, request.path,
                                         HttpHelper.get_params_request(request), t,
                                         HttpHelper.get_ip_request(request))
            return {'success': True, 'info': info, 'total': total,
                    'page': page, 'size': size, 'data': data_list}
        except Exception as exp:
            return self._on_exception(request, start, title, exp)

    # ==================================================================
    # 三、Excel 导出
    # ==================================================================
    def export_excel(self, request):
        title = self._t(request, "MODULE_TITLE")
        start = time.perf_counter()
        try:
            where_sql, params = self._build_filters(request)
            order_by = PaginationHelper.check_order_by(
                request.data.get("order_by"), ORDER_BY_WHITELIST, default="t.id asc")
            if order_by and not order_by.startswith("t."):
                order_by = "t." + order_by

            # 导出不分页，取全部符合条件的数据
            with self.connection.cursor() as cursor:
                cursor.execute(BASE_JOIN_SQL + where_sql + " order by " + order_by, params)
                rows = cursor.fetchall()
            if not rows:
                return self._fail(request, title, self._t(request, "EXPORT_NO_DATA"))

            data_list = [self._row_to_dict(r) for r in rows]
            sheet = self._t(request, "EXPORT_SHEET_NAME")
            url, path = build_excel_file(sheet, data_list,
                                         get_export_cn_headers(), get_export_en_fields(),
                                         file_prefix="demo_item")

            t = time.perf_counter() - start
            info = self._t(request, "EXPORT_SUCCESS").format(len(data_list))
            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, info, request.path,
                                         HttpHelper.get_params_request(request), t,
                                         HttpHelper.get_ip_request(request))
            return {'success': True, 'info': info, 'total': len(data_list),
                    'data': url, 'file_path': path}
        except Exception as exp:
            return self._on_exception(request, start, title, exp)

    def download_template(self, request):
        title = self._t(request, "MODULE_TITLE")
        start = time.perf_counter()
        try:
            sheet = self._t(request, "EXPORT_SHEET_NAME")
            # 模板只带 FIELD_MAP 的列（导入列），不含只有导出才有的类别名/部门名
            url, path = build_template_file(sheet, [f[0] for f in FIELD_MAP],
                                            file_prefix="demo_item_template")
            t = time.perf_counter() - start
            info = self._t(request, "EXPORT_SUCCESS").format(0)
            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, info, request.path,
                                         HttpHelper.get_params_request(request), t,
                                         HttpHelper.get_ip_request(request))
            return {'success': True, 'info': info, 'data': url, 'file_path': path}
        except Exception as exp:
            return self._on_exception(request, start, title, exp)

    # ==================================================================
    # 四、Excel 导入（upsert）
    #
    # 与参考项目的关键差异（参考项目全都没有）：
    #   1. 先全量校验，任一行不合法就整批拒绝 —— 不留半成品数据
    #   2. 单事务写入（transaction.atomic）
    #   3. upsert 走 ON CONFLICT (item_code) DO UPDATE，
    #      而不是"先 filter 再 create/update"（那种做法库上没有唯一约束、且有 TOCTOU 竞态）
    #   4. 返回结构化结果：总行数 / 新增数 / 更新数 / 逐行错误（带 Excel 行号与列名）
    # ==================================================================
    def import_excel(self, request):
        title = self._t(request, "MODULE_TITLE")
        start = time.perf_counter()
        try:
            file_path, err = self._resolve_import_file(request)
            if err:
                return self._fail(request, title, err)

            df, err = read_excel_rows(file_path)
            if err:
                return self._fail(request, title, err)

            cn_headers = [f[0] for f in FIELD_MAP]
            missing = [h for h in get_required_cn_headers() if h not in list(df.columns)]
            if missing:
                return self._fail(request, title,
                                  self._t(request, "IMPORT_HEADER_MISSING").format("、".join(missing)))

            if len(df) == 0:
                return self._fail(request, title, self._t(request, "EXPORT_NO_DATA"))
            if len(df) > IMPORT_MAX_ROWS:
                return self._fail(request, title,
                                  self._t(request, "IMPORT_ROW_LIMIT").format(IMPORT_MAX_ROWS, len(df)))

            # ---- 第一遍：全量校验，收集所有错误行，不写库 ----
            user_id = request.auth.user_id
            parsed_rows, errors = [], []
            for idx, raw in df.iterrows():
                excel_row = idx + 2  # 表头占第 1 行，数据从第 2 行开始
                values, row_errors = self._parse_and_validate_row(raw, excel_row, cn_headers, user_id)
                errors.extend(row_errors)
                if values:
                    parsed_rows.append(values)

            if errors:
                t = time.perf_counter() - start
                info = self._t(request, "OPERATION_FAIL_REASON").format(title, "{} 行校验不通过".format(len(errors)))
                insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, info + " 导入失败", request.path,
                                             HttpHelper.get_params_request(request), t,
                                             HttpHelper.get_ip_request(request))
                return {'success': False, 'info': info, 'total': len(df),
                        'created': 0, 'updated': 0, 'failed': errors}

            # ---- 第二遍：单事务 upsert ----
            created = updated = 0
            with transaction.atomic(using="default"):
                with self.connection.cursor() as cursor:
                    for values in parsed_rows:
                        cursor.execute(self._upsert_sql(), values)
                        if cursor.fetchone()[0]:   # (xmax = 0) 为真表示本次是 INSERT
                            created += 1
                        else:
                            updated += 1

            t = time.perf_counter() - start
            info = self._t(request, "IMPORT_SUCCESS").format(len(df), created, updated)
            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, info, request.path,
                                         HttpHelper.get_params_request(request), t,
                                         HttpHelper.get_ip_request(request))
            return {'success': True, 'info': info, 'total': len(df),
                    'created': created, 'updated': updated, 'failed': []}
        except Exception as exp:
            return self._on_exception(request, start, title, exp)

    @staticmethod
    def _upsert_sql():
        """
        ON CONFLICT (item_code) DO UPDATE 实现 upsert。
        returning (xmax = 0) —— PG 的惯用手法，用来区分本次是插入(True)还是更新(False)。
        """
        return """
            insert into tt_demo_item
                (item_code, item_name, category_id, department_id, amount,
                 item_status, occur_date, remark, create_user_id, create_time)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            on conflict (item_code) do update set
                item_name      = excluded.item_name,
                category_id    = excluded.category_id,
                department_id  = excluded.department_id,
                amount         = excluded.amount,
                item_status    = excluded.item_status,
                occur_date     = excluded.occur_date,
                remark         = excluded.remark,
                modify_user_id = excluded.modify_user_id,
                modify_time    = excluded.modify_time
            returning (xmax = 0) as inserted
        """

    def _resolve_import_file(self, request):
        """
        支持两种入参：
          1. multipart 直接传文件（form-data 字段名 file）
          2. 传已上传文件的 file_id（走框架既有的 tt_upload_file_data + UPLOAD_ROOT）
        返回 (本地文件路径, 错误信息)
        """
        request_file = request.FILES.get("file") if hasattr(request, "FILES") else None
        if request_file is not None:
            suffix = os.path.splitext(request_file.name)[1].lower()
            if suffix not in XLS_SUFFIXES:
                return None, self._t(request, "IMPORT_FILE_SUFFIX_INVALID").format(suffix or "未知")
            tmp_dir = os.path.join(settings.UPLOAD_ROOT, "import_tmp")
            if not os.path.isdir(tmp_dir):
                os.makedirs(tmp_dir)
            tmp_path = os.path.join(tmp_dir, "{}_{}".format(int(time.time() * 1000), request_file.name))
            with open(tmp_path, "wb") as f:
                for chunk in request_file.chunks():
                    f.write(chunk)
            return tmp_path, None

        file_id = request.data.get("file_id")
        if CommonHelper.is_valid_str(file_id):
            with self.connection.cursor() as cursor:
                cursor.execute("select file_suffix from tt_upload_file_data where file_id = %s limit 1", [file_id])
                row = cursor.fetchone()
            if row and row[0]:
                file_path = os.path.join(settings.UPLOAD_ROOT, "{}.{}".format(file_id, row[0]))
                if os.path.exists(file_path):
                    return file_path, None
            return None, "file_id {} 对应的文件不存在".format(file_id)

        return None, self._t(request, "IMPORT_NO_FILE")

    def _parse_and_validate_row(self, raw, excel_row, cn_headers, user_id):
        """
        解析并校验一行。返回 (values_list, errors_list)。
        values_list：顺序与 _upsert_sql 的占位符一一对应
        errors_list：形如 [{'row': 3, 'column': '金额', 'error': '格式不正确：abc'}]，
                     校验通过时返回空列表（**不能返回 None**，调用方会 extend）
        """
        errors = []
        values = {}
        for cn, en, ftype, required in FIELD_MAP:
            text = str(raw.get(cn, "") if raw.get(cn) is not None else "").strip()
            if text == "":
                if required:
                    errors.append({'row': excel_row, 'column': cn, 'error': "为必填项，不能为空"})
                else:
                    values[en] = None
                continue
            try:
                if ftype == "int":
                    values[en] = int(float(text))     # 兼容 Excel 把整数读成 "3.0"
                elif ftype == "decimal":
                    values[en] = decimal.Decimal(text)
                elif ftype == "date":
                    values[en] = self._parse_date(text)
                else:
                    values[en] = text
            except Exception:
                errors.append({'row': excel_row, 'column': cn, 'error': "格式不正确：{}".format(text)})

        # 必填列缺失时不继续做外键校验，避免同一行报一堆错
        if errors:
            return None, errors

        # 外键存在性校验（category_id / department_id）
        with self.connection.cursor() as cursor:
            if values.get("category_id") is not None:
                cursor.execute("select count(*) from sys_dict_catelog where id = %s", [values["category_id"]])
                if cursor.fetchone()[0] == 0:
                    errors.append({'row': excel_row, 'column': '类别id',
                                   'error': "字典类别不存在：{}".format(values["category_id"])})
            if values.get("department_id") is not None:
                cursor.execute("select count(*) from sys_department where department_id = %s",
                               [values["department_id"]])
                if cursor.fetchone()[0] == 0:
                    errors.append({'row': excel_row, 'column': '部门id',
                                   'error': "部门不存在：{}".format(values["department_id"])})
        if errors:
            return None, errors

        now = timezone.now()
        return [values.get("item_code"), values.get("item_name"),
                values.get("category_id"), values.get("department_id"),
                values.get("amount"), values.get("item_status"),
                values.get("occur_date"), values.get("remark"),
                user_id, now], []

    @staticmethod
    def _parse_date(text):
        """接受 2026-09-13 / 2026/09/13 / 2026-09-13 00:00:00 等常见写法"""
        text = str(text).strip().split(" ")[0].replace("/", "-")
        return datetime.datetime.strptime(text, "%Y-%m-%d").date()

    def _on_exception(self, request, start, title, exp):
        """异常统一处理：写异常日志 + 记操作日志 + 返回失败结构"""
        logger = logging.getLogger("django")
        logger.error("%s失败：%s", title, str(exp), exc_info=True)
        t = time.perf_counter() - start
        info = self._t(request, "OPERATION_FAIL_REASON").format(title, str(exp))
        try:
            insert_log_info_async("my_app.module.sys_manage.models.SysLog", request.auth.user, info, request.path,
                                         HttpHelper.get_params_request(request), t,
                                         HttpHelper.get_ip_request(request), str(exp))
        except Exception:
            pass
        return {'success': False, 'info': info}
