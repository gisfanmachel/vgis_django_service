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
