#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 多语言提示语自检脚本
#            1) 校验 localization_enum.py 里 <KEY>_CH / <KEY>_EN 是否成对
#            2) 校验代码里 get_local_str("KEY", ...) / get_local_str2("KEY", ...) /
#               SysInfoEnum.KEY_CH 引用到的 key 是否都已定义
#            用法：python my_app/tools/check_localization_keys.py
#            建议接入 CI 或提交前自查，避免运行期 AttributeError
# @Software: PyCharm
import pathlib
import re
import sys

# 项目根目录（本文件位于 my_app/tools/ 下）
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
ENUM_FILE = BASE_DIR / "my_app" / "enum" / "localization_enum.py"
MODULE_DIR = BASE_DIR / "my_app" / "module"

# 扫描范围：my_app 与 my_project 下的所有 py 文件
SCAN_DIRS = [BASE_DIR / "my_app", BASE_DIR / "my_project"]

# 注释/文档里用于举例的占位 key，不参与校验
IGNORE_KEYS = {"KEY"}


def collect_enum_keys():
    """全局词表 my_app/enum/localization_enum.py 的 CH/EN 键"""
    text = ENUM_FILE.read_text(encoding="utf-8")
    ch = set(re.findall(r'^\s{4}([A-Z0-9_]+)_CH\s*=', text, re.M))
    en = set(re.findall(r'^\s{4}([A-Z0-9_]+)_EN\s*=', text, re.M))
    return ch, en


def collect_module_enum_keys():
    """
    各分模块自己的词表 my_app/module/<模块>/localization.py。
    返回 {模块名: (CH键集合, EN键集合)}
    """
    result = {}
    if not MODULE_DIR.is_dir():
        return result
    for loc in sorted(MODULE_DIR.glob("*/localization.py")):
        module_name = loc.parent.name
        text = loc.read_text(encoding="utf-8")
        # 用 \s+ 容忍任意缩进（一个文件里可能有多个 Enum 类）
        ch = set(re.findall(r'^\s+([A-Z0-9_]+)_CH\s*=', text, re.M))
        en = set(re.findall(r'^\s+([A-Z0-9_]+)_EN\s*=', text, re.M))
        result[module_name] = (ch, en)
    return result


def collect_used_keys():
    used = {}
    for scan_dir in SCAN_DIRS:
        for path in scan_dir.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for key in re.findall(r'get_local_str2?\(\s*["\']([A-Z0-9_]+)["\']', text):
                if key not in IGNORE_KEYS:
                    used.setdefault(key, set()).add(path.name)
            for key in re.findall(r'SysInfoEnum\.([A-Z0-9_]+)_(?:CH|EN)', text):
                if key not in IGNORE_KEYS:
                    used.setdefault(key, set()).add(path.name)
    return used


def collect_module_used_keys():
    """
    收集分模块词条的引用，两种写法都认：
      1. 显式跨模块：CommonHelper.get_local_str_from_module("模块名", "KEY", request)
      2. 模块内包装：self._t(request, "KEY")（模块内部常用，模块名由常量传参故静态看不到）
    返回 {模块名: {KEY: {引用文件}}}
    """
    used = {}
    for scan_dir in SCAN_DIRS:
        for path in scan_dir.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            # 写法 1：显式带模块名
            for mod, key in re.findall(
                    r'get_local_str_from_module\(\s*["\']([a-z_]+)["\']\s*,\s*["\']([A-Z0-9_]+)["\']', text):
                if key not in IGNORE_KEYS:
                    used.setdefault(mod, {}).setdefault(key, set()).add(path.name)
            # 写法 2：模块目录内的 self._t(request, "KEY") / _t(request, 'KEY')
            parts = path.parts
            if "module" in parts and path.name != "localization.py":
                idx = parts.index("module")
                if idx + 1 < len(parts):
                    mod = parts[idx + 1]
                    for key in re.findall(r'_t\(\s*request\s*,\s*["\']([A-Z0-9_]+)["\']', text):
                        if key not in IGNORE_KEYS:
                            used.setdefault(mod, {}).setdefault(key, set()).add(path.name)
    return used


def main():
    failed = False

    # ---------- 一、全局词表 ----------
    ch, en = collect_enum_keys()
    unpaired = sorted(ch ^ en)
    used = collect_used_keys()
    missing = {k: sorted(v) for k, v in used.items() if k not in ch}

    print("=== 全局词表 my_app/enum/localization_enum.py ===")
    print("CH {} 条，EN {} 条".format(len(ch), len(en)))
    if unpaired:
        failed = True
        print("[错误] 以下 key 只有 CH 或只有 EN，运行期会 AttributeError：")
        for key in unpaired:
            print("    {}  (CH:{} EN:{})".format(key, key in ch, key in en))
    else:
        print("[通过] CH / EN 全部成对")

    if missing:
        failed = True
        print("[错误] 代码引用了但全局词表中缺失的 key：")
        for key, files in sorted(missing.items()):
            print("    {}   <- {}".format(key, ", ".join(files)))
    else:
        print("[通过] 代码引用的 {} 个 key 均已定义".format(len(used)))

    # ---------- 二、各分模块词表 ----------
    module_keys = collect_module_enum_keys()
    module_used = collect_module_used_keys()
    print()
    print("=== 分模块词表 my_app/module/<模块>/localization.py ===")
    if not module_keys:
        print("(未发现分模块词表)")
    for module_name in sorted(set(module_keys) | set(module_used)):
        m_ch, m_en = module_keys.get(module_name, (set(), set()))
        m_unpaired = sorted(m_ch ^ m_en)
        m_missing = {k: sorted(v) for k, v in module_used.get(module_name, {}).items() if k not in m_ch}
        m_unused = sorted(m_ch - set(module_used.get(module_name, {})))

        print("  [{}] CH {} / EN {}".format(module_name, len(m_ch), len(m_en)))
        if m_unpaired:
            failed = True
            print("     [错误] CH/EN 不成对：{}".format(m_unpaired))
        if m_missing:
            failed = True
            print("     [错误] 引用了但缺失：")
            for key, files in sorted(m_missing.items()):
                print("         {}   <- {}".format(key, ", ".join(files)))
        if not m_unpaired and not m_missing:
            print("     [通过] 全部成对且引用均已定义")
        if m_unused:
            # 未使用不算错（可能是给前端/其它项目预留的），只提示
            print("     [提示] {} 条词条当前未被代码引用：{}".format(
                len(m_unused), "、".join(m_unused[:6]) + ("…" if len(m_unused) > 6 else "")))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
