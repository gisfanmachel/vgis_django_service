#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 连接状态与连接信息
# @Software: PyCharm
import time
from datetime import datetime
from enum import Enum


class ConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


class ConnectionInfo:
    """单个客户端的连接信息与统计"""

    __slots__ = (
        "socket", "address", "thread", "status",
        "last_heartbeat", "connect_time", "last_activity",
        "reconnect_count", "total_bytes_received", "total_bytes_sent",
        "device_id", "extra",
    )

    def __init__(self, socket, address, thread=None, status=ConnectionStatus.CONNECTED,
                 last_heartbeat=None, connect_time=None, reconnect_count=0,
                 total_bytes_received=0, total_bytes_sent=0, device_id=None, extra=None):
        self.socket = socket
        self.address = address
        self.thread = thread
        self.status = status
        self.last_heartbeat = last_heartbeat
        self.connect_time = connect_time or datetime.now()
        self.last_activity = self.connect_time
        self.reconnect_count = reconnect_count
        self.total_bytes_received = total_bytes_received
        self.total_bytes_sent = total_bytes_sent
        # 业务层可在解析出设备标识后回填，用于按设备定位连接
        self.device_id = device_id
        # 业务自定义扩展字段
        self.extra = extra if extra is not None else {}

    @property
    def client_id(self):
        """连接唯一标识：IP:PORT"""
        return "{}:{}".format(self.address[0], self.address[1])

    @property
    def connection_seconds(self):
        """已连接时长（秒）"""
        if not self.connect_time:
            return 0
        return (datetime.now() - self.connect_time).total_seconds()

    @property
    def idle_seconds(self):
        """空闲时长（秒）"""
        if not self.last_activity:
            return 0
        return (datetime.now() - self.last_activity).total_seconds()

    def touch(self):
        """刷新最后活动时间"""
        self.last_activity = datetime.now()

    def to_dict(self):
        """转成可直接 JSON 序列化的字典（用于监控接口）"""
        return {
            "client_id": self.client_id,
            "address": self.client_id,
            "device_id": self.device_id,
            "status": self.status.value,
            "connect_time": self.connect_time.strftime("%Y-%m-%d %H:%M:%S") if self.connect_time else None,
            "last_activity": self.last_activity.strftime("%Y-%m-%d %H:%M:%S") if self.last_activity else None,
            "connection_seconds": round(self.connection_seconds, 1),
            "idle_seconds": round(self.idle_seconds, 1),
            "reconnect_count": self.reconnect_count,
            "total_bytes_received": self.total_bytes_received,
            "total_bytes_sent": self.total_bytes_sent,
        }


class Packet:
    """一个已拆包/解析的完整报文"""

    __slots__ = ("raw", "address", "device_id", "device_type", "msg_id", "payload", "parsed", "recv_time")

    def __init__(self, raw, address=None, device_id=None, device_type=None,
                 msg_id=None, payload=b"", parsed=None, recv_time=None):
        self.raw = raw
        self.address = address
        self.device_id = device_id
        self.device_type = device_type
        self.msg_id = msg_id
        self.payload = payload
        self.parsed = parsed if parsed is not None else {}
        self.recv_time = recv_time or time.time()

    @property
    def client_id(self):
        if not self.address:
            return None
        return "{}:{}".format(self.address[0], self.address[1])

    def to_dict(self):
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "msg_id": self.msg_id,
            "address": self.client_id,
            "recv_time": self.recv_time,
            "parsed": self.parsed,
        }
