import asyncio
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
import json
import datetime
from django.db import connection
from my_app.enum.base_env_enum import BaseEnvEnum
from my_app.enum.SOCKET_STATUS_ENUM import SOCKET_STATUS_ENUM
from my_app.enum.SOCKET_CONNECT_TYPE_ENUM import SOCKET_CONNECT_TYPE_ENUM

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # 从 WebSocket 连接的请求头中获取认证 token
        headers = dict(scope.get("headers", []))
        # oken = headers.get(b"sec-websocket-protocol", b"").decode("utf-8").split(" ")[-1]
        token = scope.get("query_string").decode('utf-8')[14:]
        # token = headers.get(b"authorization", b"").decode("utf-8").split(" ")[-1]
        #

        # 将 token 添加到 scope 中
        scope["user"] = await self.get_user_from_token(token)

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_token(self, token):
        # 根据 token 获取用户
        try:
            return Token.objects.get(key=token).user
        except Token.DoesNotExist:
            return AnonymousUser()


class AlertConsumer(AsyncJsonWebsocketConsumer):

    # 这里除了 WebsocketConsumer 之外还有
    # JsonWebsocketConsumer
    # AsyncWebsocketConsumer
    # AsyncJsonWebsocketConsumer
    # WebsocketConsumer 与 JsonWebsocketConsumer 就是多了一个可以自动处理JSON的方法
    # AsyncWebsocketConsumer 与 AsyncJsonWebsocketConsumer 也是多了一个JSON的方法
    # AsyncWebsocketConsumer 与 WebsocketConsumer 才是重点
    # 看名称似乎理解并不难 Async 无非就是异步带有 async / await
    # 是的理解并没有错,但对与我们来说他们唯一不一样的地方,可能就是名字的长短了,用法是一模一样的
    # 最夸张的是,基类是同一个,而且这个基类的方法也是Async异步
    async def websocket_connect(self, message):
        await self.accept()
        # if self.scope['user'].is_anonymous:
        #     print('用户没有登陆')
        #     self.close()
        # else:
        #     user = self.scope['user']
        #     self.user = user
        #     id = user.id
        #     username = user.username
        #
        #     self.group_name = BaseEnvEnum.ALERT_INFO_COMSUMERS_GROUP.value.format(username, id)
        #
        #     await self.accept()
        #     await self.channel_layer.group_add(self.group_name, self.channel_name)
        #     await self.send_message(await self.connect_success(username, id, self.channel_name))


    async def send_msg(self, group_id, data_info, socket_connect_type):
        if data_info:
            print('group_id = {} 发送消息,发送时间: {},msg_type = {}'.format(group_id, datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"), "登陆系统"))
            await self.send(text_data=json.dumps({
                'data': data_info,
                'socket_connect_type': socket_connect_type
            }))
            # 用户只要一登陆就初始化发送

    async def connect_success(self, username, user_id, channel_name):

        success_msg = {
            "message":
                {
                    "username": username,
                    "successes": True,
                    "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "msg": "socket 连接成功",
                    "status": SOCKET_STATUS_ENUM.SUCCESS.value,
                    "channel_name": channel_name
                },
            "socket_connect_type":
                SOCKET_CONNECT_TYPE_ENUM.LOGIN.value
        }
        return success_msg

    '''
        前端发来消息 ->
        1.发来心跳信息 5分钟发一次心跳信息 
        heartbeat_check
        2.心跳检查 
          1.5分钟一次心跳检测
            {
                "message" {
                    "socket_connect_type":"heartbeat_check"
                }
            }
          2.相应
          {
            "socket_connect_type":"heartbeat_check",
            "successes":True,
            "time":datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "msg":"socket heartbeat_check ok",
            "status": SOCKET_STATUS_ENUM.SUCCESS.value,
            "channel_name": channel_name
         }


    '''

    async def websocket_receive(self, msg):

        text_data_json = json.loads(msg['text'])

        message = text_data_json['message']

        socket_connect_type = message['socket_connect_type']

        if SOCKET_CONNECT_TYPE_ENUM.HEARTBEAT_CHECK.value == socket_connect_type:
            msg = await self.receive_reback_msg(socket_connect_type)
            # 心跳检测
            # Send message to room group
            await self.channel_layer.group_send(

                self.group_name,
                {
                    'type': 'send.message',  # 这里的type 实际上就是 下面的chat_message自定义函数
                    'message': msg,
                    'socket_connect_type': SOCKET_STATUS_ENUM.REBACK.value
                }
            )

    # 相应用户的信息
    async def receive_reback_msg(self, socket_connect_type):
        user = self.user
        user_id = user.id
        username = user.username
        channel_name = self.channel_name

        return {
            "user_id": user_id,
            "username": username,
            "socket_connect_type": socket_connect_type,
            "successes": True,
            "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "msg": "socket {} ok".format(socket_connect_type),
            "status": SOCKET_STATUS_ENUM.SUCCESS.value,
            "channel_name": channel_name
        }

    async def websocket_disconnect(self, message):
        try:
            if self.group_name is not None:
                group_name = self.group_name
                channel_name = self.channel_name
                print("用户关闭连接group_name = {}, channel_name = {}", group_name, channel_name)

                await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception as ex:
            pass

        # Receive message from room group

    async def send_message(self, event):
        msg = event['message']
        socket_connect_type = event['socket_connect_type']
        await self.send(text_data=json.dumps({
            'data': msg,
            'socket_connect_type': socket_connect_type
        }))
