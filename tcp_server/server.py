#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : 通用 TCP 长连接服务器骨架
#
#            框架负责：连接生命周期、每连接独立收包线程、粘包/半包拆包、
#                     数据包队列 + 线程池消费、连接监控与超时清理、
#                     自动重连、日志轮转与清理、优雅关停。
#            业务只需：实现 ProtocolHandler（拆包/校验/解析）+ 一个 on_packet 回调。
#
#            示例：
#                from protocol import DemoProtocol
#                def on_packet(packet, conn_info, server):
#                    print(packet.device_id, packet.parsed)
#                server = TCPServer(protocol=DemoProtocol(), on_packet=on_packet)
#                server.start()
# @Software: PyCharm
import logging
import queue
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import config
from connection import ConnectionInfo, ConnectionStatus, Packet
from db_pool import PgConnectionPool
from logger_setup import cleanup_old_logs
from protocol import PassThroughProtocol

logger = logging.getLogger(__name__)


class TCPServer:
    """通用 TCP 长连接服务器"""

    def __init__(self, host=None, port=None, protocol=None,
                 on_packet=None,
                 on_client_connected=None,
                 on_client_disconnected=None,
                 enable_db=None,
                 enable_web_api=None,
                 name="TCPServer"):
        """
        :param host:            监听地址，默认取 config.TCP_SERVER_HOST
        :param port:            监听端口，默认取 config.TCP_SERVER_PORT
        :param protocol:        ProtocolHandler 实例，负责拆包/校验/解析
        :param on_packet:       业务处理回调 fn(packet: Packet, conn_info: ConnectionInfo, server) -> None
        :param on_client_connected:    连接建立回调 fn(conn_info, server)
        :param on_client_disconnected: 连接断开回调 fn(conn_info, server)
        :param enable_db:       是否启用数据库连接池，默认取 config.DB_ENABLED
        :param enable_web_api:  是否启用 Flask 控制/监控接口，默认取 config.WEB_API_ENABLED
        """
        self.name = name
        self.host = host or config.TCP_SERVER_HOST
        self.port = port or config.TCP_SERVER_PORT
        self.protocol = protocol or PassThroughProtocol()
        self.on_packet = on_packet
        self.on_client_connected = on_client_connected
        self.on_client_disconnected = on_client_disconnected
        self.enable_web_api = config.WEB_API_ENABLED if enable_web_api is None else enable_web_api

        # --- 连接管理 ---
        self.connections = {}  # client_id -> ConnectionInfo
        self.connections_lock = threading.RLock()

        # --- 运行状态 ---
        self.server_socket = None
        self.running = threading.Event()
        self.monitor_running = threading.Event()
        self.started_at = None

        # --- 数据包处理 ---
        self.packet_queue = queue.Queue(maxsize=config.MAX_PACKET_QUEUE_SIZE)
        self.packet_thread_pool = ThreadPoolExecutor(
            max_workers=config.THREAD_POOL_SIZE,
            thread_name_prefix="PacketProcessor",
        )
        self._consumer_threads = []

        # --- 监控线程 ---
        self.monitor_thread = None
        self.log_monitor_thread = None

        # --- 统计 ---
        self.stats = {
            "total_connections": 0,  # 累计接受的连接数
            "total_packets": 0,  # 累计收到的完整报文数
            "total_parse_failed": 0,  # 累计解析/校验失败数
            "total_bytes_received": 0,
        }

        # --- 数据库连接池 ---
        self.db_pool = None
        if enable_db is None:
            enable_db = config.DB_ENABLED
        if enable_db:
            self.db_pool = PgConnectionPool()

        logger.info("%s 初始化 - 主机: %s, 端口: %s, 协议: %s",
                    name, self.host, self.port, type(self.protocol).__name__)

    # ==================================================================
    # 生命周期
    # ==================================================================
    def start(self):
        """启动服务器（阻塞运行，直到 stop() 被调用或进程退出）"""
        self._prepare_socket()
        self.running.set()
        self.monitor_running.set()
        self.started_at = datetime.now()

        cleanup_old_logs()
        self._start_monitor_thread()
        self._start_log_monitor_thread()
        self._start_packet_consumers()

        if self.enable_web_api:
            self._start_web_api()

        logger.info("%s 已启动，开始接收客户端连接...", self.name)
        try:
            self._accept_loop()
        except KeyboardInterrupt:
            logger.info("收到中断信号，准备停止 %s", self.name)
        finally:
            self.stop()

    def _prepare_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, config.RECV_BUFFER_SIZE)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(config.TCP_CLIENT_MAX_NUMBERS)
        # 非阻塞 accept，配合下面的短休眠实现可控的关闭
        self.server_socket.setblocking(False)
        logger.info("%s 监听 %s:%s，最大连接数 %s", self.name, self.host, self.port,
                    config.TCP_CLIENT_MAX_NUMBERS)

    def _accept_loop(self):
        while self.running.is_set():
            try:
                client_socket, client_address = self.server_socket.accept()
            except BlockingIOError:
                time.sleep(0.001)  # 无新连接，短暂让出 CPU
                continue
            except OSError:
                # server socket 已被 stop() 关闭
                break
            except Exception as e:
                logger.error("接受连接时发生错误: %s", e)
                time.sleep(1)
                continue

            try:
                self._tune_client_socket(client_socket)
                logger.info("新连接来自 %s:%s，当前时间 %s", client_address[0], client_address[1],
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self.start_client_handler(client_socket, client_address)
            except Exception as e:
                logger.error("处理新连接失败: %s", e)
                self._safe_close(client_socket)

    @staticmethod
    def _tune_client_socket(client_socket):
        """开启 TCP 保活，尽早发现对端掉线"""
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        for opt_name, opt_val in (
            ("TCP_KEEPIDLE", config.SOCKET_KEEPIDLE),
            ("TCP_KEEPINTVL", config.SOCKET_KEEPINTVL),
            ("TCP_KEEPCNT", config.SOCKET_KEEPCNT),
        ):
            opt = getattr(socket, opt_name, None)
            if opt is not None:
                try:
                    client_socket.setsockopt(socket.IPPROTO_TCP, opt, opt_val)
                except OSError:
                    pass

    def stop(self):
        """优雅停止：停线程 → 关连接 → 关线程池 → 关连接池 → 关监听"""
        if not self.running.is_set() and self.server_socket is None:
            return
        logger.info("正在停止 %s ...", self.name)
        self.running.clear()
        self.monitor_running.clear()

        # 1. 关闭监听 socket，让 accept 循环退出
        self._safe_close(self.server_socket)
        self.server_socket = None

        # 2. 等待监控线程退出
        for thread in (self.monitor_thread, self.log_monitor_thread):
            if thread and thread.is_alive():
                thread.join(timeout=5)

        # 3. 关闭所有客户端连接
        with self.connections_lock:
            for client_id, conn_info in list(self.connections.items()):
                self._safe_close(conn_info.socket)
            self.connections.clear()

        # 4. 通知队列消费线程退出
        for _ in self._consumer_threads:
            try:
                self.packet_queue.put_nowait(None)
            except queue.Full:
                pass
        for thread in self._consumer_threads:
            if thread.is_alive():
                thread.join(timeout=5)
        self._consumer_threads = []

        # 5. 关闭线程池与数据库连接池
        if self.packet_thread_pool:
            self.packet_thread_pool.shutdown(wait=True)
        if self.db_pool:
            self.db_pool.close_all()

        logger.info("%s 已完全停止", self.name)

    @staticmethod
    def _safe_close(sock):
        if sock is None:
            return
        try:
            sock.close()
        except Exception:
            pass

    # ==================================================================
    # 客户端连接处理
    # ==================================================================
    def start_client_handler(self, client_socket, client_address):
        """登记连接并启动独立的收包线程"""
        conn_info = ConnectionInfo(
            socket=client_socket,
            address=client_address,
            connect_time=datetime.now(),
            status=ConnectionStatus.CONNECTED,
        )
        with self.connections_lock:
            self.connections[conn_info.client_id] = conn_info
        self.stats["total_connections"] += 1

        thread = threading.Thread(
            target=self.handle_client,
            args=(client_socket, client_address),
            name="ClientHandler-{}".format(conn_info.client_id),
            daemon=True,
        )
        conn_info.thread = thread
        thread.start()

        if self.on_client_connected:
            try:
                self.on_client_connected(conn_info, self)
            except Exception as e:
                logger.error("on_client_connected 回调异常: %s", e)

    def handle_client(self, client_socket, client_address):
        """单个客户端的收包循环：累积 buffer → 拆包 → 入队"""
        client_id = "{}:{}".format(client_address[0], client_address[1])
        buffer = b""
        normal_close = False

        try:
            while self.running.is_set():
                try:
                    client_socket.settimeout(config.RECV_TIMEOUT_SECONDS)
                    data = client_socket.recv(config.REC_MAX_BYTES)
                except socket.timeout:
                    continue  # 收包超时不代表断开，继续等
                except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
                    logger.warning("连接异常中断 %s: %s", client_address, e)
                    break

                if not data:
                    logger.info("连接正常断开: %s", client_address)
                    normal_close = True
                    break

                with self.connections_lock:
                    conn_info = self.connections.get(client_id)
                    if conn_info:
                        conn_info.touch()
                        conn_info.total_bytes_received += len(data)
                self.stats["total_bytes_received"] += len(data)

                buffer += data
                buffer = self.process_received_data(buffer, client_address, client_socket)

        except Exception as e:
            logger.error("处理客户端 %s 时发生错误: %s", client_address, e, exc_info=True)
        finally:
            self._on_client_thread_exit(client_id, client_address, normal_close)

    def _on_client_thread_exit(self, client_id, client_address, normal_close):
        """收包线程退出：正常断开直接清理，异常断开标记为 DISCONNECTED 交给监控线程重连"""
        conn_info = None
        with self.connections_lock:
            conn_info = self.connections.get(client_id)

        if conn_info is None:
            return

        if normal_close:
            self.cleanup_connection(client_id)
        else:
            # 异常断开：先标记，由监控线程按 MAX_RECONNECT_ATTEMPTS 决定重连还是清理
            conn_info.status = ConnectionStatus.DISCONNECTED
            logger.info("客户端 %s 异常断开，进入重连流程", client_address)

        if self.on_client_disconnected:
            try:
                self.on_client_disconnected(conn_info, self)
            except Exception as e:
                logger.error("on_client_disconnected 回调异常: %s", e)

    def process_received_data(self, buffer, client_address, client_socket):
        """
        从缓冲区拆出完整报文并入队，返回剩余（不足一包的）缓冲区。

        拆包逻辑在 ProtocolHandler.split_packets() 里，这里只管派发。
        """
        packets, remain = self.protocol.split_packets(buffer)
        for raw in packets:
            self.enqueue_packet(raw, client_address, client_socket)
        return remain

    def enqueue_packet(self, raw, client_address, client_socket):
        """把完整报文放入处理队列，超过上限时丢弃最旧的包并告警"""
        try:
            self.packet_queue.put_nowait((raw, client_address, client_socket))
        except queue.Full:
            logger.error("数据包队列已满（上限 %s），丢弃报文", config.MAX_PACKET_QUEUE_SIZE)

    # ==================================================================
    # 数据包消费
    # ==================================================================
    def _start_packet_consumers(self):
        for i in range(config.DATA_PROCESSOR_THREADS):
            thread = threading.Thread(
                target=self.consume_packet_queue,
                name="PacketConsumer-{}".format(i + 1),
                daemon=True,
            )
            thread.start()
            self._consumer_threads.append(thread)
        logger.info("已启动 %s 个数据包消费线程，线程池大小 %s",
                    config.DATA_PROCESSOR_THREADS, config.THREAD_POOL_SIZE)

    def consume_packet_queue(self):
        """从队列取包，交给线程池处理"""
        while True:
            try:
                item = self.packet_queue.get(timeout=1.0)
            except queue.Empty:
                if not self.running.is_set():
                    break
                continue

            if item is None:  # 退出信号
                self.packet_queue.task_done()
                break

            try:
                self.packet_thread_pool.submit(self.process_packet, *item)
            except RuntimeError:
                # 线程池已关闭
                break
            finally:
                self.packet_queue.task_done()

    def process_packet(self, raw, client_address, client_socket):
        """校验 + 解析 + 交给业务回调"""
        self.stats["total_packets"] += 1
        client_id = "{}:{}".format(client_address[0], client_address[1])

        # 1. 校验
        try:
            if not self.protocol.verify(raw):
                self.stats["total_parse_failed"] += 1
                logger.warning("报文校验失败，已丢弃 - 来自 %s，原始报文: %s", client_id, raw.hex().upper())
                return
        except Exception as e:
            self.stats["total_parse_failed"] += 1
            logger.error("报文校验异常，已丢弃 - 来自 %s: %s", client_id, e)
            return

        # 2. 解析
        try:
            parsed = self.protocol.parse(raw)
        except Exception as e:
            self.stats["total_parse_failed"] += 1
            logger.error("报文解析失败 - 来自 %s: %s", client_id, e, exc_info=True)
            return

        # 3. 组装 Packet，并回填连接上的设备标识
        try:
            info = self.protocol.extract_device_info(raw)
        except Exception:
            info = {}
        packet = Packet(
            raw=raw,
            address=client_address,
            device_id=info.get("device_id"),
            device_type=info.get("device_type"),
            msg_id=info.get("msg_id"),
            payload=raw[self.protocol.header_len:] if self.protocol.header_len else b"",
            parsed=parsed,
        )

        with self.connections_lock:
            conn_info = self.connections.get(client_id)
            if conn_info and packet.device_id is not None:
                conn_info.device_id = packet.device_id

        self.log_packet(packet)

        # 4. 业务处理
        if self.on_packet:
            try:
                self.on_packet(packet, conn_info, self)
            except Exception as e:
                logger.error("on_packet 业务处理异常 - 设备 %s 报文 %s: %s",
                             packet.device_id, packet.msg_id, e, exc_info=True)

    def log_packet(self, packet):
        """记录报文日志（整包 hex 只在 DEBUG 级别输出，避免日志爆炸）"""
        logger.debug("收到报文 - 来自 %s，设备 %s，报文ID %s，长度 %s，内容: %s",
                     packet.client_id, packet.device_id, packet.msg_id, len(packet.raw),
                     packet.raw.hex().upper())

    # ==================================================================
    # 连接监控 / 重连 / 清理
    # ==================================================================
    def _start_monitor_thread(self):
        self.monitor_thread = threading.Thread(
            target=self.monitor_connections, name="ConnectionMonitor", daemon=True)
        self.monitor_thread.start()
        logger.info("连接监控线程已启动，检查间隔 %s 秒", config.MONITOR_INTERVAL_SECONDS)

    def monitor_connections(self):
        """周期性检查：超时 / 超长空闲 / 异常断开的连接"""
        while self.monitor_running.is_set():
            # 用 Event.wait 代替 sleep，stop() 时能立即退出
            if self.monitor_running.wait(config.MONITOR_INTERVAL_SECONDS):
                break
            try:
                to_cleanup = []
                with self.connections_lock:
                    for client_id, conn_info in list(self.connections.items()):
                        if conn_info.connection_seconds > config.MAX_CONNECTION_HOURS * 3600:
                            logger.warning("客户端 %s 连接时间超过 %s 小时，强制断开",
                                           client_id, config.MAX_CONNECTION_HOURS)
                            to_cleanup.append(client_id)
                            continue
                        if conn_info.idle_seconds > config.MAX_IDLE_SECONDS:
                            logger.warning("客户端 %s 空闲时间超过 %s 秒，强制断开",
                                           client_id, config.MAX_IDLE_SECONDS)
                            to_cleanup.append(client_id)
                            continue
                        if conn_info.status == ConnectionStatus.DISCONNECTED:
                            if conn_info.reconnect_count < config.MAX_RECONNECT_ATTEMPTS:
                                self.attempt_reconnect(client_id, conn_info)
                            else:
                                logger.warning("客户端 %s 重连次数超过限制，移除连接", client_id)
                                to_cleanup.append(client_id)

                for client_id in to_cleanup:
                    self.cleanup_connection(client_id)

                self.log_connection_stats()
            except Exception as e:
                logger.error("连接监控线程错误: %s", e, exc_info=True)

    def attempt_reconnect(self, client_id, conn_info):
        """尝试重连（针对异常断开的连接）"""
        try:
            conn_info.status = ConnectionStatus.RECONNECTING
            conn_info.reconnect_count += 1
            logger.info("尝试重连客户端 %s，第 %s 次", client_id, conn_info.reconnect_count)

            new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_socket.settimeout(config.RECONNECT_TIMEOUT)
            new_socket.connect(conn_info.address)

            self._safe_close(conn_info.socket)
            conn_info.socket = new_socket
            conn_info.status = ConnectionStatus.CONNECTED
            conn_info.touch()
            self._tune_client_socket(new_socket)
            logger.info("客户端 %s 重连成功", client_id)

            # 复用原有的 ConnectionInfo（保留 reconnect_count 等统计），
            # 不能走 start_client_handler，否则会用新的 ConnectionInfo 覆盖掉重连次数
            thread = threading.Thread(
                target=self.handle_client,
                args=(new_socket, conn_info.address),
                name="ClientHandler-{}".format(client_id),
                daemon=True,
            )
            conn_info.thread = thread
            thread.start()
        except Exception as e:
            logger.warning("客户端 %s 重连失败: %s", client_id, e)
            conn_info.status = ConnectionStatus.DISCONNECTED
            if conn_info.reconnect_count >= config.MAX_RECONNECT_ATTEMPTS:
                logger.warning("客户端 %s 重连次数已达上限，清理连接", client_id)
                self.cleanup_connection(client_id)

    def cleanup_connection(self, client_id):
        """关闭 socket 并移除连接记录"""
        with self.connections_lock:
            conn_info = self.connections.pop(client_id, None)
        if conn_info is None:
            return
        self._safe_close(conn_info.socket)
        logger.info("已清理客户端 %s 的连接资源", client_id)

    def log_connection_stats(self):
        """输出连接统计，每 30 分钟额外输出一次每连接明细"""
        with self.connections_lock:
            total = len(self.connections)
            if total == 0:
                return
            connected = sum(1 for c in self.connections.values()
                            if c.status == ConnectionStatus.CONNECTED)
            disconnected = total - connected
            logger.info("连接统计 - 总计: %s, 已连接: %s, 断开: %s", total, connected, disconnected)

            if datetime.now().minute % 30 == 0:
                for client_id, conn_info in self.connections.items():
                    logger.debug("客户端 %s: %s", client_id, conn_info.to_dict())

    # ==================================================================
    # 日志监控
    # ==================================================================
    def _start_log_monitor_thread(self):
        self.log_monitor_thread = threading.Thread(
            target=self.monitor_logs, name="LogMonitor", daemon=True)
        self.log_monitor_thread.start()

    def monitor_logs(self):
        """每小时清理一次超量日志备份"""
        while self.monitor_running.is_set():
            if self.monitor_running.wait(3600):
                break
            try:
                cleanup_old_logs()
            except Exception as e:
                logger.error("日志监控线程错误: %s", e)

    # ==================================================================
    # 对外发送
    # ==================================================================
    def send_to_client(self, client_id, data: bytes) -> bool:
        """按 client_id 向指定连接发送数据"""
        with self.connections_lock:
            conn_info = self.connections.get(client_id)
        if conn_info is None or conn_info.socket is None:
            logger.warning("发送失败，设备未连接: %s", client_id)
            return False
        return self._send(conn_info, data)

    def send_to_device(self, device_id, data: bytes) -> bool:
        """按设备ID向已登记该 device_id 的连接发送数据"""
        with self.connections_lock:
            targets = [c for c in self.connections.values()
                       if c.device_id is not None and str(c.device_id) == str(device_id)]
        if not targets:
            logger.warning("发送失败，设备未连接: %s", device_id)
            return False
        return self._send(targets[0], data)

    def broadcast_to_all(self, data: bytes) -> int:
        """向所有已连接客户端发送，返回成功数"""
        with self.connections_lock:
            targets = list(self.connections.values())
        ok = 0
        for conn_info in targets:
            if self._send(conn_info, data):
                ok += 1
        return ok

    @staticmethod
    def _send(conn_info, data: bytes) -> bool:
        try:
            conn_info.socket.sendall(data)
            conn_info.total_bytes_sent += len(data)
            conn_info.touch()
            return True
        except Exception as e:
            logger.error("发送数据失败 %s: %s", conn_info.client_id, e)
            return False

    # ==================================================================
    # 状态查询（供监控接口使用）
    # ==================================================================
    def get_status(self):
        with self.connections_lock:
            connections = [c.to_dict() for c in self.connections.values()]
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "protocol": type(self.protocol).__name__,
            "running": self.running.is_set(),
            "started_at": self.started_at.strftime("%Y-%m-%d %H:%M:%S") if self.started_at else None,
            "uptime_seconds": round((datetime.now() - self.started_at).total_seconds(), 1)
            if self.started_at else 0,
            "connection_count": len(connections),
            "queue_size": self.packet_queue.qsize(),
            "db_enabled": self.db_pool is not None,
            "stats": dict(self.stats),
            "connections": connections,
        }

    # ==================================================================
    # Web 控制接口
    # ==================================================================
    def _start_web_api(self):
        from web_api import create_web_app

        app = create_web_app(self)
        thread = threading.Thread(
            target=lambda: app.run(host=config.WEB_API_HOST, port=config.WEB_API_PORT,
                                   debug=config.WEB_API_DEBUG, use_reloader=False, threaded=True),
            name="WebAPI",
            daemon=True,
        )
        thread.start()
        logger.info("Web 控制接口已启动: http://%s:%s", config.WEB_API_HOST, config.WEB_API_PORT)
