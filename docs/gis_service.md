# GIS Service 模块说明

> 状态：v1.0（2026-09-15）
> 前缀：`/my_api/gis/`
> 模块位置：`my_project/my_app/module/gis_service/`

## 设计目标

把 `E:\workbuddy\2026-09-07-14-57-30\stac_demo` 里散落的 4 个 CLI 工具
（PostGIS MVT / PMTiles / COG / STAC ingest）封装为统一 Django REST API，
与框架的 token 鉴权 / 统一响应 / Celery 异步等机制集成。

| 原 CLI              | 迁移后             | 异步？ |
|---------------------|--------------------|--------|
| `load_vector_pg.py` | `POST /vector/load/` | 否（同步） |
| `mvt_server.py`     | `GET /mvt/...`    | 否（HTTP 直查） |
| `publish_pmtiles.py`| `POST /pmtiles/publish/` | 是（Celery） |
| `publish_cog.py`    | `POST /cog/publish/` | 是（Celery） |
| `ingest_stac.py`    | `POST /stac/ingest/` | 是（Celery） |

## 架构概览

```
                            ┌─────────────────┐
                            │  浏览器 / 前端   │
                            └────────┬────────┘
                                     │  HTTP /my_api/gis/*
                                     ▼
                            ┌─────────────────┐
                            │  Django waitress │ ← 同步路径
                            │   (10846)        │   - vector load / tables / drop / columns
                            │                  │   - MVT tiles / table info
                            │                  │   - cog tiles（反代 TiTiler）
                            │                  │   - health / info
                            └────────┬─────────┘
                                     │ Celery .delay()
                                     ▼
                            ┌─────────────────┐
                            │  Celery worker   │ ← 异步路径（40 服务器上跑）
                            │  on 192.168.3.40 │   - publish_pmtiles_task
                            │                  │   - publish_cog_task
                            └────────┬─────────┘
                                     │ SSH / docker run mc
                                     ▼
                            ┌─────────────────┐
                            │  外部依赖        │
                            │  - MYDB.PostGIS  │ ← Django 直查
                            │  - TiTiler       │ ← COG 瓦片反代
                            │  - MinIO         │ ← COG / PMTiles asset
                            │  - pgSTAC        │ ← STAC item/collection
                            └─────────────────┘
```

## 依赖（已在 venv_6.06 实测可装）

```
shapely>=2.0.0
mercantile>=1.2.0
mapbox-vector-tile>=2.0.0   # 强制 protobuf<7（pip 安装时被拉 6.33.6）
pmtiles>=3.0.0
rasterio>=1.3.0
numpy>=1.24.0
```

注意 `mapbox-vector-tile` 与 vgis-utils 共用 protobuf，需留意版本锁。

## 配置（env-driven，全在 `my_project/config.py` 的 GIS_* 段）

| 变量 | 默认值 | 说明 |
|---|---|---|
| `GIS_SSH_HOST` | `192.168.3.40` | Celery worker SSH 目标 |
| `GIS_SSH_PORT` | `22` | |
| `GIS_SSH_USER` | `root` | |
| `GIS_SSH_PASSWORD` | `qwer1234` | |
| `GIS_MINIO_ENDPOINT` | `http://192.168.3.40:9000` | |
| `GIS_MINIO_USER` | `minioadmin` | |
| `GIS_MINIO_PASSWORD` | `minioadmin123` | |
| `GIS_MINIO_BUCKET` | `stac-demo` | |
| `GIS_TITILER_URL` | `http://192.168.3.40:8001` | |
| `GIS_PGSTAC_DSN` | `postgresql://pgstac:pgstac123@192.168.3.40:5433/pgstac` | |
| `GIS_NGINX_HOST` | `192.168.3.40` | |
| `GIS_NGINX_PORT` | `8080` | |
| `GIS_WORK_DIR` | `/mnt/data/cog_publish` | Celery worker 端的工作目录 |

## 数据库表

执行 `my_project/database/GIS_TABLES_2026_09.sql` 在 mydb_test 上：

```sql
CREATE TABLE tt_gis_task  -- Celery 异步任务状态
CREATE TABLE tt_gis_layer -- vector 表注册
```

3 个高频索引（task_type / status / create_time DESC）。

## REST API 一览

所有路径都在 `/my_api/gis/` 前缀下；鉴权走 `ExpiringTokenAuthentication`。

### Vector 灌库 / 列表

| 方法 | URL | 用途 |
|---|---|---|
| POST | `/vector/load/` | GeoJSON 灌入 + 建 GIST 索引（同步，因文件小） |
| GET | `/vector/tables/` | 列出 vector 表（要素数、bbox、列数） |
| DELETE | `/vector/tables/{table}/` | 删表（需 `X-Confirm: true` header） |
| GET | `/vector/tables/{table}/columns/` | 列出非几何列 |

### MVT（动态瓦片）

| 方法 | URL | 用途 |
|---|---|---|
| GET | `/mvt/{table}/info/` | 表信息 + bbox + 字段 |
| GET | `/mvt/{table}/{z}/{x}/{y}.pbf` | 动态 MVT 瓦片（`application/vnd.mapbox-vector-tile`） |

MVT SQL 与原 `mvt_server.py` 一致：低层级（z<14）做
`ST_SimplifyPreserveTopology(ST_Transform(geom, 3857), tolerance)`，
高层级直接 `ST_Transform(geom, 3857)`。

### PMTiles（异步发布）

| 方法 | URL | 用途 |
|---|---|---|
| POST | `/pmtiles/publish/` | 异步 Celery，返回 `task_id` |
| GET | `/pmtiles/tasks/{task_id}/` | 任务状态（pmtiles 类型） |
| GET | `/pmtiles/list/?limit=N` | 已发布列表（pmtiles） |

### COG（异步发布）

| 方法 | URL | 用途 |
|---|---|---|
| POST | `/cog/publish/` | 异步 Celery，返回 `task_id` |
| GET | `/cog/tasks/{task_id}/` | 任务状态（cog 类型） |
| GET | `/cog/list/?limit=N` | 已发布列表（cog） |
| GET | `/cog/tiles/{z}/{x}/{y}.png` | 反代 TiTiler，取最近一次 success cog 的瓦片 |

### STAC ingest

| 方法 | URL | 用途 |
|---|---|---|
| POST | `/stac/ingest/` | 异步 pypgstac load（collections + items） |

入参支持两种格式：
- `collections` / `items` 直接喂 list[dict]（view 层落盘 ndjson）
- `collections_ndjson` / `items_ndjson` 喂 worker 已有的文件路径

### 统一任务 / 健康

| 方法 | URL | 用途 |
|---|---|---|
| GET | `/tasks/{task_id}/` | 任意 task_type 的统一查询 |
| GET | `/tasks/list/?type=pmtiles\|cog\|stac&status=running&limit=N` | 统一列表 |
| GET | `/health/` | TiTiler / MinIO / pgSTAC / 主库连通 |
| GET | `/info/` | 服务信息 + 外部依赖 URL + 端点 |

## 用法示例

```bash
# 登录拿 token
TOKEN=$(curl -sk -X POST http://127.0.0.1:10846/my_api/userman/user/loginWithForce/ \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"Test@12345","client_time":1789443257484,"client_other_time":1651766400000}' \
    | python -c "import sys,json; print(json.load(sys.stdin)['token'])")

# 1) 灌 vector
curl -sk -X POST -H "Authorization: Token $TOKEN" \
    -F "src=@buildings.geojson" -F "table=test_buildings" \
    http://127.0.0.1:10846/my_api/gis/vector/load/

# 2) 取 MVT 瓦片（z=10, x=853, y=445）
curl -sk -H "Authorization: Token $TOKEN" -o tile.pbf \
    http://127.0.0.1:10846/my_api/gis/mvt/test_buildings/10/853/445.pbf

# 3) 异步发布 PMTiles
TASK=$(curl -sk -X POST -H "Authorization: Token $TOKEN" \
    -F "src=@buildings.geojson" -F "layer=buildings" -F "minzoom=5" -F "maxzoom=14" \
    http://127.0.0.1:10846/my_api/gis/pmtiles/publish/ \
    | python -c "import sys,json; print(json.load(sys.stdin)['obj']['task_id'])")

# 4) 查任务状态
curl -sk -H "Authorization: Token $TOKEN" \
    http://127.0.0.1:10846/my_api/gis/tasks/$TASK/

# 5) 健康
curl -sk -H "Authorization: Token $TOKEN" \
    http://127.0.0.1:10846/my_api/gis/health/
```

## 已知遗留 / 注意事项

1. **Celery worker 必须在 40 服务器跑** —— `upload_to_minio` 走 `docker run mc + /mnt/data` 挂载，
   本机（Windows）无法执行重活，HTTP 派发后 worker 会失败。
2. **pmtiles.cog publish 实际未端到端跑通** —— 缺 Celery worker + 缺 pypgstac；
   当前只在 HTTP 路径验证了派发与状态查询。
3. **cog/tiles 反代** —— 当前从最近一次 success 的 cog 取参数；如果没有任何
   success 的 cog，端点会返回 `"no published COG asset available"`。
4. **gdalinfo/gdalwarp/gdal_translate** 在 worker 路径通过 SSH 调用，
   worker 端需先装好 GDAL + miniforge python。

## 已知坑

- DRF `request.data` 在 multipart 时已经是 dict，但里面**不含**文件；
  文件在 `request.FILES`。本模块严格遵守这个区分。
- Django URL 顺序：`tasks/list/` 必须在 `tasks/{task_id}/` 之前，
  否则 list 会被当成 task_id。已在 urls.py 注释说明。
- mapbox-vector-tile 强制 protobuf<7，会卸载已装的 7.36 → 装 6.33.6。
  如果项目其它地方强依赖 protobuf 7，需另做版本兼容。