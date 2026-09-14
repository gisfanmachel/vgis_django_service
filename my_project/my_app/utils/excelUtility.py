# -*- coding: utf-8 -*-
# Excel 通用工具：生成导出文件 / 生成导入模板 / 读取导入文件
#
# 设计要点：
#   1. 读入一律 dtype=str + keep_default_na=False，把类型转换交给调用方自己做，
#      避免 pandas 的类型推断把 "0001" 变成 1、把空串变成 NaN 之类的问题。
#   2. 生成的文件落到 settings.STATICFILES_DIRS[0] 下的 xls/ 目录，
#      返回 (可访问 URL, 本地路径)。开发模式(DEBUG=True)下 runserver 会直接把
#      /my_static/xls/xxx.xlsx 映射到该目录；生产环境由 nginx 负责静态映射。
#   3. 参考项目（PNT / 保险OCR）都用 pandas + xlsxwriter，这里保持一致。
import os
import uuid

import pandas as pd

from my_app.utils.commonUtility import CommonHelper
from my_project import settings

XLS_SUB_DIR = "xls"
XLS_SUFFIXES = (".xlsx", ".xls")


def get_xls_dir():
    """导出文件存放目录：<静态资源根>/xls/"""
    xls_dir = os.path.join(settings.STATICFILES_DIRS[0], XLS_SUB_DIR)
    if not os.path.isdir(xls_dir):
        os.makedirs(xls_dir)
    return xls_dir


def build_excel_file(sheet_name, rows, cn_headers, en_fields, file_prefix="export"):
    """
    按中文表头生成 Excel。

    :param rows: list[dict]，每个 dict 是「英文字段名 -> 值」
    :param cn_headers: 中文表头列表（Excel 第一行）
    :param en_fields:  英文字段名列表，与 cn_headers 按下标一一对应
    :return: (可访问 URL, 本地绝对路径)
    """
    data_list = []
    for row in rows:
        data_list.append({cn: row.get(en) for cn, en in zip(cn_headers, en_fields)})

    file_name = "{}_{}.xlsx".format(file_prefix, uuid.uuid4())
    file_path = os.path.join(get_xls_dir(), file_name)

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df = pd.DataFrame(data_list, columns=cn_headers)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        # 列宽按中文表头长度自适应（中文按 2 个字符宽估算，再留些余量）
        for idx, header in enumerate(cn_headers):
            width = max(len(str(header)) * 2 + 4, 12)
            worksheet.set_column(idx, idx, min(width, 60))

    url = CommonHelper.get_url_head() + "{}/{}".format(XLS_SUB_DIR, file_name)
    return url, file_path


def read_excel_rows(file_path):
    """
    读取导入文件，返回 (DataFrame, error)。全部按字符串读入，不做类型推断。

    .xlsx 用 openpyxl；.xls 让 pandas 自己选引擎（通常是 xlrd）。
    """
    suffix = os.path.splitext(file_path)[1].lower()
    if suffix not in XLS_SUFFIXES:
        return None, "unsupported suffix: {}".format(suffix)
    try:
        if suffix == ".xlsx":
            df = pd.read_excel(file_path, engine="openpyxl", dtype=str, keep_default_na=False)
        else:
            df = pd.read_excel(file_path, dtype=str, keep_default_na=False)
    except Exception as e:
        return None, str(e)
    # 去掉 pandas 给无名列生成的 "Unnamed: N" 列（尾部空列常出现）
    df = df.loc[:, [c for c in df.columns if not str(c).startswith("Unnamed:")]]
    return df, None


def build_template_file(sheet_name, cn_headers, file_prefix="template"):
    """生成只带表头的空白导入模板，返回 (URL, 路径)"""
    file_name = "{}_{}.xlsx".format(file_prefix, uuid.uuid4())
    file_path = os.path.join(get_xls_dir(), file_name)
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df = pd.DataFrame(columns=cn_headers)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        for idx, header in enumerate(cn_headers):
            worksheet.set_column(idx, idx, min(max(len(str(header)) * 2 + 4, 12), 60))
    url = CommonHelper.get_url_head() + "{}/{}".format(XLS_SUB_DIR, file_name)
    return url, file_path
