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

serve(
    app=application,
    host='0.0.0.0',
    port=10846,
    threads=4
)

