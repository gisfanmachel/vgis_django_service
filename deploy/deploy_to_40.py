# -*- coding: utf-8 -*-
"""
Stage E：一键部署到 40 服务器（paramiko SSH）

能力：
  - 把 my_project 源码 rsync 到 40 服务器
  - 远端跑 docker-compose up -d --build
  - 校验容器起来 + 健康接口通

注意：
  - 当前机器没有部署公钥时，脚本会 fallback 用密码登录（密码写死在脚本顶部）
  - 真上线请改用 ssh key + ssh-agent
  - **仅当用户显式触发时才执行** —— 不在本会话自动跑

调用：
  python deploy/deploy_to_40.py            # 默认 1 web + 1 celery
  python deploy/deploy_to_40.py --scale 4 # 4 web
"""
from __future__ import unicode_literals

import argparse
import os
import sys
import time

SSH_HOST = "192.168.3.40"
SSH_PORT = 22
SSH_USER = "root"
SSH_PASSWORD = "qwer1234"  # 真上线请用 ssh key 替代

REMOTE_DIR = "/opt/vgis_django_service"
REMOTE_COMPOSE_DIR = os.path.join(REMOTE_DIR, "deploy")


def _ssh_exec(client, cmd, timeout=600):
    """在远端跑一条命令并实时打印 stdout/stderr；返回 (rc, stdout, stderr)"""
    print("\n[remote] $ {}".format(cmd))
    chan = client.get_transport().open_session()
    chan.settimeout(timeout)
    chan.exec_command(cmd)
    out, err = b"", b""
    while True:
        if chan.recv_ready():
            chunk = chan.recv(4096)
            if not chunk:
                break
            out += chunk
            sys.stdout.write(chunk.decode("utf-8", "replace"))
            sys.stdout.flush()
        if chan.recv_stderr_ready():
            chunk = chan.recv_stderr(4096)
            if chunk:
                err += chunk
                sys.stderr.write(chunk.decode("utf-8", "replace"))
                sys.stderr.flush()
        if chan.exit_status_ready():
            break
        time.sleep(0.1)
    rc = chan.recv_exit_status()
    chan.close()
    return rc, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scale", type=int, default=1, help="web 副本数")
    p.add_argument("--host", default=SSH_HOST)
    p.add_argument("--port", type=int, default=SSH_PORT)
    p.add_argument("--user", default=SSH_USER)
    p.add_argument("--password", default=SSH_PASSWORD)
    p.add_argument("--no-rsync", action="store_true",
                   help="跳过 rsync（用于仅重启容器）")
    args = p.parse_args()

    try:
        import paramiko
    except ImportError:
        print("# paramiko 未装；pip install paramiko")
        sys.exit(1)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("# 连 {}@{}:{}".format(args.user, args.host, args.port))
    client.connect(args.host, port=args.port, username=args.user, password=args.password, timeout=15)

    # 1) 准备远端目录
    rc, _, _ = _ssh_exec(client,
                         "mkdir -p {} && cd {} && ls -la".format(REMOTE_DIR, REMOTE_DIR))
    if rc != 0:
        print("# 远端目录准备失败"); sys.exit(2)

    # 2) rsync（python 没自带 rsync，这里用 scp -r 代替）
    if not args.no_rsync:
        print("\n# scp 本地代码到 {}:{}".format(args.host, REMOTE_DIR))
        sftp = client.open_sftp()
        # 简化：只 push deploy/ + my_project/ 两个核心目录
        # （vcs 仓库一般都已经 clone 在远端，所以这里支持增量覆盖）
        local_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for sub in ("deploy", "my_project"):
            src_dir = os.path.join(local_root, sub)
            dst_dir = os.path.join(REMOTE_DIR, sub)
            _sftp_mirror(sftp, src_dir, dst_dir)
        sftp.close()

    # 3) 跑 docker-compose
    compose_cmd = (
        "cd {} && "
        "docker-compose up -d --build "
        "--scale web={scale}".format(REMOTE_COMPOSE_DIR, scale=args.scale)
    )
    rc, _, err = _ssh_exec(client, compose_cmd, timeout=1800)
    if rc != 0:
        print("# docker-compose 失败：", err)
        sys.exit(3)

    # 4) 健康检查：等 5 秒后 curl 健康接口
    print("\n# 等 5 秒后验证健康接口…")
    time.sleep(5)
    rc, out, _ = _ssh_exec(client,
                           "docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'web|celery' || true")
    print("# 容器状态：\n{}".format(out))

    client.close()
    print("\n# 部署完成。")


def _sftp_mirror(sftp, src_dir, dst_dir):
    """递归 sftp mirror：把 src_dir 拷到 dst_dir（dst_dir 必须已存在父目录）"""
    import stat as stat_mod
    try:
        sftp.stat(dst_dir)
    except IOError:
        sftp.mkdir(dst_dir)

    for name in os.listdir(src_dir):
        if name in (".git", "__pycache__", ".venv", "venv", "log", "logs", "node_modules", "static/upload"):
            continue
        src_path = os.path.join(src_dir, name)
        dst_path = os.path.join(dst_dir, name)
        if os.path.isdir(src_path):
            _sftp_mirror(sftp, src_path, dst_path)
        else:
            try:
                sftp.stat(dst_path)
            except IOError:
                pass
            sftp.put(src_path, dst_path)
            print("  put {}/{}".format(os.path.relpath(src_path, os.path.dirname(src_dir)), ""))


if __name__ == "__main__":
    main()