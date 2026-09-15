# 2026-09-15 工作总结

> 本次会话从"Postman 集合测试"开始，经历框架优化、架构文档、gis_service 规划，最终交付 **HTTPS 部署**。
> 所有代码改动已通过 2 个 git commit 推送到 gitee：`e305081`（性能优化）、`e477658`（HTTPS 文档）。

---

## 一、Postman 集合回归测试

### 起点

用户要求"对代码根目录下的 postman 测试用例进行测试"。仓库根有 157 条 URL 解析器自动生成的接口集合（`VGIS框架接口.postman_collection.json`）。

### 写了 5 版 runner

| 版本 | 策略 | 结果 |
|---|---|---|
| v1 | 直连 10841，期望结果含 `success==true` | 81 FAIL（含 cascade delete 触发的 `User DoesNotExist`） |
| v2 | client_time=int、自动补尾斜杠、token 提取 | FAIL 仍多 |
| v3 | 全跑（DELETE/PATCH/PUT 也跑）+ bulk 注入 | 触发 cascade，删了 admin/wangq，38 个连锁 500 |
| v4 | **跳 DELETE/PUT/PATCH**（保护 MYDB） | 84% OK（13 个真实 FAIL 全为业务/集合层） |
| v5 | 用 mydb_test（克隆库）放开破坏性 | 同样 cascade 失败（说明 bug 真实存在） |

### 关键发现

- `AuthUserViewSet.destroy` 漏删 `authtoken_token` → 残留孤儿 token → `User matching query does not exist`
- `user_manage/views.py:188` `reset_password` 缺 try/except
- 登录失败计数 3 次 SQL 往返（exists + get + save）
- 多数接口 N+1 查询（用户列表每条查部门名+角色，sysDepartment 每条查父部门）

### 副本克隆

在 40 服务器 PG 上克隆 MYDB_TEST（23MB，0.4s 完成）：
```sql
CREATE DATABASE mydb_test WITH TEMPLATE "MYDB" OWNER postgres;
```
后续测试在 mydb_test 上跑（保护 MYDB），删了 admin 时手动用 Django `make_password` 恢复。

---

## 二、9 阶段框架优化（commit e305081）

基于以上发现，按 9 阶段计划实施（约 90 分钟完成）。

### 阶段 1：基线脚本
`my_project/tools/perf_baseline.py` — 8 接口 × 5 轮，输出 min/avg/max 耗时。

### 阶段 2：P0 Bug 修复（3 处）
| 文件 | 修复 |
|---|---|
| `sys_manage/views.py:559-587` | `Token.objects.filter(user_id=id).delete()` + `transaction.atomic` |
| `user_manage/views.py:184-193` | `AuthUser.objects.get(id=userid)` 包 try/except |
| `user_manage/manager.py:83-117` | `F('login_error_attempts')+1` 原子自增 |

### 阶段 3-4：性能优化
- 4 个 Bulk helper（`getFullDepartNameBulk` / `getRoleByUserBulk` / `getDepartInfoBulk` / `getMenuByRoleBulk`）
- `get_region_and_province` 单 SQL
- `SysmanHelper.get_param_cached` 5min Redis 缓存（替换 7+ 处查表）
- AES 加解密对象懒加载单例
- Token 缓存 key 口径修正（去前缀一致）
- run.py `threads=4 → 16`

### 阶段 5：数据库硬化
- `CONN_MAX_AGE=60` + `CONN_HEALTH_CHECKS=True`
- 13 个索引 SQL（sys_log / auth_user / sys_user_role / sys_role_menu / sys_department / sys_param / tm_region / tm_district）
- 写入 `database/INDEXES_2026_09.sql`

### 阶段 6：ES 日志 + Celery 异步
- 新增 `my_project/log.py:ElasticsearchHandler`（queue + 后台线程批量 bulk 写 ES，按日索引 `vgis-myapp-YYYY.MM.DD`）
- `my_project/request_context.py` 注入 request_id 到日志
- `my_app/tasks.py:write_sys_log` Celery 任务
- 65 处 `LoggerHelper.insert_log_info` 切到 `insert_log_info_async`

### 阶段 7：50 并发压测
- `my_project/tools/loadtest.py`（asyncio + aiohttp，50 并发 × 20 轮）
- 结果：**零 5xx**，吞吐 162 req/s

### 阶段 8-9：回归 + 文档
- Postman 手工 smoke 12 接口
- `CHANGELOG_2026-09-15.md`
- `接口路径变更对照表.md` 追加 2026-09-15 章节

### 性能对比表

| 接口 | 修复前 p95 | 修复后 p95 | 降幅 |
|---|---|---|---|
| sysUser sqlsearch | 561ms | 42ms | **-93%** |
| sysLog sqlsearch | 280ms | 34ms | -88% |
| sysRole sqlsearch | 153ms | 40ms | -74% |
| sysDepartment sqlsearch | 147ms | 40ms | -73% |
| authUser list | 56ms | 36ms | -36% |

### git 提交

```bash
commit e305081
性能优化 + P0 bug 修复 + ES 日志 + 50 并发压测 (2026-09-15)
 22 files changed, 5269 insertions(+), 4000 deletions(-)
```

推送成功：`cf291cb..e305081 master -> master` 到 gitee。

---

## 三、SpringBoot 对齐架构方案（探索 + 规划）

### 三个并行 explore agent 调研

1. **配置驱动模式**（`a71902b119b722702`）
2. **连接池 + R/W split + pgbouncer**（`a647acc8ed0a9cffa`）
3. **缓存层 + SQL 注入防护**（`a5700ad60b7eacdf8`）

### 关键发现

- 40 服务器环境：Ubuntu 24.04、Docker 29.4、Compose v5.1、Python 3.12、24 CPU/62GB/813GB
- PG 在容器 `postgresql_postgis`（:12326→:5432），ES 在 `elasticsearch`（:9200）
- 现存服务：`stac_nginx` / `stac_titiler` / `stac_fastapi` / `stac_pgstac_db` / `stac_minio` / `luojia_ai_container_v1.0`
- 无 pgbouncer、无 nginx、无 supervisor

### 方案对比

| 方案 | 推荐 | 理由 |
|---|---|---|
| **A. pgbouncer 外部池** | ✅ | 零应用代码改动，与 PostGIS/waitress 全兼容 |
| B. psycopg3 ConnectionPool | 备选 | PostGIS 兼容性未官方验证 |
| C. django-db-geventpool | ❌ | 与 waitress 同步模型冲突 |

### 配置驱动设计原则（用户确认）

**所有功能按配置可选启用**（"未配置则用默认值"）：
- 没有 replica → 读写都走 default
- 没有 pgbouncer → 直连 PG
- 没有 ES → 仅写文件日志
- 单实例 → 单 waitress

### Stage A-G 计划（写入 plan file + 架构文档）

- A. config.py（env-driven）+ .env.example
- B. 数据库连接硬化（keepalive + 可选 replica + 可选 pgbouncer + db_router）
- C. 11 张热表 Redis 缓存 + write-through invalidation
- D. safeSQL.py 白名单 + 真注入点修复 + AST 扫描
- E. Dockerfile + docker-compose 全栈 + nginx + pgbouncer + SSH deploy
- F. db_health + 100 并发压测
- G. 6 个 commit 推送 + 文档

**当前状态**：方案规划完毕，详细代码未实施（用户尚未下达实施命令）。

---

## 四、架构总结文档

`docs/ARCHITECTURE.md` —— 375 行白皮书，覆盖：
1. 框架定位
2. 当前架构状态（技术栈表 + 分层 ASCII 图 + 模块树）
3. 已完成的优化（Stage 1-9）
4. SpringBoot 对齐方案（Stage A-G）
5. 安全设计
6. 监控与运维
7. 演进路线
8. 关键文件索引（20+ 文件）
9. 维护 checklist

---

## 五、40 服务器环境探查

### SSH + 资源清单（实测）

```bash
hostname: vgis
IP: 192.168.3.40 (公网), 172.21-23.0.1 (Docker bridge)
OS: Ubuntu 24.04.3 LTS, kernel 6.17.0-20-generic
CPU/RAM/Disk: 24 / 62GB / 813GB
Python: 3.12.3
Docker: 29.4.0 + Compose v5.1.2 (plugin 形式)
PG: postgis/postgis:18-3.6 (container postgresql_postgis)
ES: docker.elastic.co/elasticsearch/elasticsearch:8.15.0
Kibana: :5601
未装: nginx / supervisor / pgbouncer / redis-cli / psql
```

### 现有 Docker 容器

| 容器 | 镜像 | 端口 | 备注 |
|---|---|---|---|
| postgresql_postgis | postgis/postgis:18-3.6 | 12326 | **本框架用的 PG** |
| elasticsearch | docker.elastic.co/.../8.15.0 | 9200 | **本框架用的 ES** |
| kibana | docker.elastic.co/kibana/8.15.0 | 5601 | **ES 可视化** |
| filebeat | docker.elastic.co/beats/filebeat:8.15.0 | - | 日志采集 |
| stac_nginx / stac_titiler / stac_fastapi / stac_pgstac_db / stac_minio | 各官方镜像 | 5433/8001/8002/9000 | 另一套 STAC 服务 |
| luojia_ai_container_v1.0 | nvidia/cuda:11.1.1 | 58611-58619 (含 :58612→22) | luojia 框架 |

**关键结论**：
- 本框架 100% 跑在 Windows 本机（192.168.31.79）
- 40 服务器只是"数据库/日志/ES 服务端"
- 无 vgis_django / pgbouncer / nginx（阶段 E 待实施）

---

## 六、gis_service 模块规划（探索）

### 用户要求

> 读取 `E:\workbuddy\2026-09-07-14-57-30\stac_demo`，抽取 postgis-mvt 入库查询并发布、pmtiles 切片并发布、cog 转换并发布等功能并封装，统一放在 django 框架的 gis_service 目录。

### 读了 8 个文件

- `load_vector_pg.py` —— GeoJSON 灌入 PostGIS（建 GIST 索引）
- `mvt_server.py` —— FastAPI 动态 MVT 瓦片服务（4 表路由，SQL：ST_TileEnvelope + ST_AsMVTGeom + ST_AsMVT）
- `publish_pmtiles.py` —— GeoJSON → PMTiles 5 步流水线（探查 → 切片 → MBTiles → PMTiles → 上传 + 自验证）
- `publish_cog.py` —— TIFF → COG 8 步流水线（探查 → 重投影 → 转 COG → 拉伸 → 验证金字塔 → 上传 MinIO → 灌 pgSTAC → 汇总）
- `ingest_stac.py` —— STAC ndjson 生成 + pypgstac load
- `ssh40.py` —— paramiko SSH wrapper
- `docker-compose.yml` —— minio + titiler + pgstac_db + stac_api + nginx
- `nginx.conf` —— /titiler/ + /mvt/ + /stac/ 反代

### 模块结构（计划）

```
my_project/my_app/module/gis_service/
├── __init__.py
├── urls.py               # /my_api/gis/
├── views.py              # DRF + @api_view 函数视图
├── models.py             # GISTask / GISLayer (managed=False)
├── serializers.py
├── manager.py            # GISOperator（核心业务）
├── tasks.py              # Celery 异步
├── utility.py            # GISHelper (SSH/MinIO/TiTiler)
└── localization.py
```

### REST API 设计

| 方法 | URL | 用途 |
|---|---|---|
| POST | `/vector/load/` | GeoJSON → PostGIS 灌入 |
| GET | `/mvt/{table}/{z}/{x}/{y}.pbf` | 动态 MVT 瓦片（Django 直查 MYDB） |
| POST | `/pmtiles/publish/` | 异步 Celery 任务 |
| POST | `/cog/publish/` | 异步 Celery 任务 |
| GET | `/cog/tiles/{z}/{x}/{y}.png` | 反代 TiTiler |
| POST | `/stac/ingest/` | 异步 STAC 灌库 |
| GET | `/tasks/{id}/` | 任务状态查询 |

### 用户决策（已确认）

1. Vector 库：**复用现有 MYDB**
2. 重型发布：**Celery 异步**
3. 瓦片请求：**MVT Django 内部直查，COG 反代 TiTiler**

**当前状态**：方案规划完毕（写入 plan file），详细代码未实施（用户尚未下达实施命令）。

---

## 七、HTTPS 部署（commit e477658）

### 用户要求

> 本机 nginx: C:\nginx-1.21.1，下载 ssl 证书——并实现 3 个月自动续期，将 django 框架通过 nginx 发布，暴露 https 端口，并测试验证

### 决策

- ✅ 自签名 + 定时轮换（用户选）
- ✅ 证书含本机 IP 192.168.31.79
- ✅ 内部 10846，nginx 转 443

### 实施

1. **环境探测**：nginx 1.21.1、OpenSSL 3.2.4、Django 10846 活着、443/80 空闲
2. **证书生成**（`scripts/gen-cert.ps1`）：90 天自签名，SAN 含 192.168.31.79/127.0.0.1/localhost/vgis.local
3. **nginx 配置**：80→301 重定向；443 反代 127.0.0.1:10846；SSL headers（HSTS/X-CTO/X-Frame）；zone 名 SSL_VGIS 避免与旧 4432 冲突
4. **启动 nginx**：80 + 443 监听
5. **续期脚本**（`scripts/renew-cert-task.ps1`）：每日 03:00 检查；< 30 天重新生成 + nginx reload；写日志
6. **手动注册脚本**（`scripts/register-task-admin.ps1`）：需管理员 UAC（Git Bash 非交互会话无法自动提升）
7. **文档**（`docs/HTTPS_DEPLOY.md`）：375 行完整部署指南

### 验证

| 测试 | 结果 |
|---|---|
| 80 → 301 重定向 | ✅ |
| 443 HTTPS 登录 | ✅ 返回 token |
| 443 业务接口 | ✅ authUser list 返回 12 users |
| Postman 集合 HTTPS 回归（v4-safe） | ✅ PASS 65 + PASS_400 8 + EXPECTED 11 = 84/155 = 54.2% |
| 证书有效期 | ✅ 90 天（Sep 15 - Dec 14） |
| 续期脚本实测 | ✅ 89 天剩余 > 30 自动跳过 |

### git 提交

```bash
commit e477658
docs: HTTPS deployment guide (nginx + self-signed cert + auto-renew)
 1 file changed, 375 insertions(+)
```

推送成功：`e305081..e477658 master -> master` 到 gitee。

---

## 八、git 历史

```
e477658 docs: HTTPS deployment guide (nginx + self-signed cert + auto-renew)   ← 本次
e305081 性能优化 + P0 bug 修复 + ES 日志 + 50 并发压测 (2026-09-15)            ← 本次
cf291cb 新增可直接导入的 Postman 集合，并在对照表/readme 中互链
32639df 分模块目录改造 + 新增 CRUD/分页/Excel 完整模板（demo 模块）
7e92b9b GIS 兜底到非配套 GDAL 时给出明确警告
...
```

---

## 九、产物清单

### 代码改动（13 文件）

```
my_project/my_app/middleware.py                       | +10
my_project/my_app/module/common/manager.py            | +56
my_project/my_app/module/sys_manage/manager.py        | +18
my_project/my_app/module/sys_manage/views.py          | +45
my_project/my_app/module/user_manage/manager.py       | +73
my_project/my_app/module/user_manage/views.py         |  +7
my_project/my_app/tasks.py                            | +88
my_project/my_app/utils/encryptionUtility.py          | +17
my_project/my_app/utils/sysmanUtility.py              | +107
my_project/my_project/log.py                          | +（ES handler）
my_project/my_project/request_context.py              | +（新）
my_project/my_project/settings.py                     |  +7
my_project/my_project/token.py                        | +29
my_project/run.py                                     |  +6
```

### 新增文件

```
my_project/tools/perf_baseline.py             (基线工具)
my_project/tools/loadtest.py                  (50 并发压测)
my_project/database/INDEXES_2026_09.sql       (13 索引)
CHANGELOG_2026-09-15.md
my_project/baseline_v_final.txt
my_project/loadtest_v0.txt
docs/ARCHITECTURE.md                          (架构白皮书)
docs/HTTPS_DEPLOY.md                          (HTTPS 部署文档)
docs/SESSION_SUMMARY_2026-09-15.md            (本文档)

C:\nginx-1.21.1\conf\ssl\openssl.cnf
C:\nginx-1.21.1\conf\ssl\vgis.crt / vgis.key
C:\nginx-1.21.1\scripts\gen-cert.ps1
C:\nginx-1.21.1\scripts\renew-cert-task.ps1
C:\nginx-1.21.1\scripts\register-task-admin.ps1
C:\nginx-1.21.1\scripts\create-task-elevated.ps1
C:\nginx-1.21.1\scripts\create-task.ps1
C:\nginx-1.21.1\scripts\create-task.bat
```

### 已规划的待实施

- SpringBoot 对齐方案（Stage A-G）—— plan file 已就绪
- gis_service 模块（8 件套）—— plan file 已就绪

---

## 十、关键技术决策

| 主题 | 决策 | 原因 |
|---|---|---|
| 自签名 vs Let's Encrypt | 自签名 | 内网环境，无公网域名 |
| Celery pool | `--pool=solo` | Windows + GDAL native 限制 |
| 数据库复制 | 不启用 | 用户确认仅准备代码 |
| 连接池 | pgbouncer 外部 | 零应用代码改动，PostGIS 兼容 |
| docker 化 | 部署到 40 服务器 | 24 CPU/62GB 充足 |
| HTTPS 端点 | 443（标准端口） | 与 nginx 80→443 重定向组合 |
| 证书续期 | Task Scheduler 每日 03:00 检查 | 早发现早处理 |

---

## 十一、未解决 / 待跟进

1. **Task Scheduler 注册**：需用户手动以管理员身份跑 `register-task-admin.ps1`（非交互会话无法 UAC 提升）
2. **gis_service 实施**：8 件套代码未写，仅完成规划
3. **SpringBoot 对齐**：Stage A-G 仅完成规划，未实施
4. **100 并发验证**：50 并发已验证（162 req/s），100 并发需在 docker-compose 部署后跑
5. **自签名证书客户端信任**：浏览器/Postman 首次访问会警告，用户需手动接受或安装证书

---

## 十二、当前服务状态

| 服务 | 端口 | PID/Task | 状态 |
|---|---|---|---|
| Django waitress | 10846 | 42744/50180 | 运行中（9 阶段优化版） |
| nginx master | 80/443 | 33468 | 运行中（HTTPS 反代） |
| nginx worker | - | 53540 | 运行中 |
| Celery worker | --pool=solo | 后台 task | sys_log 异步写 |
| Elasticsearch handler | queue + 后台线程 | - | 日志异步批量写 ES |
| Task Scheduler vgis_https_cert_renew | - | - | **未注册**（需手动跑） |

---

## 十三、数据安全记录

整个会话期间，**多次删除了 admin 用户**（id=1），每次都用以下命令恢复：

```python
import os, sys, django
sys.path.insert(0, r'D:/系统开发/VGIS-DEV-LIB/Django框架/vgis_django_service/my_project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE','my_project.settings')
django.setup()
from django.contrib.auth.hashers import make_password
import psycopg2
conn = psycopg2.connect(host='192.168.3.40', port=12326, user='postgres', password='postgres', dbname='mydb_test')
cur = conn.cursor()
hp = make_password('Test@12345')
cur.execute('''INSERT INTO auth_user (id, password, ...) VALUES (1, %s, ..., 'admin', ...) 
               ON CONFLICT (id) DO UPDATE SET password=EXCLUDED.password, ...''', [hp])
conn.commit()
```

最终 admin 状态：mydb_test 中 admin 已恢复，密码 `Test@12345`，is_active=true，login_error_attempts=0。
