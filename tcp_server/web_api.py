#!/usr/bin/python3.9
# -*- coding: utf-8 -*-
# @Descr   : TCP 服务的 Web 控制/监控接口（Flask）
#
#            框架只提供「通用运维接口」：服务器状态、连接列表、日志查看下载、
#            文件上传、向连接/设备发送数据、广播。
#            业务指令（参数查询、系统复位、固件升级…）通过指令注册表挂进来：
#
#                from web_api import register_command
#
#                @register_command("system_reset")
#                def handle_system_reset(server, payload):
#                    device_id = payload.get("device_id")
#                    # ... 组装下行报文并发送
#                    return {"success": True, "info": "复位指令已下发"}
#
#            前端统一调用 POST /command/<name>，请求体 JSON 原样传给 handler。
# @Software: PyCharm
import logging
import os

from flask import Flask, jsonify, request, send_file

import config
from commonUtility import CommonHelper
from logger_setup import LOG_DIR

logger = logging.getLogger(__name__)

# 业务指令注册表：name -> handler(server, payload) -> dict
COMMAND_REGISTRY = {}


def register_command(name):
    """指令注册装饰器"""
    def decorator(func):
        COMMAND_REGISTRY[name] = func
        return func
    return decorator


def create_web_app(server):
    """创建并返回绑定到给定 TCPServer 实例的 Flask app"""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    CommonHelper.ensure_dir(config.UPLOAD_FOLDER)

    # ------------------------------------------------------------------
    # 通用运维接口
    # ------------------------------------------------------------------
    @app.route("/server_status", methods=["GET"])
    def server_status():
        """服务器运行状态 + 统计 + 连接列表"""
        status = server.get_status()
        status.pop("connections", None)  # 连接明细走 /connections，避免响应过大
        return jsonify({"success": True, "info": status})

    @app.route("/connections", methods=["GET"])
    def connections():
        """当前所有连接明细"""
        with server.connections_lock:
            data = [c.to_dict() for c in server.connections.values()]
        return jsonify({"success": True, "total": len(data), "info": data})

    @app.route("/protocol/msg_types", methods=["GET"])
    def protocol_msg_types():
        """当前协议支持的报文类型（ProtocolHandler.msg_types）"""
        msg_types = getattr(server.protocol, "msg_types", {}) or {}
        data = [{"msg_id": k, "desc": v} for k, v in sorted(msg_types.items())]
        return jsonify({"success": True, "info": data})

    @app.route("/log_info", methods=["GET"])
    def log_info():
        """日志文件列表（名称/大小/修改时间）"""
        try:
            files = []
            for name in sorted(os.listdir(LOG_DIR)):
                path = os.path.join(LOG_DIR, name)
                if not os.path.isfile(path):
                    continue
                stat = os.stat(path)
                files.append({
                    "filename": name,
                    "size": stat.st_size,
                    "size_readable": CommonHelper.format_file_size(stat.st_size),
                    "modified": CommonHelper.get_curent_time_str(),
                })
            return jsonify({"success": True, "info": files})
        except Exception as e:
            logger.error("读取日志目录失败: %s", e)
            msg = CommonHelper.get_local_str("GET_DATA_FAIL", request)
            return jsonify({"success": False, "info": msg}), 500

    @app.route("/download_log/<path:filename>", methods=["GET"])
    def download_log(filename):
        """下载指定日志文件（限制在 LOG_DIR 内，防目录穿越）"""
        safe_name = os.path.basename(filename)
        path = os.path.join(LOG_DIR, safe_name)
        if not os.path.isfile(path):
            msg = CommonHelper.get_local_str("LOG_FILE_NOT_EXIST", request)
            return jsonify({"success": False, "info": msg}), 404
        return send_file(path, as_attachment=True, download_name=safe_name)

    @app.route("/upload", methods=["POST"])
    def upload_file():
        """上传文件（默认只允许 config.ALLOWED_EXTENSIONS，用于固件 bin 等）"""
        if "file" not in request.files:
            msg = CommonHelper.get_local_str4("REQUEST_PARAMETER_DOES_NOT_HAVE_FILE_OBJECT", request)
            return jsonify({"success": False, "info": msg}), 400

        file = request.files["file"]
        if not file or file.filename == "":
            msg = CommonHelper.get_local_str4("NO_FILE_SELECTED_FOR_UPLOAD", request)
            return jsonify({"success": False, "info": msg}), 400

        if not CommonHelper.allowed_upload_file(file.filename):
            msg = CommonHelper.get_local_str4("FILE_TYPE_NOT_ALLOWED", request)
            return jsonify({"success": False, "info": msg}), 400

        try:
            save_path = os.path.join(config.UPLOAD_FOLDER, os.path.basename(file.filename))
            file.save(save_path)
            hex_str, byte_count = CommonHelper.bin_to_hex_and_count(save_path)
            logger.info("文件上传成功: %s，%s 字节", save_path, byte_count)
            msg = CommonHelper.get_local_str4("FILE_UPLOAD_SUCCESS", request)
            return jsonify({
                "success": True,
                "info": msg,
                "filename": os.path.basename(save_path),
                "path": save_path,
                "size": byte_count,
                "size_readable": CommonHelper.format_file_size(byte_count),
                "hex": hex_str,
            })
        except Exception as e:
            logger.error("文件上传失败: %s", e, exc_info=True)
            msg = CommonHelper.get_local_str4("FILE_UPLOAD_FAILED", request)
            return jsonify({"success": False, "info": "{}: {}".format(msg, e)}), 500

    # ------------------------------------------------------------------
    # 下行发送
    # ------------------------------------------------------------------
    @app.route("/send", methods=["POST"])
    def send_to_target():
        """
        向指定连接或设备发送数据。请求体：
            {"client_id": "1.2.3.4:5678", "hex": "A0A1..."}
            或 {"device_id": 123, "hex": "A0A1..."}
        """
        data = request.get_json(silent=True) or {}
        hex_str = data.get("hex")
        if not hex_str:
            msg = CommonHelper.get_local_str3("MISSING_REQUIRED_FIELD", request)
            return jsonify({"success": False, "info": "{}: hex".format(msg)}), 400

        try:
            raw = bytes.fromhex(hex_str)
        except ValueError:
            msg = CommonHelper.get_local_str3("INVALID_JSON_FORMAT", request)
            return jsonify({"success": False, "info": "{}: hex".format(msg)}), 400

        if data.get("client_id"):
            ok = server.send_to_client(data["client_id"], raw)
        elif data.get("device_id") is not None:
            ok = server.send_to_device(data["device_id"], raw)
        else:
            msg = CommonHelper.get_local_str3("MISSING_REQUIRED_FIELD", request)
            return jsonify({"success": False, "info": "{}: client_id/device_id".format(msg)}), 400

        if ok:
            msg = CommonHelper.get_local_str3("SEND_MESSAGE_SUCCESS", request)
            return jsonify({"success": True, "info": msg})
        msg = CommonHelper.get_local_str3("DEVICE_NOT_CONNECTED", request)
        return jsonify({"success": False, "info": msg}), 404

    @app.route("/broadcast", methods=["POST"])
    def broadcast():
        """向所有已连接客户端广播。请求体：{"hex": "A0A1..."}"""
        data = request.get_json(silent=True) or {}
        hex_str = data.get("hex")
        if not hex_str:
            msg = CommonHelper.get_local_str3("MISSING_REQUIRED_FIELD", request)
            return jsonify({"success": False, "info": "{}: hex".format(msg)}), 400
        try:
            raw = bytes.fromhex(hex_str)
        except ValueError:
            msg = CommonHelper.get_local_str3("INVALID_JSON_FORMAT", request)
            return jsonify({"success": False, "info": "{}: hex".format(msg)}), 400

        ok_count = server.broadcast_to_all(raw)
        msg = CommonHelper.get_local_str3("SEND_MESSAGE_SUCCESS", request)
        return jsonify({"success": True, "info": msg, "sent_count": ok_count})

    # ------------------------------------------------------------------
    # 业务指令下发（注册表驱动）
    # ------------------------------------------------------------------
    @app.route("/commands", methods=["GET"])
    def list_commands():
        """列出已注册的业务指令名"""
        return jsonify({"success": True, "info": sorted(COMMAND_REGISTRY.keys())})

    @app.route("/command/<name>", methods=["POST"])
    def run_command(name):
        """执行已注册的业务指令，请求体 JSON 原样传给 handler"""
        handler = COMMAND_REGISTRY.get(name)
        if handler is None:
            msg = CommonHelper.get_local_str3("COMMAND_NOT_SUPPORTED", request)
            return jsonify({"success": False, "info": "{}: {}".format(msg, name)}), 404

        payload = request.get_json(silent=True) or {}
        try:
            result = handler(server, payload)
            return jsonify(result if isinstance(result, dict) else {"success": True, "info": result})
        except Exception as e:
            logger.error("执行指令 %s 失败: %s", name, e, exc_info=True)
            msg = CommonHelper.get_local_str3("COMMAND_EXECUTE_FAILED", request)
            return jsonify({"success": False, "info": "{}: {}".format(msg, e)}), 500

    return app
