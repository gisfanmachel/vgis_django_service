#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 通用帮助类（WebSocket 版：语言标识来自消息体，不是 HTTP header）
# @Software: PyCharm
import asyncio
import logging
import os
from datetime import datetime

import config
from localization_enum import SysInfoEnum

logger = logging.getLogger(__name__)


class CommonHelper:
    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # 多语言
    # WebSocket 没有 HTTP header，语言标识统一放在客户端消息里：
    #   {"type": "subscribe", "localization": "EN", ...}
    # 取不到默认 CH
    # ------------------------------------------------------------------
    @staticmethod
    def get_local_str(STR_KEY, message):
        """从消息体取语言标识后返回提示语"""
        return CommonHelper.get_local_str2(STR_KEY, CommonHelper.get_local_flag(message))

    @staticmethod
    def get_local_str2(STR_KEY, local):
        """已知语言标识时直接取提示语"""
        return getattr(SysInfoEnum, "{}_{}".format(STR_KEY, local))

    @staticmethod
    def get_local_flag(message):
        """取消息体里 localization 的值，缺省 CH"""
        local = None
        if isinstance(message, dict):
            local = message.get("localization")
        if local is None or str(local).strip() == "":
            return "CH"
        return str(local).strip()

    # ------------------------------------------------------------------
    # 数值
    # ------------------------------------------------------------------
    @staticmethod
    def clamp_number(value, min_value, max_value, default):
        """把数值收敛到 [min_value, max_value]；非法值返回 default"""
        try:
            num = float(value)
        except (TypeError, ValueError):
            return default
        if num < min_value:
            return min_value
        if num > max_value:
            return max_value
        return num

    @staticmethod
    def batch_list(items, batch_size):
        """把列表按 batch_size 切块（生成器），用于 IN (...) 分批查询"""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]

    # ------------------------------------------------------------------
    # 时间
    # ------------------------------------------------------------------
    @staticmethod
    def get_curent_time_str():
        """当前时间的字符串格式"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def datetime_to_str(dt):
        """datetime 转字符串，None 返回 None"""
        return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None

    @staticmethod
    def get_last_hour_time(time_str):
        """取给定时间所在的上一整点，如 11:23 → 11:00、11:00 → 10:00"""
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        if dt.minute == 0:
            last_hour = dt.replace(hour=dt.hour - 1, minute=0, second=0, microsecond=0)
        else:
            last_hour = dt.replace(minute=0, second=0, microsecond=0)
        return last_hour.strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------------------------------------------
    # 其他
    # ------------------------------------------------------------------
    @staticmethod
    def is_valid_str(input_str):
        """判断字符串是否有效：None、空串、字符串'null'/'none' 都算无效"""
        if input_str is None:
            return False
        s = str(input_str).strip()
        if s == "" or s.lower() in ("null", "none"):
            return False
        return True

    @staticmethod
    def format_file_size(size_byte):
        """把字节数格式化成易读字符串"""
        size = float(size_byte)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024 or unit == "GB":
                return "{:.2f}{}".format(size, unit)
            size /= 1024

    @staticmethod
    def ensure_dir(path):
        """确保目录存在"""
        if path and not os.path.exists(path):
            os.makedirs(path)
        return path

    @staticmethod
    async def safe_send(websocket, payload):
        """
        安全发送 JSON：连接已关闭时返回 False 而不是抛异常。
        payload 为 dict，会自动 json.dumps(ensure_ascii=False)。
        """
        import json
        try:
            await websocket.send(json.dumps(payload, ensure_ascii=False))
            return True
        except Exception as e:
            logger.debug("发送消息失败（连接可能已关闭）: %s", e)
            return False

    @staticmethod
    async def sleep_with_cancel(seconds, cancel_event):
        """可被 asyncio.Event 提前唤醒的 sleep，用于让推送循环能立即退出"""
        try:
            await asyncio.wait_for(cancel_event.wait(), timeout=seconds)
            return True  # 被取消唤醒
        except asyncio.TimeoutError:
            return False  # 正常睡满
