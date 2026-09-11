#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 多语言提示语自检
#            1) 校验 localization_enum.py 里 <KEY>_CH / <KEY>_EN 是否成对
#            2) 校验代码里 get_local_str("KEY", ...) / get_local_str2("KEY", local) 引用到的 key 是否都已定义
#            用法：python check_localization_keys.py
#            全部通过退出码 0，可接入 CI 或提交前钩子
# @Software: PyCharm
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENUM_FILE = os.path.join(BASE_DIR, "localization_enum.py")

# 只扫描当前目录下的 py 文件（本框架是独立部署的目录）
IGNORE_KEYS = {"KEY"}  # 注释/文档里用于举例的占位 key
IGNORE_FILES = {os.path.basename(__file__)}


def collect_enum_keys():
    with open(ENUM_FILE, encoding="utf-8") as f:
        text = f.read()
    ch = set(re.findall(r'^\s{4}([A-Z0-9_]+)_CH\s*=', text, re.M))
    en = set(re.findall(r'^\s{4}([A-Z0-9_]+)_EN\s*=', text, re.M))
    return ch, en


def collect_used_keys():
    used = {}
    for name in os.listdir(BASE_DIR):
        if not name.endswith(".py") or name in IGNORE_FILES:
            continue
        with open(os.path.join(BASE_DIR, name), encoding="utf-8", errors="ignore") as f:
            text = f.read()
        keys = re.findall(r'get_local_str2?[0-9]?\(\s*["\']([A-Z0-9_]+)["\']', text)
        keys += re.findall(r"SysInfoEnum\.([A-Z0-9_]+)_(?:CH|EN)", text)
        for key in keys:
            if key not in IGNORE_KEYS:
                used.setdefault(key, set()).add(name)
    return used


def main():
    ch, en = collect_enum_keys()
    unpaired = sorted(ch ^ en)
    used = collect_used_keys()
    missing = {k: sorted(v) for k, v in used.items() if k not in ch}

    print("枚举提示语：CH {} 条，EN {} 条".format(len(ch), len(en)))
    if unpaired:
        print("[错误] 以下 key 只有 CH 或只有 EN，运行期会 AttributeError：")
        for key in unpaired:
            print("    {}  (CH:{} EN:{})".format(key, key in ch, key in en))
    else:
        print("[通过] CH / EN 全部成对")

    if missing:
        print("[错误] 代码引用了但枚举中缺失的 key：")
        for key, files in sorted(missing.items()):
            print("    {}   <- {}".format(key, ", ".join(files)))
    else:
        print("[通过] 代码引用的 {} 个 key 均已定义".format(len(used)))

    return 1 if (unpaired or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
