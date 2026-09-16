# Stage E：VGIS Django 框架 Docker 镜像
#
# 说明：
#   - 基于 python:3.12-slim，与 venv_6.06 (Python 3.12.14) 对齐
#   - libpq5（PG 客户端）/ libgdal32 / libgeos / libproj（CGO 依赖）由 apt 装
#   - gunicorn 23.0.0（与 venv_6.06 内的版本对齐）
#   - 默认监听 10846（与当前 waitress 端口一致，便于切换验证）
#
# 构建：
#   cd my_project
#   docker build -t vgis-django:stage-e .
#
# 运行（环境变量驱动；DB/Redis/ES 由 config.py 读 ENV）：
#   docker run -p 10846:10846 \
#     -e DB_DEFAULT_HOST=192.168.3.40 -e DB_DEFAULT_PORT=12326 \
#     -e REDIS_HOST=192.168.3.80 \
#     -e ES_HOSTS=http://192.168.3.40:9200 \
#     vgis-django:stage-e
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=my_project.settings

WORKDIR /app

# 系统依赖：libpq5（PG）/ libgdal36 / libgeos-c1t64 / libproj25 / proj-bin / gdal-bin / gdal-data
# 注：python:3.12-slim 当前基 Debian 13 trixie，GDAL/GEOS/PROJ 包名与 bookworm 不同
#     - bookworm: libgdal32 / libgeos-c1v5
#     - trixie  : libgdal36 / libgeos-c1t64
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libgdal36 \
        libgeos-c1t64 \
        libproj25 \
        proj-bin \
        gdal-bin \
        gdal-data \
        curl \
    && rm -rf /var/lib/apt/lists/*

# 先 copy requirements 单独装，Docker 层缓存友好
COPY requirements.txt /app/requirements.txt

# 拆 3 步装的理由：vgis-office==1.1.8 的元数据 Requires-Dist 里写了 fitz，
# 但 PyPI 的 fitz 已被官方 deprecate（"Package 'fitz' has been deactivated and cannot be installed.
# Please install 'pymupdf' instead."），直接 -r 安装会挂。
# 解法：先装除 vgis-office 之外的全部依赖 + pymupdf（提供 fitz shim 兼容层），
#      最后用 --no-deps 单独装 vgis-office（它的真依赖已经在上一步装好）。
# 注意：grep 要同时过滤掉注释行（#）和空行，否则 # ---- xxx ---- 会被当成 pip 参数，
#      而 `pip install -- xxx` 会报 "no such option: ----"。
RUN pip install --no-cache-dir \
        gunicorn==23.0.0 \
        pymupdf==1.28.2 \
        $(grep -vE '^(#|$|vgis-office)' /app/requirements.txt)
RUN pip install --no-cache-dir --no-deps vgis-office==1.1.8

# 再 copy 源码
COPY . /app

# 容器内 GDAL 数据目录（debian 13 trixie：gdal-data 包路径 /usr/share/gdal，proj-bin 包路径 /usr/share/proj）
ENV GDAL_DATA=/usr/share/gdal \
    PROJ_LIB=/usr/share/proj \
    GDAL_SKIP=DRIVER_OGR_GRASS

EXPOSE 10846

# 健康检查：每 30s 调一次 /my_api/gis/health/；失败 3 次标记 unhealthy
# -k 允许 curl 跳过自签证书 / 5xx；-f 仅 HTTP<400 算成功
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fk http://127.0.0.1:10846/my_api/gis/health/ || exit 1

# 默认用 gunicorn 起 4 worker / 16 thread；与 run.py threads 16 一致
CMD ["gunicorn", "my_project.wsgi:application", \
     "--bind", "0.0.0.0:10846", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "16", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]