# -*- coding: utf-8 -*-
# gis_service 模块的工具类：GISHelper
#
# 封装：
#   - SSH 客户端（paramiko，复用 stac_demo/ssh40.py 的模式）
#   - MinIO 上传（通过一次性 mc 容器）
#   - TiTiler 反代
#   - Step 计时器（publish_pmtiles.py / publish_cog.py 都用了同样的模式）
import logging
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger("django")


class Step:
    """步骤计时器（与原 publish_pmtiles.py / publish_cog.py 完全等价）。

    用法：
        with Step("读取 GeoJSON", on_step=lambda name: task.current_step = name):
            ...
    on_step 回调在进入步骤时触发，便于把 current_step 写回 tt_gis_task。
    """

    def __init__(self, name, on_step=None):
        self.name = name
        self.on_step = on_step
        self.t0 = None

    def __enter__(self):
        logger.info("[Step] %s 开始", self.name)
        if self.on_step:
            try:
                self.on_step(self.name)
            except Exception:  # 回调失败不应阻塞主流程
                logger.exception("Step.on_step 回调失败：%s", self.name)
        self.t0 = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        dt = time.time() - (self.t0 or time.time())
        logger.info("[Step] %s 完成 耗时 %.2fs", self.name, dt)
        return False  # 不吞异常


class GISHelper:
    """GIS 模块的客户端封装。
    设计为 stateless 工具类：方法都是 static，不需要持有任何资源。
    跨方法共享的状态走 my_project.settings（GIS_* 段）。
    """

    # =========================================================================
    # SSH（paramiko）
    # =========================================================================
    @staticmethod
    def ssh(host=None, port=None, user=None, password=None, timeout=15):
        """拿一个 SSHClient。
        调用方负责 close()。用法：
            cli = GISHelper.ssh()
            try:
                sftp = cli.open_sftp()
                sftp.put(local, remote)
            finally:
                cli.close()
        """
        # 延后 import：paramiko 不在 HTTP 路径必须，Celery worker 路径才用得到
        import paramiko

        from my_project import settings

        cli = paramiko.SSHClient()
        cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cli.connect(
            host or settings.GIS_SSH_HOST,
            port=port or settings.GIS_SSH_PORT,
            username=user or settings.GIS_SSH_USER,
            password=password or settings.GIS_SSH_PASSWORD,
            timeout=timeout,
        )
        return cli

    @staticmethod
    def ssh_run(cmd, timeout=600, host=None, port=None, user=None, password=None):
        """在 SSH 端跑一条命令，返回 (rc, out, err)。

        用 subprocess 在宿主机直跑的情况（这是 worker 跑在 40 上时），
        也可以走系统 ssh；为简化统一走 paramiko。
        """
        cli = GISHelper.ssh(host, port, user, password, timeout=timeout)
        try:
            stdin, stdout, stderr = cli.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode("utf-8", "replace")
            err = stderr.read().decode("utf-8", "replace")
            rc = stdout.channel.recv_exit_status()
            return rc, out, err
        finally:
            cli.close()

    @staticmethod
    def ssh_upload(local, remote, host=None, port=None, user=None, password=None):
        """SFTP 上传文件。返回 True/False。"""
        cli = GISHelper.ssh(host, port, user, password)
        try:
            sftp = cli.open_sftp()
            sftp.put(local, remote)
            sftp.close()
            return True
        finally:
            cli.close()

    # =========================================================================
    # MinIO（通过一次性 mc 容器上传，与原 publish_cog.py L67-77 一致）
    # =========================================================================
    @staticmethod
    def upload_to_minio(local_path, bucket, key):
        """把 local_path（容器/worker 本地路径）通过 mc 上传到 MinIO。

        走一次性 mc 容器（minio/minio:latest），自带 mc 客户端，
        用完即销毁。返回值是 (True, "OK") / (False, "原因")。
        注意：local_path 必须是 mc 容器能看到的路径，
        因此本机 worker 调用本接口时要把文件先放到挂载点（如 /mnt/data）下。
        """
        from my_project import settings

        MINIO_IMAGE = "minio/minio:latest"
        ALIAS = "pub"
        script = (
            "mc alias set {a} {ep} {u} {p} >/dev/null 2>&1; "
            "mc cp --quiet /{lp} {a}/{b}/{k} && "
            "mc anonymous set download {a}/{b}/{k} >/dev/null 2>&1 && echo UPLOAD_OK".format(
                a=ALIAS,
                ep=settings.GIS_MINIO_ENDPOINT,
                u=settings.GIS_MINIO_USER,
                p=settings.GIS_MINIO_PASSWORD,
                lp=os.path.relpath(local_path, "/").lstrip("/")
                   if local_path.startswith("/") else local_path,
                b=bucket,
                k=key,
            )
        )
        cmd = ["docker", "run", "--rm", "--network", "host",
               "-v", "/mnt/data:/mnt/data",
               "--entrypoint", "sh", MINIO_IMAGE, "-c", script]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if p.returncode != 0:
                logger.error("mc upload failed: %s", p.stderr[-1500:])
                return False, p.stderr or "mc exited non-zero"
            return "UPLOAD_OK" in (p.stdout or ""), p.stdout
        except Exception as e:
            logger.exception("upload_to_minio 异常：%s", e)
            return False, str(e)

    # =========================================================================
    # TiTiler 反代（COG 动态瓦片）
    # =========================================================================
    @staticmethod
    def call_titiler(z, x, y, asset_url, bands=None, stretch=None,
                     media_type="image/png", timeout=30):
        """直接走 TiTiler 取瓦片字节。返回 (status, content_type, bytes)。

        不做缓存、不做重试；上层 view 负责把 (status, content_type, bytes) 透回客户端。
        stretch：dict {band(int): (low, high)}；按波段重复拼 rescale 参数。
        """
        from my_project import settings

        # url 参数必须先 encode
        qs = "url=" + urllib.parse.quote(asset_url, safe="")
        if bands:
            qs += "&" + "&".join("bidx={}".format(int(b)) for b in bands)
        if stretch:
            rescale_parts = []
            for b in (bands or sorted(stretch.keys())):
                lo, hi = stretch.get(b, (0, 1))
                rescale_parts.append("rescale={:.4f},{:.4f}".format(lo, hi))
            qs += "&" + "&".join(rescale_parts)

        url = "{}/cog/tiles/WebMercatorQuad/{}/{}/{}.{}?{}".format(
            settings.GIS_TITILER_URL.rstrip("/"), z, x, y, "png", qs)

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.headers.get("Content-Type", media_type), r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Content-Type", media_type) if e.headers else media_type, \
                   (e.read() if e.fp else b"")
        except Exception as e:
            logger.exception("call_titiler 异常：%s", e)
            return 0, "text/plain", str(e).encode()

    # =========================================================================
    # 通用 HTTP 健康探针（health / info 共用）
    # =========================================================================
    @staticmethod
    def http_probe(url, timeout=5):
        """HTTP GET 探活，返回 (ok, status, elapsed_seconds, body_bytes)。"""
        t0 = time.time()
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                body = r.read()
                return True, r.status, time.time() - t0, len(body)
        except urllib.error.HTTPError as e:
            return False, e.code, time.time() - t0, len(e.read() or b"")
        except Exception:
            return False, 0, time.time() - t0, 0

    @staticmethod
    def pg_probe(dsn, timeout=5):
        """PostgreSQL 探活，返回 (ok, version_or_err)。"""
        try:
            import psycopg2
            conn = psycopg2.connect(dsn, connect_timeout=timeout)
            cur = conn.cursor()
            cur.execute("SELECT version()")
            v = cur.fetchone()[0]
            conn.close()
            return True, v[:80]
        except Exception as e:
            return False, str(e)[:200]