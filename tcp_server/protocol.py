#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 报文协议抽象层
#            框架只负责「连接/线程/队列/监控」，报文相关的拆包、校验、解析、组包
#            全部由 ProtocolHandler 子类实现。新项目继承 ProtocolHandler 即可。
#
#            拆包（粘包/半包处理）的通用逻辑已实现在 ProtocolHandler.split_packets()，
#            子类通常只需要实现 payload_length / verify / parse / build 四个钩子。
#
#            如果只是「帧头 + 长度字段」这种最常见布局，可直接用 LengthPrefixedProtocol。
# @Software: PyCharm
import logging
import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ProtocolHandler(ABC):
    """报文协议处理基类"""

    #: 帧头字节，如 b"\xa0\xa1"
    header: bytes = b""
    #: 包头（帧头 + 各定长字段）总长度
    header_len: int = 0

    #: 报文ID → 说明，供监控接口展示；子类按自己的协议填写
    msg_types: Dict[int, str] = {}

    # ------------------------------------------------------------------
    # 子类必须实现的钩子
    # ------------------------------------------------------------------
    @abstractmethod
    def payload_length(self, header: bytes) -> Optional[int]:
        """
        从包头里读出「载荷长度」（不含包头本身）。

        :param header: 长度等于 self.header_len 的包头字节
        :return: 载荷字节数；无法解析时返回 None
        """

    def verify(self, packet: bytes) -> bool:
        """
        校验整包（如 BCC 校验和）。默认不做校验，子类按需重写。

        :param packet: 完整报文（包头 + 载荷）
        """
        return True

    def parse(self, packet: bytes) -> Optional[Dict]:
        """
        解析完整报文，返回业务字段字典。默认返回空字典，子类按需重写。

        返回值会被塞进 Packet.parsed，业务层在 on_packet 回调里取用。
        """
        return {}

    def build(self, msg_id: int, payload: bytes = b"", **kwargs) -> bytes:
        """
        组下行报文（平台 → 设备）。默认不支持下行，子类按需重写。
        """
        raise NotImplementedError("当前协议未实现组包（下行）能力")

    # ------------------------------------------------------------------
    # 通用拆包逻辑（子类一般不需要重写）
    # ------------------------------------------------------------------
    def split_packets(self, buffer: bytes) -> Tuple[List[bytes], bytes]:
        """
        从接收缓冲区里切出所有完整报文。

        :return: (完整报文列表, 剩余不足一包的缓冲区)
        """
        packets: List[bytes] = []
        if not self.header or self.header_len <= 0:
            # 未配置协议时不做拆包，把整个 buffer 当作一包交给业务处理
            if buffer:
                return [buffer], b""
            return packets, buffer

        while len(buffer) >= self.header_len:
            # 帧头不对：逐字节右移重新对齐
            if buffer[:len(self.header)] != self.header:
                logger.warning("包头错误，跳过1字节重新对齐，当前头部: %s", buffer[:8].hex())
                buffer = buffer[1:]
                continue

            header = buffer[:self.header_len]
            length = self.payload_length(header)
            if length is None or length < 0:
                logger.warning("无法从包头解析载荷长度，跳过1字节重新对齐")
                buffer = buffer[1:]
                continue

            total_length = self.header_len + length
            if len(buffer) < total_length:
                # 半包：等待更多数据
                break

            packets.append(buffer[:total_length])
            buffer = buffer[total_length:]

        return packets, buffer

    def extract_device_info(self, packet: bytes) -> Dict:
        """从报文中提取设备标识，用于回填 ConnectionInfo.device_id。默认不提取。"""
        return {"device_id": None, "device_type": None, "msg_id": None}


class PassThroughProtocol(ProtocolHandler):
    """
    直通协议：不拆包，把每次 recv 到的数据当作一个「报文」交给业务。

    仅用于调试或对端已经保证「一次发送 = 一个完整包」的场景。
    生产环境请实现自己的 ProtocolHandler。
    """

    header = b""
    header_len = 0

    def payload_length(self, header: bytes) -> Optional[int]:
        return 0

    def parse(self, packet: bytes) -> Optional[Dict]:
        return {"payload_len": len(packet), "payload_hex": packet.hex().upper()}


# ----------------------------------------------------------------------
# 最常用的实现：帧头 + 长度字段
# ----------------------------------------------------------------------
@dataclass
class FrameSpec:
    """
    「帧头 + 长度字段」布局描述。

    例：包头 = 帧头(2) | 载荷长度(2, 大端) | 设备ID(4) | 报文ID(1)
        FrameSpec(header=b"\xa0\xa1", header_len=9,
                  length_offset=2, length_size=2,
                  device_id_offset=4, device_id_size=4,
                  msg_id_offset=8, msg_id_size=1)
    """
    header: bytes = b"\xa0\xa1"
    header_len: int = 9
    # 长度字段
    length_offset: int = 2
    length_size: int = 2
    length_byteorder: str = "big"
    # 设备标识（可选）
    device_id_offset: Optional[int] = 4
    device_id_size: int = 4
    # 设备类型（可选）
    device_type_offset: Optional[int] = None
    device_type_size: int = 1
    # 报文ID（可选）
    msg_id_offset: Optional[int] = 8
    msg_id_size: int = 1
    # 校验相关：校验字节在包头中的偏移，以及需要参与校验的字节范围
    checksum_offset: Optional[int] = None
    checksum_size: int = 1
    checksum_start: int = 0
    checksum_end: int = 0  # 0 表示校验到载荷末尾


class LengthPrefixedProtocol(ProtocolHandler):
    """
    「帧头 + 长度字段」协议的通用实现，可直接实例化使用，
    也可继承后重写 verify / parse / build 补充业务语义。
    """

    def __init__(self, spec: Optional[FrameSpec] = None, msg_types: Optional[Dict[int, str]] = None):
        self.spec = spec or FrameSpec()
        self.header = self.spec.header
        self.header_len = self.spec.header_len
        self.msg_types = msg_types or {}

    # ------------------------------------------------------------------
    def _read_int(self, data: bytes, offset: Optional[int], size: int) -> Optional[int]:
        if offset is None:
            return None
        chunk = data[offset:offset + size]
        if len(chunk) < size:
            return None
        return int.from_bytes(chunk, byteorder=self.spec.length_byteorder, signed=False)

    def payload_length(self, header: bytes) -> Optional[int]:
        return self._read_int(header, self.spec.length_offset, self.spec.length_size)

    def extract_device_info(self, packet: bytes) -> Dict:
        return {
            "device_id": self._read_int(packet, self.spec.device_id_offset, self.spec.device_id_size),
            "device_type": self._read_int(packet, self.spec.device_type_offset, self.spec.device_type_size),
            "msg_id": self._read_int(packet, self.spec.msg_id_offset, self.spec.msg_id_size),
        }

    def verify(self, packet: bytes) -> bool:
        """按 spec 配置做异或（BCC）校验；未配置 checksum_offset 时不做校验"""
        if self.spec.checksum_offset is None:
            return True
        expect = self._read_int(packet, self.spec.checksum_offset, self.spec.checksum_size)
        if expect is None:
            return False
        end = self.spec.checksum_end or len(packet)
        bcc = 0
        for b in packet[self.spec.checksum_start:end]:
            bcc ^= b
        return bcc == expect

    def parse(self, packet: bytes) -> Optional[Dict]:
        """给出默认解析结果：把载荷原样返回，业务在 on_packet 里自行处理"""
        info = self.extract_device_info(packet)
        return {
            "device_id": info["device_id"],
            "device_type": info["device_type"],
            "msg_id": info["msg_id"],
            "payload_len": len(packet) - self.header_len,
        }


# ----------------------------------------------------------------------
# 参考实现：一个完整可跑的示例协议（新增项目时照这个改）
# ----------------------------------------------------------------------
@dataclass
class DemoFrameSpec(FrameSpec):
    """
    示例协议（不要直接用在生产上，仅作为「怎么配 FrameSpec」的参考）：
      包头(12) = 帧头(2) | 载荷长度(2,大端) | BCC(1) | 版本(1) | 设备ID(4) | 设备类型(1) | 报文ID(1)
    """
    header: bytes = b"\xa0\xa1"
    header_len: int = 12
    length_offset: int = 2
    length_size: int = 2
    checksum_offset: int = 4
    checksum_size: int = 1
    checksum_start: int = 0
    checksum_end: int = 0  # 0 = 校验到载荷末尾
    device_id_offset: int = 6
    device_id_size: int = 4
    device_type_offset: int = 10
    device_type_size: int = 1
    msg_id_offset: int = 11
    msg_id_size: int = 1


class DemoProtocol(LengthPrefixedProtocol):
    """
    示例协议实现：演示如何在通用拆包之上补 BCC 校验和业务解析。

    用法见 readme.md「如何接入自己的协议」。
    """

    #: 报文ID → 说明
    DEFAULT_MSG_TYPES = {
        0x01: "定位/上报（设备主动发起）",
        0x10: "参数查询（平台主动发起）",
        0x20: "参数设置（平台主动发起）",
        0x21: "系统复位（平台主动发起）",
    }

    def __init__(self, spec: Optional[DemoFrameSpec] = None):
        super().__init__(spec or DemoFrameSpec(), self.DEFAULT_MSG_TYPES)

    def verify(self, packet: bytes) -> bool:
        """异或（BCC）校验：校验字节 = 除校验位外所有字节逐字节异或"""
        offset = self.spec.checksum_offset
        expect = packet[offset]
        bcc = 0
        for idx, b in enumerate(packet):
            if idx == offset:
                continue
            bcc ^= b
        return bcc == expect

    def parse(self, packet: bytes) -> Optional[Dict]:
        info = self.extract_device_info(packet)
        payload = packet[self.header_len:]
        return {
            "device_id": info["device_id"],
            "device_type": info["device_type"],
            "msg_id": info["msg_id"],
            "msg_type_desc": self.msg_types.get(info["msg_id"], "未知报文"),
            "payload_len": len(payload),
            "payload_hex": payload.hex().upper(),
        }

    def build(self, msg_id: int, payload: bytes = b"", device_id: int = 0,
              device_type: int = 0, version: int = 1) -> bytes:
        """组下行报文"""
        header = bytearray()
        header += self.spec.header
        header += struct.pack(">H", len(payload))
        header += b"\x00"  # 校验位占位
        header += bytes([version])
        header += struct.pack(">I", device_id)
        header += bytes([device_type])
        header += bytes([msg_id])

        packet = bytes(header) + payload
        bcc = 0
        for b in packet:
            bcc ^= b
        # 把校验值写回校验位
        packet = packet[:self.spec.checksum_offset] + bytes([bcc]) + packet[self.spec.checksum_offset + 1:]
        return packet
