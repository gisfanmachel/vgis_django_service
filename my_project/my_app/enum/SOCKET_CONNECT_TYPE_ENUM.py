#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
from enum import Enum

'''
    socket connect type enum 

'''
class SOCKET_CONNECT_TYPE_ENUM(Enum):

    #心跳检测
    HEARTBEAT_CHECK = "heartbeat_check"

    #登陆
    LOGIN = "login"

    DATA = "data"

    REBACK = "reback"

    def getEnumByName(name):
        for socket_connect_type_enum in SOCKET_CONNECT_TYPE_ENUM:
            if socket_connect_type_enum.value == name:
                return socket_connect_type_enum
        return None


