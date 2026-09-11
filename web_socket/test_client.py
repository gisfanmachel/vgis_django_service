#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 测试用 WebSocket 客户端：跑一遍订阅 → 收推送 → 改频率 → 取消订阅 → 心跳
#            用法：python test_client.py [ws://host:port]
# @Software: PyCharm
import asyncio
import json
import sys

import websockets

URI = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8765"


async def recv_for(websocket, seconds, label):
    """在指定的总时长内接收并打印服务端推送（用截止时间，不是每条消息各等 N 秒）"""
    import time

    received = 0
    deadline = time.monotonic() + seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=remaining)
        except asyncio.TimeoutError:
            break
        data = json.loads(message)
        received += 1
        # 推送数据只打前 3 条，避免刷屏
        if received <= 3:
            print("[{}] 收到: {}".format(label, json.dumps(data, ensure_ascii=False)[:200]))
    print("[{}] 共收到 {} 条".format(label, received))
    return received


async def main():
    async with websockets.connect(URI) as websocket:
        print("已连接 {}".format(URI))

        # 1) 心跳
        await websocket.send(json.dumps({"type": "ping"}))
        print("心跳响应:", await asyncio.wait_for(websocket.recv(), timeout=5))

        # 2) 查询服务端状态
        await websocket.send(json.dumps({"type": "status"}))
        print("服务端状态:", await asyncio.wait_for(websocket.recv(), timeout=5))

        # 3) 订阅（间隔 1 秒，带上业务字段 + 语言）
        await websocket.send(json.dumps({
            "type": "subscribe",
            "interval": 1,
            "localization": "CH",
            "device_ids": [1, 2, 3],
        }))
        print("订阅响应:", await asyncio.wait_for(websocket.recv(), timeout=5))
        await recv_for(websocket, 3.5, "1秒间隔")

        # 4) 改成 0.2 秒，验证频率切换能立即生效
        await websocket.send(json.dumps({"type": "set_interval", "interval": 0.2}))
        print("改频率响应:", await asyncio.wait_for(websocket.recv(), timeout=5))
        await recv_for(websocket, 2, "0.2秒间隔")

        # 5) 非法间隔应被拒绝
        await websocket.send(json.dumps({"type": "set_interval", "interval": "abc"}))
        print("非法间隔响应:", await asyncio.wait_for(websocket.recv(), timeout=5))

        # 6) 取消订阅
        await websocket.send(json.dumps({"type": "unsubscribe"}))
        print("取消订阅响应:", await asyncio.wait_for(websocket.recv(), timeout=5))
        got = await recv_for(websocket, 1.5, "取消后")
        print("取消订阅后不再收到推送: {}".format("是" if got == 0 else "否（仍有推送！）"))

        # 7) 未知消息类型应回错误
        await websocket.send(json.dumps({"type": "no_such_type"}))
        print("未知类型响应:", await asyncio.wait_for(websocket.recv(), timeout=5))

    print("连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
