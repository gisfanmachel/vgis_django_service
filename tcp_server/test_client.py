#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 测试用客户端：按协议组包发给 TCP 服务，并打印服务端响应
#            用法：python test_client.py [host] [port]
# @Software: PyCharm
import socket
import sys
import time

from protocol import DemoProtocol

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 3869


def main():
    protocol = DemoProtocol()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((HOST, PORT))
    print("已连接 {}:{}".format(HOST, PORT))

    try:
        for i in range(3):
            # 组一个「定位/上报」报文（报文ID 0x01，设备ID 12345）
            payload = bytes([i] * 8)
            packet = protocol.build(msg_id=0x01, payload=payload, device_id=12345)
            print("[{}] 发送: {}".format(i + 1, packet.hex().upper()))
            sock.sendall(packet)

            # 半包测试：把一个完整报文拆成两段发，服务端应当能拼回来
            half = len(packet) // 2
            sock.sendall(packet[:half])
            time.sleep(0.05)
            sock.sendall(packet[half:])
            print("[{}] 半包发送完成".format(i + 1))

            time.sleep(0.5)

        # 粘包测试：连发两个完整报文
        p1 = protocol.build(msg_id=0x01, payload=b"\x01\x02", device_id=12345)
        p2 = protocol.build(msg_id=0x10, payload=b"\x03\x04", device_id=12345)
        sock.sendall(p1 + p2)
        print("粘包发送完成（2 个报文）")

        # 读一下服务端可能返回的数据
        sock.settimeout(2)
        try:
            data = sock.recv(4096)
            if data:
                packets, _ = protocol.split_packets(data)
                for p in packets:
                    print("收到响应: {}, 解析: {}".format(p.hex().upper(), protocol.parse(p)))
            else:
                print("服务端未返回数据（正常，取决于业务实现）")
        except socket.timeout:
            print("读取响应超时（正常，取决于业务实现）")
    finally:
        sock.close()
        print("连接已关闭")


if __name__ == "__main__":
    main()
