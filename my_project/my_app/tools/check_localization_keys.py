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

# 扫描范围：my_app 与 my_project 下的所有 py 文件
SCAN_DIRS = [BASE_DIR / "my_app", BASE_DIR / "my_project"]

# 注释/文档里用于举例的占位 key，不参与校验
IGNORE_KEYS = {"KEY"}


def collect_enum_keys():
    text = ENUM_FILE.read_text(encoding="utf-8")
    ch = set(re.findall(r'^\s{4}([A-Z0-9_]+)_CH\s*=', text, re.M))
    en = set(re.findall(r'^\s{4}([A-Z0-9_]+)_EN\s*=', text, re.M))
    return ch, en


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
