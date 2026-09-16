# -*- coding: utf-8 -*-
"""
Stage E+：一键部署 v2 —— 40 服务器部署 + 可迁移镜像导出

能力（在 deploy_to_40.py 之上扩展）：
  1) SSH 连 192.168.3.40:22 root/qwer1234
  2) 探测远端环境（docker / df / 已有项目）
  3) git clone 远端仓库到 /opt/vgis_django（已存在则 git pull）
  4) 构建 Docker 镜像：vgis-django:v1.0
  5) docker save 导出可迁移 tar（800MB-1.2GB）
  6) 在 deploy/ 下生成 .env（DB/Redis/ES/GIS_* 配置）
  7) cd deploy && docker compose up -d
  8) 验证 health / info / login 三个端点
  9) 镜像可迁移性证明：cp 到 /tmp + docker load + tag 校验

调用：
  python deploy/deploy_v2.py
  python deploy/deploy_v2.py --skip-build  # 仅重启容器
  python deploy/deploy_v2.py --no-pull     # 跳过 git pull
  python deploy/deploy_v2.py --no-save     # 不导出 tar
"""
from __future__ import unicode_literals

import argparse
import os
import sys
import time

# ---------- SSH 连接参数 ----------
SSH_HOST = "192.168.3.40"
SSH_PORT = 22
SSH_USER = "root"
SSH_PASSWORD = "qwer1234"

# ---------- 远端部署路径（注意：远端是 Linux，必须用 POSIX 路径，不能用 os.path.join）----------
REMOTE_ROOT = "/opt/vgis_django"
REMOTE_REPO = "https://gitee.com/gisfanmachel/vgis_django_service.git"
REMOTE_COMPOSE_DIR = REMOTE_ROOT + "/deploy"

# ---------- 镜像 ----------
IMAGE_TAG = "vgis-django:v1.0"
IMAGE_TAR_NAME = "vgis-django-v1.0.tar"
REMOTE_IMAGE_TAR = REMOTE_ROOT + "/" + IMAGE_TAR_NAME


def _ssh_exec(client, cmd, timeout=900, hide=False):
    """在远端跑一条命令并实时打印 stdout/stderr；返回 (rc, stdout, stderr)"""
    if not hide:
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
            if not hide:
                sys.stdout.write(chunk.decode("utf-8", "replace"))
                sys.stdout.flush()
        if chan.recv_stderr_ready():
            chunk = chan.recv_stderr(4096)
            if chunk:
                err += chunk
                if not hide:
                    sys.stderr.write(chunk.decode("utf-8", "replace"))
                    sys.stderr.flush()
        if chan.exit_status_ready():
            break
        time.sleep(0.1)
    rc = chan.recv_exit_status()
    chan.close()
    return rc, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def _probe_remote(client):
    """探测远端环境：docker / 现有容器 / /opt 目录 / 磁盘"""
    print("\n" + "=" * 70)
    print("# 阶段 1：探测远端 40 服务器环境")
    print("=" * 70)
    probes = [
        ("docker --version", "Docker 版本"),
        ("docker ps --format 'table {{.Names}}\\t{{.Status}}'", "现有容器"),
        ("ls -la /opt", "/opt 目录"),
        ("df -h /", "磁盘空间"),
        ("free -h", "内存"),
        ("nproc", "CPU 核数"),
        ("cat /etc/os-release | head -5", "操作系统"),
    ]
    for cmd, desc in probes:
        print("\n--- {} ---".format(desc))
        _ssh_exec(client, cmd, timeout=30)


def _ensure_repo(client, no_pull=False):
    """git clone 或 pull"""
    print("\n" + "=" * 70)
    print("# 阶段 2：同步远端仓库到 {}".format(REMOTE_ROOT))
    print("=" * 70)

    rc, out, _ = _ssh_exec(client, "test -d {}/.git && echo EXISTS || echo MISSING".format(REMOTE_ROOT),
                           timeout=15)
    if "EXISTS" in out:
        if no_pull:
            print("# 已存在且 --no-pull，跳过 git pull")
            return
        print("# 已存在仓库，执行 git pull")
        _ssh_exec(client,
                  "cd {} && "
                  "git fetch --all && "
                  "git reset --hard origin/master".format(REMOTE_ROOT),
                  timeout=120)
    else:
        print("# 仓库不存在，开始 git clone")
        # 先创建父目录
        _ssh_exec(client, "mkdir -p {}".format(REMOTE_ROOT), timeout=10)
        # clone 到 REMOTE_ROOT 目录
        _ssh_exec(client,
                  "git clone {} {}".format(REMOTE_REPO, REMOTE_ROOT),
                  timeout=600)


def _write_remote_env(client):
    """在 deploy/ 下生成 .env（DB / Redis / ES / GIS_*）"""
    print("\n" + "=" * 70)
    print("# 阶段 3：在远端 deploy/ 下写 .env")
    print("=" * 70)

    env_content = """# Stage E+ 部署 .env（由 deploy_v2.py 自动生成于 {}）
# 数据库（直连物理 40 PG 容器 12326）
DB_DEFAULT_HOST=192.168.3.40
DB_DEFAULT_PORT=12326
DB_DEFAULT_NAME=mydb_test
DB_DEFAULT_USER=postgres
DB_DEFAULT_PASSWORD=postgres
DB_REPLICA_ENABLED=false
PGBOUNCER_ENABLED=false

# Redis（容器内 redis service）
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PROTOCOL=2
REDIS_DB_CACHE=0
REDIS_DB_CHANNEL=1
REDIS_DB_CELERY=2

# ES
ES_ENABLED=true
ES_HOSTS=http://192.168.3.40:9200
ES_USER=elastic
ES_PASSWORD=VgisES@2026!

# GIS 工作目录（容器内 /mnt/data；40 服务器需挂载或创建）
GIS_WORK_DIR=/mnt/data/cog_publish
GIS_SSH_HOST=192.168.3.40
GIS_SSH_PORT=22
GIS_SSH_USER=root
GIS_SSH_PASSWORD=qwer1234
""".format(time.strftime("%Y-%m-%d %H:%M:%S"))

    # 用 heredoc 写文件（注意远端是 Linux，路径必须 POSIX）
    write_cmd = "cat > {}/.env <<'VGIS_ENV_EOF'\n{}VGIS_ENV_EOF\n".format(
        REMOTE_COMPOSE_DIR, env_content)
    rc, _, err = _ssh_exec(client, write_cmd, timeout=15)
    if rc != 0:
        print("# .env 写入失败：", err)
        sys.exit(5)
    print("# .env 写入成功：{}/.env".format(REMOTE_COMPOSE_DIR))


def _build_image(client, skip_build=False):
    """docker build 构建镜像（预计 3-5 分钟）"""
    print("\n" + "=" * 70)
    print("# 阶段 4：构建镜像 {}".format(IMAGE_TAG))
    print("=" * 70)
    if skip_build:
        print("# --skip-build 跳过构建")
        return

    build_cmd = (
        "cd {} && "
        "docker build -t {} -f my_project/Dockerfile my_project/ "
        "2>&1 | tee /tmp/docker_build.log".format(REMOTE_ROOT, IMAGE_TAG)
    )
    t0 = time.time()
    rc, _, err = _ssh_exec(client, build_cmd, timeout=1800)
    elapsed = time.time() - t0
    if rc != 0:
        print("# 构建失败 rc={} err={}".format(rc, err))
        sys.exit(6)
    print("# 构建完成，耗时 {:.1f}s".format(elapsed))

    # 看一下镜像大小
    _ssh_exec(client,
              "docker images {} --format 'table {{{{.Repository}}}}\\t{{{{.Tag}}}}\\t{{{{.Size}}}}'".format(
                  IMAGE_TAG), timeout=15)


def _save_image(client, no_save=False):
    """docker save 导出 tar（预计 800MB-1.2GB）"""
    print("\n" + "=" * 70)
    print("# 阶段 5：导出可迁移 tar")
    print("=" * 70)
    if no_save:
        print("# --no-save 跳过 save")
        return

    save_cmd = "docker save -o {} {}".format(REMOTE_IMAGE_TAR, IMAGE_TAG)
    t0 = time.time()
    rc, _, err = _ssh_exec(client, save_cmd, timeout=600)
    elapsed = time.time() - t0
    if rc != 0:
        print("# save 失败 rc={} err={}".format(rc, err))
        sys.exit(7)
    print("# save 完成，耗时 {:.1f}s".format(elapsed))

    # 看大小
    _ssh_exec(client, "ls -lh {} && du -h {}".format(REMOTE_IMAGE_TAR, REMOTE_IMAGE_TAR), timeout=10)


def _compose_up(client, skip_compose=False):
    """cd deploy && docker compose up -d"""
    print("\n" + "=" * 70)
    print("# 阶段 6：docker compose up -d")
    print("=" * 70)
    if skip_compose:
        print("# --skip-compose 跳过")
        return

    up_cmd = "cd {} && docker compose up -d 2>&1 | tee /tmp/docker_compose.log".format(REMOTE_COMPOSE_DIR)
    t0 = time.time()
    rc, _, err = _ssh_exec(client, up_cmd, timeout=600)
    elapsed = time.time() - t0
    if rc != 0:
        print("# compose up 失败 rc={} err={}".format(rc, err))
        sys.exit(8)
    print("# compose up 完成，耗时 {:.1f}s".format(elapsed))

    # 等 5 秒再 ps
    time.sleep(5)
    _ssh_exec(client,
              "cd {} && docker compose ps".format(REMOTE_COMPOSE_DIR),
              timeout=30)


def _verify_health(client):
    """验证 health / info / login 三个端点（远端 curl）"""
    print("\n" + "=" * 70)
    print("# 阶段 7：远端 curl 验证")
    print("=" * 70)

    probes = [
        # nginx 反代 8080
        ("curl -s -o /dev/null -w 'nginx_8080_http_code=%{http_code}\\n' "
         "http://127.0.0.1:8080/my_api/gis/health/", "nginx 8080 health"),
        # web 直连 10846
        ("curl -s -o /dev/null -w 'web_10846_http_code=%{http_code}\\n' "
         "http://127.0.0.1:10846/my_api/gis/health/", "web 10846 health"),
        # login
        ("curl -sk -X POST http://127.0.0.1:10846/my_api/userman/user/loginWithForce/ "
         "-H 'Content-Type: application/json' "
         "-d '{\"username\":\"admin\",\"password\":\"Test@12345\","
         "\"client_time\":1789443257484,\"client_other_time\":1651766400000}' "
         "| head -c 300", "login 接口"),
    ]
    for cmd, desc in probes:
        print("\n--- {} ---".format(desc))
        _ssh_exec(client, cmd, timeout=30)


def _verify_migration(client):
    """镜像可迁移性证明：cp 到 /tmp + docker load + tag 校验"""
    print("\n" + "=" * 70)
    print("# 阶段 8：镜像可迁移性测试")
    print("=" * 70)

    steps = [
        ("cp {} /tmp/ && ls -lh /tmp/{}".format(REMOTE_IMAGE_TAR, IMAGE_TAR_NAME),
         "cp 到 /tmp"),
        ("docker load -i /tmp/{}".format(IMAGE_TAR_NAME), "docker load"),
        ("docker images | grep vgis-django", "tag 校验"),
    ]
    for cmd, desc in steps:
        print("\n--- {} ---".format(desc))
        rc, _, err = _ssh_exec(client, cmd, timeout=300)
        if rc != 0:
            print("# 失败：", err)


def _stats(client):
    """容器资源占用"""
    print("\n" + "=" * 70)
    print("# 阶段 9：容器资源统计")
    print("=" * 70)
    _ssh_exec(client,
              "docker stats --no-stream --format "
              "'table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.MemPerc}}\\t{{.NetIO}}\\t{{.BlockIO}}'",
              timeout=15)
    _ssh_exec(client,
              "cd {} && docker compose logs --no-color web 2>&1 | tail -30".format(REMOTE_COMPOSE_DIR),
              timeout=15)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default=SSH_HOST)
    p.add_argument("--port", type=int, default=SSH_PORT)
    p.add_argument("--user", default=SSH_USER)
    p.add_argument("--password", default=SSH_PASSWORD)
    p.add_argument("--skip-probe", action="store_true", help="跳过远端环境探测")
    p.add_argument("--no-pull", action="store_true", help="跳过 git pull")
    p.add_argument("--skip-build", action="store_true", help="跳过 docker build")
    p.add_argument("--no-save", action="store_true", help="跳过 docker save")
    p.add_argument("--skip-compose", action="store_true", help="跳过 docker compose up")
    args = p.parse_args()

    try:
        import paramiko
    except ImportError:
        print("# paramiko 未装；pip install paramiko")
        sys.exit(1)

    print("# 连 {}@{}:{}".format(args.user, args.host, args.port))
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(args.host, port=args.port, username=args.user,
                   password=args.password, timeout=15)

    try:
        if not args.skip_probe:
            _probe_remote(client)
        _ensure_repo(client, no_pull=args.no_pull)
        _write_remote_env(client)
        _build_image(client, skip_build=args.skip_build)
        _save_image(client, no_save=args.no_save)
        _compose_up(client, skip_compose=args.skip_compose)
        _verify_health(client)
        _verify_migration(client)
        _stats(client)
    finally:
        client.close()

    print("\n" + "=" * 70)
    print("# 部署全流程完成")
    print("=" * 70)
    print("# 镜像位置：{}".format(REMOTE_IMAGE_TAR))
    print("# compose 目录：{}".format(REMOTE_COMPOSE_DIR))


if __name__ == "__main__":
    main()