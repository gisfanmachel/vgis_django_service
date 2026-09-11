#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : TCP 服务启动入口（示例）
#
#            新项目接入步骤：
#              1. 在 protocol.py 里按自己的报文格式实现一个 ProtocolHandler 子类
#                 （最常见的是继承 LengthPrefixedProtocol，改 FrameSpec 即可）
#              2. 在下面的 on_packet 里写业务处理；需要访问数据库时用 server.db_pool
#              3. 需要下行指令时用 web_api.register_command 注册
#              4. 配置全部走 config.py 的同名环境变量，不要写死在代码里
# @Software: PyCharm
import logging

# 先导入 logger_setup：模块导入即完成日志初始化，后续模块才能正常打日志
from logger_setup import logger, log_system_info

import config
from protocol import DemoProtocol, FrameSpec, LengthPrefixedProtocol
from server import TCPServer
from web_api import register_command

logger = logging.getLogger("main")


# ======================================================================
# 1) 业务处理回调：收到一个完整报文时被调用
# ======================================================================
def on_packet(packet, conn_info, server):
    """
    :param packet:    connection.Packet，含 device_id / msg_id / parsed 等
    :param conn_info: 该连接的信息（可能为 None，如连接刚被清理）
    :param server:    TCPServer 实例，可用 server.db_pool 取数据库连接
    """
    logger.info("收到报文 - 设备: %s，报文ID: %s，解析结果: %s",
                packet.device_id, packet.msg_id, packet.parsed)

    # 示例：把解析结果写库。真实项目改成自己的表结构。
    # if server.db_pool is not None:
    #     with server.db_pool as conn:
    #         with conn.cursor() as cur:
    #             cur.execute(
    #                 "INSERT INTO your_table (id, device_id, msg_id, payload, create_time) "
    #                 "VALUES (%s, %s, %s, %s, now())",
    #                 [SnowflakeIDUtil.snowflakeId(), packet.device_id,
    #                  packet.msg_id, packet.parsed.get("payload_hex")],
    #             )
    #         conn.commit()


def on_client_connected(conn_info, server):
    logger.info("客户端上线: %s", conn_info.client_id)


def on_client_disconnected(conn_info, server):
    logger.info("客户端下线: %s，共接收 %s 字节", conn_info.client_id, conn_info.total_bytes_received)


# ======================================================================
# 2) 下行指令（通过 POST /command/<name> 触发）
# ======================================================================
@register_command("ping_device")
def ping_device(server, payload):
    """示例指令：向指定设备下发一条空载荷报文，验证链路是否通"""
    device_id = payload.get("device_id")
    if device_id is None:
        return {"success": False, "info": "缺少 device_id"}

    raw = server.protocol.build(msg_id=0x01, payload=b"", device_id=int(device_id))
    ok = server.send_to_device(device_id, raw)
    if ok:
        return {"success": True, "info": "已下发", "hex": raw.hex().upper()}
    return {"success": False, "info": "设备未连接"}


@register_command("connections_count")
def connections_count(server, payload):
    """示例指令：返回当前连接数"""
    return {"success": True, "info": {"count": len(server.connections)}}


# ======================================================================
# 3) 启动
# ======================================================================
def build_protocol():
    """
    构造协议处理器。三种用法按需选择：
      - DemoProtocol()：示例协议（帧头+长度+BCC），可直接跑通
      - LengthPrefixedProtocol(FrameSpec(...))：只要「帧头+长度字段」，不做校验
      - 自己继承 ProtocolHandler：协议复杂时用
    """
    return DemoProtocol()


def main():
    log_system_info()
    logger.info("%s", "=" * 60)
    logger.info("通用TCP服务启动 - 监听 %s:%s", config.TCP_SERVER_HOST, config.TCP_SERVER_PORT)
    logger.info("线程池大小: %s，消费线程数: %s，最大连接数: %s",
                config.THREAD_POOL_SIZE, config.DATA_PROCESSOR_THREADS, config.TCP_CLIENT_MAX_NUMBERS)
    logger.info("数据库: %s", "已启用" if config.DB_ENABLED else "未启用（DB_ENABLED=false）")
    logger.info("Web控制接口: %s", "已启用" if config.WEB_API_ENABLED else "未启用")
    logger.info("%s", "=" * 60)

    server = TCPServer(
        protocol=build_protocol(),
        on_packet=on_packet,
        on_client_connected=on_client_connected,
        on_client_disconnected=on_client_disconnected,
    )
    server.start()


if __name__ == "__main__":
    main()
