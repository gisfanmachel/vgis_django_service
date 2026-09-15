"""
my_project 配置中心（Stage A）

设计原则：
  - 所有可调参数都通过同名环境变量覆盖，便于容器化部署（改 env 不用改代码）。
  - 任何开关/特性默认关闭（DB_REPLICA_ENABLED / PGBOUNCER_ENABLED），
    不设置时完全沿用旧行为，零回归风险。
  - 复用了 tcp_server/config.py 的 _env 模式，保证全仓风格一致。

参见 plan: C:\\Users\\Administrator\\.claude\\plans\\vivid-rolling-cat.md § SpringBoot 对齐方案 / Stage A。
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(key, default, cast=str):
    """读环境变量并转换类型，未设置或转换失败时回落到默认值"""
    val = os.environ.get(key)
    if val is None or str(val).strip() == "":
        return default
    try:
        return cast(val)
    except (TypeError, ValueError):
        return default


def _env_bool(key, default):
    """布尔开关：1/true/yes/on 视为 True，其它视为 False（大小写不敏感）"""
    val = _env(key, "")
    if val == "":
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# 数据库（主库）
# ---------------------------------------------------------------------------
DB_DEFAULT_NAME = _env("DB_DEFAULT_NAME", "mydb_test")
DB_DEFAULT_USER = _env("DB_DEFAULT_USER", "postgres")
DB_DEFAULT_PASSWORD = _env("DB_DEFAULT_PASSWORD", "postgres")
DB_DEFAULT_HOST = _env("DB_DEFAULT_HOST", "192.168.3.40")
DB_DEFAULT_PORT = _env("DB_DEFAULT_PORT", "12326", int)

# 连接硬化（PostgreSQL libpq 选项）
DB_CONNECT_TIMEOUT = _env("DB_CONNECT_TIMEOUT", "10", int)
DB_KEEPALIVES_IDLE = _env("DB_KEEPALIVES_IDLE", "30", int)
DB_KEEPALIVES_INTERVAL = _env("DB_KEEPALIVES_INTERVAL", "10", int)
DB_KEEPALIVES_COUNT = _env("DB_KEEPALIVES_COUNT", "5", int)
# 连接池：60 秒保留 + 健康检查
DB_CONN_MAX_AGE = _env("DB_CONN_MAX_AGE", "60", int)

# ---------------------------------------------------------------------------
# 数据库（读副本，默认关闭）
# ---------------------------------------------------------------------------
# 当 DB_REPLICA_ENABLED=true 时，DATABASES 中会多一个 'replica' alias，
# 由 db_router.py 把 db_for_read 路由过去（写仍走 default）。
DB_REPLICA_ENABLED = _env_bool("DB_REPLICA_ENABLED", False)
DB_REPLICA_NAME = _env("DB_REPLICA_NAME", "mydb_test")
DB_REPLICA_USER = _env("DB_REPLICA_USER", "readonly_user")
DB_REPLICA_PASSWORD = _env("DB_REPLICA_PASSWORD", "")
DB_REPLICA_HOST = _env("DB_REPLICA_HOST", "192.168.3.40")
DB_REPLICA_PORT = _env("DB_REPLICA_PORT", "12326", int)

# ---------------------------------------------------------------------------
# pgbouncer（默认关闭）
# ---------------------------------------------------------------------------
# 当 PGBOUNCER_ENABLED=true 时，所有 alias 的 HOST/PORT 都改写为 pgbouncer 监听地址。
# 注意 pgbouncer 模式下 CONN_MAX_AGE 必须为 0（pgbouncer 自己管池），
# 但本项目 pg 端是直接连接，所以默认行为下不需要改。
PGBOUNCER_ENABLED = _env_bool("PGBOUNCER_ENABLED", False)
PGBOUNCER_HOST = _env("PGBOUNCER_HOST", "127.0.0.1")
PGBOUNCER_PORT = _env("PGBOUNCER_PORT", "6432", int)

# ---------------------------------------------------------------------------
# Redis（缓存 / 通道层 / Celery broker 统一一台物理机，按 DB 隔离）
# ---------------------------------------------------------------------------
REDIS_HOST = _env("REDIS_HOST", "192.168.3.80")
REDIS_PORT = _env("REDIS_PORT", "6379", int)
REDIS_PASSWORD = _env("REDIS_PASSWORD", None)
REDIS_DB_CACHE = _env("REDIS_DB_CACHE", "0", int)
REDIS_DB_CHANNEL = _env("REDIS_DB_CHANNEL", "1", int)
REDIS_DB_CELERY = _env("REDIS_DB_CELERY", "2", int)
# 该服务器 Redis 5.x 不支持 HELLO，强制 RESP2。
REDIS_PROTOCOL = _env("REDIS_PROTOCOL", "2", int)

# ---------------------------------------------------------------------------
# Elasticsearch（异步日志）
# ---------------------------------------------------------------------------
ES_ENABLED = _env_bool("ES_ENABLED", True)
ES_HOSTS = _env("ES_HOSTS", "http://192.168.3.40:9200").split(",")
ES_USER = _env("ES_USER", "elastic")
ES_PASSWORD = _env("ES_PASSWORD", "VgisES@2026!")
ES_INDEX_PREFIX = _env("ES_INDEX_PREFIX", "vgis-myapp")
ES_FLUSH_INTERVAL = _env("ES_FLUSH_INTERVAL", "1.0", float)
ES_BATCH_SIZE = _env("ES_BATCH_SIZE", "100", int)

# ---------------------------------------------------------------------------
# gis_service 模块（GIS vector / MVT / PMTiles / COG / STAC）
# ---------------------------------------------------------------------------
# 设计：
#   1) Vector 数据直接用上面的 DB_DEFAULT_*（MYDB.PostGIS），
#      不另开库；MVT 瓦片由 Django 直查渲染
#   2) 重型发布（PMTiles / COG / STAC ingest）走 Celery 异步，
#      见 my_app/module/gis_service/tasks.py
#   3) COG 瓦片反代 TiTiler；SSH/MinIO 只在 Celery worker 里用

# SSH 到 40 服务器（Celery worker 在 40 上跑时会用到）
GIS_SSH_HOST = _env("GIS_SSH_HOST", "192.168.3.40")
GIS_SSH_PORT = _env("GIS_SSH_PORT", "22", int)
GIS_SSH_USER = _env("GIS_SSH_USER", "root")
GIS_SSH_PASSWORD = _env("GIS_SSH_PASSWORD", "qwer1234")

# MinIO（pgSTAC asset / COG 实际存储）
GIS_MINIO_ENDPOINT = _env("GIS_MINIO_ENDPOINT", "http://192.168.3.40:9000")
GIS_MINIO_USER = _env("GIS_MINIO_USER", "minioadmin")
GIS_MINIO_PASSWORD = _env("GIS_MINIO_PASSWORD", "minioadmin123")
GIS_MINIO_BUCKET = _env("GIS_MINIO_BUCKET", "stac-demo")

# TiTiler（COG 动态瓦片）
GIS_TITILER_URL = _env("GIS_TITILER_URL", "http://192.168.3.40:8001")

# pgSTAC（STAC 元数据）
GIS_PGSTAC_DSN = _env(
    "GIS_PGSTAC_DSN", "postgresql://pgstac:pgstac123@192.168.3.40:5433/pgstac")

# Nginx（静态资源 / 反代：192.168.3.40:8080/vector/*、/imagery/*）
GIS_NGINX_HOST = _env("GIS_NGINX_HOST", "192.168.3.40")
GIS_NGINX_PORT = _env("GIS_NGINX_PORT", "8080", int)

# Celery worker 跑在 40 上，写的是 SSH 端路径
GIS_WORK_DIR = _env("GIS_WORK_DIR", "/mnt/data/cog_publish")