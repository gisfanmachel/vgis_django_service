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

# 系统依赖：libpq5（PG）/ libgdal32 / libgeos-c1v5 / libproj25 / proj-bin（GDAL 数据）
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libgdal32 \
        libgeos-c1v5 \
        libproj25 \
        proj-bin \
        curl \
    && rm -rf /var/lib/apt/lists/*

# 先 copy requirements 单独装，Docker 层缓存友好
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir gunicorn==23.0.0 -r /app/requirements.txt

# 再 copy 源码
COPY . /app

# 容器内 GDAL 数据目录（debian 包一般在 /usr/share/gdal /usr/share/proj）
ENV GDAL_DATA=/usr/share/gdal \
    PROJ_LIB=/usr/share/proj \
    GDAL_SKIP=DRIVER_OGR_GRASS

EXPOSE 10846

# 默认用 gunicorn 起 4 worker / 16 thread；与 run.py threads 16 一致
CMD ["gunicorn", "my_project.wsgi:application", \
     "--bind", "0.0.0.0:10846", \
     "--workers", "4", \
     "--worker-class", "gthread", \
     "--threads", "16", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]