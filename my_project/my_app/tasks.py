# tasks.py

from __future__ import absolute_import, unicode_literals

import time

from celery import shared_task


# @shared_task
# def add(x, y):
#     time.sleep(20)  # 模拟任务处理
#     return x + y


# # 使用Celery的例子
from my_project.celery import app

@app.task
def add(x, y):
    print("start excute task")
    time.sleep(200)  # 模拟任务处理
    print("finish excute task")
    return x + y