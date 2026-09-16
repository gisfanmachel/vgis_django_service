# gis_service 模块说明

> Stage 6.1 模块：PostGIS MVT + PMTiles (vector / raster / terrain) + COG + STAC ingest
>
> 所有重型发布走 Celery 异步 worker（worker 须跑在 40 服务器，因为
> `GISHelper.upload_to_minio` 走 docker run mc + /mnt/data 挂载）。
> 本机（Windows）仅做 HTTP 派发；如需本机调试，可在请求里加 `run_inline=true` 跳过 Celery。

## 路由总览（前缀 `/my_api/gis/`）

| Method | Path                                | 说明                                        |
| ------ | ----------------------------------- | ------------------------------------------- |
| POST   | `/vector/load/`                     | GeoJSON 灌库 + 建 GIST 索引（同步）         |
| GET    | `/vector/tables/`                   | 列 vector 表                                |
| DELETE | `/vector/tables/{table}/`           | 删表（`X-Confirm: true` header 必带）       |
| GET    | `/vector/tables/{table}/columns/`   | 非几何列                                    |
| GET    | `/mvt/{table}/{z}/{x}/{y}.pbf`      | MVT 瓦片                                    |
| GET    | `/mvt/{table}/info/`                | 表信息                                      |
| POST   | `/pmtiles/publish/`                 | 异步发布 PMTiles（vector / raster / terrain） |
| GET    | `/pmtiles/tasks/{task_id}/`         | 任务状态                                    |
| GET    | `/pmtiles/list/`                    | 已发布列表                                  |
| POST   | `/cog/publish/`                     | 异步发布 COG                                |
| GET    | `/cog/tasks/{task_id}/`             | COG 任务状态                                |
| GET    | `/cog/tiles/{z}/{x}/{y}.png`        | TiTiler 反代瓦片                            |
| POST   | `/stac/ingest/`                     | ndjson → pgSTAC                             |
| GET    | `/tasks/{task_id}/`                 | 统一任务查询                                |
| GET    | `/tasks/list/`                      | 统一任务列表                                |
| GET    | `/health/`                          | TiTiler / MinIO / pgSTAC / 主库探活        |
| GET    | `/info/`                            | 服务信息                                    |

---

## PMTiles 发布（`POST /pmtiles/publish/`）

### 通用入参

| 字段           | 必填 | 默认值      | 说明                                            |
| -------------- | ---- | ----------- | ----------------------------------------------- |
| `src`          | 是   | —           | 源文件（multipart / file_id / 路径）            |
| `tile_type`    | 否   | `vector`    | `vector` / `raster` / `terrain`                 |
| `layer`        | 否   | src.stem    | 图层名                                          |
| `name`         | 否   | 同 layer    | 显示名（MBTiles metadata）                      |
| `minzoom`      | 否   | 5           | 起始 zoom                                       |
| `maxzoom`      | 否   | 14          | 终止 zoom                                       |
| `out`          | 否   | 自动        | 输出 .pmtiles 文件名                            |
| `run_inline`   | 否   | false       | true 时跳过 Celery，本机同步执行（仅本机测试）   |

### Vector 模式（`tile_type=vector`，默认值）

将 GeoJSON → MVT → MBTiles → PMTiles → MinIO；与 Stage 6.1 行为完全一致。

```bash
curl -X POST "http://127.0.0.1:10846/my_api/gis/pmtiles/publish/" \
  -H "Authorization: Token $TOKEN" \
  -F "src=@points.geojson" \
  -F "tile_type=vector" \
  -F "minzoom=5" -F "maxzoom=14" \
  -F "layer=points"
```

### Raster 模式（`tile_type=raster`）

将 TIFF 影像栅格 → 256×256 PNG 瓦片 → MBTiles → PMTiles → MinIO。

| 额外字段       | 默认值      | 说明                                                              |
| -------------- | ----------- | ----------------------------------------------------------------- |
| `tile_size`    | 256         | 瓦片边长像素                                                       |
| `resampling`   | bilinear    | nearest / bilinear / cubic / lanczos / average                    |
| `bands`        | 空          | 逗号分隔波段号；空 = 取前 3 波段（RGB）                            |

**坐标系处理**：源 raster 自动 reproject 到 EPSG:3857（Web Mercator）。

**数据类型**：
- `uint8` 直接写出（不拉伸）
- `uint16` → 拉伸到 0–255
- 浮点 → 按 2/98 百分位拉伸到 0–255（避免 PMTiles viewer 看起来一片黑/白）

**波段数**：
- 1 波段 → 灰度 PNG（`L` 模式）
- 2 波段 → 灰度 + Alpha（`LA` 模式）
- 3 波段 → RGB
- 4+ 波段 → RGB，第 4 波段作为 Alpha（RGBA）

```bash
curl -X POST "http://127.0.0.1:10846/my_api/gis/pmtiles/publish/" \
  -H "Authorization: Token $TOKEN" \
  -F "src=@test_rgb.tif" \
  -F "tile_type=raster" \
  -F "minzoom=5" -F "maxzoom=10" \
  -F "layer=test_rgb" \
  -F "tile_size=256"
```

前端消费：用 Mapbox GL / MapLibre / Leaflet 加载

```js
map.addSource('raster-src', {
  type: 'raster',
  url: 'pmtiles://https://minio.example.com/gis/raster/test_rgb_raster.pmtiles',
});
```

### Terrain 模式（`tile_type=terrain`）

将 DEM TIFF → quantized-mesh v1 → MBTiles → PMTiles → MinIO。

| 额外字段              | 默认值 | 说明                                       |
| --------------------- | ------ | ------------------------------------------ |
| `vertices_per_side`   | 65     | 顶点网格边长（默认 65 = 64 cells × 64 cells） |

**输入要求**：
- 单波段高程 TIFF（DEM）
- 坐标系自动 reproject 到 EPSG:4326（WGS84 Plate Carrée，quantized-mesh 硬要求）
- 必须有 nodata 标记或全有效像元

**quantized-mesh v1 格式**（big-endian，Cesium 标准）：
- Header (44 B): center(3 float32) + bbox(4 float32) + horizon(3 float32) + maxZoom(uint16)
- Vertex data: count(uint32) + count×3 uint16（X/Y/Z 量化到 [0, 32767]）
- Index data: count(uint32) + count×3 uint32（每 cell 两个三角形）
- Edge metadata flag (uint8 = 0，无扩展)

```bash
curl -X POST "http://127.0.0.1:10846/my_api/gis/pmtiles/publish/" \
  -H "Authorization: Token $TOKEN" \
  -F "src=@test_dem.tif" \
  -F "tile_type=terrain" \
  -F "minzoom=5" -F "maxzoom=10" \
  -F "layer=test_dem" \
  -F "vertices_per_side=65"
```

前端消费：用 CesiumJS

```js
import { Ion, Terrain } from 'cesium';
const terrain = new Terrain(
  'pmtiles://https://minio.example.com/gis/terrain/test_dem_terrain.pmtiles'
);
viewer.terrainProvider = terrain;
```

---

## 任务查询

```bash
# 查任务状态
curl -H "Authorization: Token $TOKEN" \
  "http://127.0.0.1:10846/my_api/gis/tasks/<celery_task_id>/"

# 列出所有 pmtiles 任务
curl -H "Authorization: Token $TOKEN" \
  "http://127.0.0.1:10846/my_api/gis/pmtiles/list/?limit=20"

# 按状态过滤
curl -H "Authorization: Token $TOKEN" \
  "http://127.0.0.1:10846/my_api/gis/tasks/list/?type=pmtiles&status=running"
```

返回结构：

```json
{
  "task_id": "abc-123-...",
  "task_type": "pmtiles",
  "status": "success | pending | running | failure",
  "current_step": "上传 MinIO",
  "result": { "pmtiles_url": "...", "tile_count": 1024, ... },
  "error": null,
  "create_time": "...",
  "update_time": "..."
}
```

---

## 本机调试（跳过 Celery）

环境：`run_inline=true` 后 manager 直接同步执行，写库任务状态会正常更新。

```bash
# vector
curl -X POST "http://127.0.0.1:10846/my_api/gis/pmtiles/publish/" \
  -H "Authorization: Token $TOKEN" \
  -F "src=@points.geojson" \
  -F "tile_type=vector" \
  -F "run_inline=true"

# raster
curl -X POST "http://127.0.0.1:10846/my_api/gis/pmtiles/publish/" \
  -H "Authorization: Token $TOKEN" \
  -F "src=@test_rgb.tif" \
  -F "tile_type=raster" \
  -F "run_inline=true"

# terrain
curl -X POST "http://127.0.0.1:10846/my_api/gis/pmtiles/publish/" \
  -H "Authorization: Token $TOKEN" \
  -F "src=@test_dem.tif" \
  -F "tile_type=terrain" \
  -F "run_inline=true"
```

注意：本机没有 Docker 也没有 mc 客户端，`upload_to_minio` 会失败；
需要把 `GISHelper.upload_to_minio` 改为走 boto3（直接 SDK 调用 MinIO）
或在 40 服务器上跑 worker。
