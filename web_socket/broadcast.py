#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 客户端数据推送任务
#
#            为每个 WebSocket 客户端维护一个独立的 asyncio 任务，按固定间隔调用
#            callback(websocket) 取数据并推送。callback 返回 None 或空则本轮跳过。
#
#            典型用法：
#                task = ClientBroadcastTask(websocket, interval=1, callback=fetch)
#                await task.start()
#                await task.update_interval(2)   # 客户端中途改频率
#                await task.stop()
# @Software: PyCharm
import asyncio
import logging

from commonUtility import CommonHelper

logger = logging.getLogger(__name__)


class ClientBroadcastTask:
    """单个客户端的数据推送任务"""

    def __init__(self, websocket, interval, callback, task_type="realtime"):
        """
        :param websocket: 客户端连接
        :param interval:  推送间隔（秒）
        :param callback:  取数据回调，签名 async def callback(websocket) -> dict | None
        :param task_type: 任务类型标签，仅用于日志区分（如 realtime / review）
        """
        self.websocket = websocket
        self.interval = interval
        self.callback = callback
        self.task_type = task_type

        self.client_id = id(websocket)
        self.task = None
        self.is_running = False
        self.cancel_event = asyncio.Event()

    # ------------------------------------------------------------------
    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.cancel_event = asyncio.Event()
        self.task = asyncio.create_task(self._loop())
        logger.info("客户端 %s 的 %s 推送任务启动，间隔 %.2f 秒",
                    self.client_id, self.task_type, self.interval)

    async def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        # 先唤醒可能正在 sleep 的循环，让它立刻退出
        self.cancel_event.set()

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        logger.info("客户端 %s 的 %s 推送任务已停止", self.client_id, self.task_type)

    async def update_interval(self, new_interval):
        """更新推送间隔；正在等待的那一轮会立刻被唤醒并按新间隔继续"""
        if new_interval is None or abs(new_interval - self.interval) < 1e-6:
            return
        logger.info("客户端 %s 推送间隔 %.2f → %.2f 秒", self.client_id, self.interval, new_interval)
        self.interval = new_interval
        # 唤醒循环，让新间隔立即生效
        self.cancel_event.set()
        self.cancel_event = asyncio.Event()

    # ------------------------------------------------------------------
    async def _loop(self):
        while self.is_running:
            try:
                payload = await self.callback(self.websocket)

                if payload:
                    if not await CommonHelper.safe_send(self.websocket, payload):
                        logger.info("客户端 %s 连接已关闭，停止推送", self.client_id)
                        break

                # 间隔等待；被 cancel_event 唤醒（stop 或改频率）时提前返回
                cancelled = await CommonHelper.sleep_with_cancel(self.interval, self.cancel_event)
                if cancelled:
                    # 是 stop() 触发的就退出；是 update_interval() 触发的就重置事件继续跑
                    if not self.is_running:
                        break
                    self.cancel_event = asyncio.Event()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("客户端 %s 的 %s 推送任务出错: %s", self.client_id, self.task_type,
                             e, exc_info=True)
                # 出错后短暂等待再继续，避免异常时疯狂刷日志
                await asyncio.sleep(min(1, self.interval))

    # ------------------------------------------------------------------
    def __repr__(self):
        return "<ClientBroadcastTask client={} type={} interval={} running={}>".format(
            self.client_id, self.task_type, self.interval, self.is_running)
