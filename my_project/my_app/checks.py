# -*- coding: utf-8 -*-
# Django system check —— 启动期校验（manage.py check / runserver 都会触发）
#
# 为什么需要它：分模块架构下，各模块把路由前缀写死在**自己的** urls.py 里
# （好处是新增模块不动顶层聚合），代价是前缀冲突无法在编译期发现。
# 参考项目（印尼遥感AI）就踩过：basic_tool/urls.py 与 ortho_fusion/urls.py
# 同为 ynai_api/basictool/，靠 router 注册名恰好不重名才没出事 —— 一旦重名，
# Django 会静默取先匹配的那个，直到某个接口莫名 404 才发现。
#
# 这里把问题拦在启动阶段。
import re

from django.core.checks import Error, Warning, register

# 从视图函数的 __module__ 里识别它属于哪个分模块
_MODULE_RE = re.compile(r"my_app\.module\.([^.]+)\.")


def _norm(seg):
    """把 DRF 的参数化片段归一化成 {id}，便于比对"""
    return re.sub(r"\(\?P<[^>]+>\[[^\]]+\]\)", "{id}", seg)


def _walk(resolver, prefix=""):
    """遍历 URLConf，产出 (归一化完整路径, 所属分模块名 或 None)"""
    for p in resolver.url_patterns:
        seg = str(p.pattern).strip("^$")
        full = prefix + _norm(seg)
        if hasattr(p, "url_patterns"):
            yield from _walk(p, full)
            continue
        if not full.startswith("my_api/") or "(?P<format>" in full:
            continue
        callback = getattr(p, "callback", None)
        module_name = None
        if callback is not None:
            m = _MODULE_RE.match(getattr(callback, "__module__", "") or "")
            if m:
                module_name = m.group(1)
        yield full, module_name


@register()
def check_module_route_prefix_conflict(app_configs, **kwargs):
    """同一路由前缀下混杂了多个分模块时告警"""
    from django.urls import get_resolver

    results = []
    prefix_modules = {}   # "my_api/demo" -> {模块名: [完整路由...]}

    try:
        leaves = list(_walk(get_resolver()))
    except Exception:
        # URLConf 本身有问题时交给 Django 自己的检查去报，这里不抢
        return results

    for full, module_name in leaves:
        if not module_name:
            continue
        parts = full.split("/")
        if len(parts) < 2:
            continue
        shared_prefix = "{}/{}".format(parts[0], parts[1])
        prefix_modules.setdefault(shared_prefix, {}).setdefault(module_name, []).append(full)

    for shared_prefix, modules in prefix_modules.items():
        if len(modules) > 1:
            results.append(Warning(
                "路由前缀 {} 下存在多个分模块：{}".format(
                    shared_prefix, "、".join(sorted(modules))),
                hint="共用前缀本身合法（只要 router 注册名不重复），但一旦重名 Django 会静默取先匹配者。"
                     "建议各模块使用与模块同名的前缀，便于定位。涉及路由数：{}".format(
                         sum(len(v) for v in modules.values())),
                id="my_app.W001",
            ))
    return results


@register()
def check_duplicate_route_path(app_configs, **kwargs):
    """完全相同的路由路径被注册多次时告警（Django 只认第一个）"""
    from django.urls import get_resolver

    results = []
    try:
        leaves = list(_walk(get_resolver()))
    except Exception:
        return results

    seen = {}
    for full, module_name in leaves:
        seen.setdefault(full, []).append(module_name or "旧版扁平路由")

    for path, owners in seen.items():
        if len(owners) > 1:
            results.append(Error(
                "路由路径重复注册：{}".format(path),
                hint="归属：{}。Django 只会匹配第一个，其余永远不会被命中。".format("、".join(owners)),
                id="my_app.E001",
            ))
    return results


# ===========================================================================
# Stage D：AST 静态扫描 —— 拦下"format(用户输入) 直接拼 SQL"类注入风险
#
# 思路：用 ast 遍历 my_app 下所有 .py，对每个 cursor.execute / .raw(...)
# 调用，检查其 SQL 字符串是否包含 .format( 形态：
#   1) 字符串里有 {field}，且参数是 **变量/属性**（不是字面量白名单）
#      → 大概率是 order_by / 表名 / 列名 类无法参数化的标识符
#   2) 这种用法应通过 safeSQL.assert_table_allowed / safe_order_by 走白名单
#
# 这层只做 Warning，不阻断 manage.py；目的是把"看起来可疑的"列出来让作者审视。
# 误报可控：把光标移到那个 format 调用、加一行 `# safe_sql: order_by` 之类的注释即可。
# ===========================================================================
import ast
import os

_SCAN_ROOTS = [
    # 默认扫 my_app 下的 module / utils；INSTALLED_APPS 里其它包按需追加
    os.path.join(os.path.dirname(__file__), "module"),
    os.path.join(os.path.dirname(__file__), "utils"),
]

# SQL 调用形式（识别 "cursor.execute / .raw / .extra" 触发器）
_SQL_TRIGGERS = ("execute", "raw", "extra")


def _collect_sql_calls(tree):
    """
    遍历 AST，找出所有形如 cursor.execute(sql_str, ...) 的 sql 字符串节点。
    sql_str 可以是：
      a) Constant 字符串里直接含 {field}（很少见 —— 拼字符串就直接拼了）
      b) "...".format(x) 链式调用：execute 调用节点的第一参数是 .format() 的 Call
    """
    findings = []

    def _emit(line, sql):
        if "{table" in sql or "order by {" in sql.lower() or "set {" in sql.lower():
            findings.append((line, sql.strip().split("\n")[0][:120]))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        attr_name = None
        if isinstance(func, ast.Attribute):
            attr_name = func.attr
        else:
            continue
        if attr_name not in _SQL_TRIGGERS:
            continue
        if not node.args:
            continue
        first = node.args[0]
        # 情形 a：直接传字符串常量
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            _emit(first.lineno, first.value)
            continue
        # 情形 b：传的是 "...{field}...".format(x) —— 即 first 是 .format() 的 Call
        # 形如 Call(func=Attribute(value=Constant, attr='format'), args=[...])
        if isinstance(first, ast.Call) and isinstance(first.func, ast.Attribute) \
                and first.func.attr == "format" \
                and isinstance(first.func.value, ast.Constant) \
                and isinstance(first.func.value.value, str):
            sql = first.func.value.value
            _emit(first.func.value.lineno, sql)
    return findings


@register()
def check_raw_sql_format_usage(app_configs, **kwargs):
    """Stage D 静态扫描：cursor.execute("...{}...".format(x)) 类用法提示走白名单"""
    results = []
    for root in _SCAN_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, _, filenames in os.walk(root):
            for name in filenames:
                if not name.endswith(".py") or name == "__init__.py":
                    continue
                path = os.path.join(dirpath, name)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        source = fh.read()
                    tree = ast.parse(source, filename=path)
                except (SyntaxError, UnicodeDecodeError):
                    continue
                for line, sql_head in _collect_sql_calls(tree):
                    results.append(Warning(
                        "裸 SQL 含 .format 占位符：{}:{} — {}".format(path, line, sql_head),
                        hint=("若占位符是 order by / 表名 / 列名，请用 "
                              "my_app.utils.safeSQL.safe_order_by / assert_table_allowed 走白名单；"
                              "若是值参数化，请改用 %s 占位符 + 参数列表。"),
                        id="my_app.W002",
                    ))
    return results
