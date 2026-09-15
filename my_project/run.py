"""
#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
@Project :zwbx_fzcd_service
@File    :run.py
@IDE     :PyCharm
@Author  :chenxw
@Date    :2023/9/22 15:16
@Descr:
"""
from waitress import serve
from my_project.wsgi import application

# 阶段 6.1：threads 4 → 16。
# 原配置在 50 并发下请求排队明显（waitress 是 thread-per-request 模型）。
# 注意：线程数不是越大越好，超过 CPU 核数反而因上下文切换降速，
# 这里取 16 是配合本机 12 核 + 超线程的常用上限。
serve(
    app=application,
    host='0.0.0.0',
    port=10846,
    threads=16
)

