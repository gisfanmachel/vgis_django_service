# CHANGELOG — 2026-09-15 v2（SpringBoot 对齐 Stage A-G）

5 个 commit，本轮改动全清单。

## 改动一览

| Stage | 主题 | commit | 关键文件 |
|---|---|---|---|
| A | env-driven config（去硬编码） | 8ac3713 | my_project/my_project/config.py + .env.example + .gitignore + settings.py |
| B | DB 连接硬化 + replica/pgbouncer 路由 | 8ac3713 | my_project/my_project/db_router.py + settings.py:_build_db_options |
| C | 11 张热表缓存 + Celery worker_ready 预热 | 33abf36 | cacheHelper / cacheInvalidate / cacheWarmer + sys_manage/views.py + celery.py |
| D | SQL 注入防护 + AST 静态扫描 | b4fb499 | safeSQL / paginationUtility / demo/manager.py + checks.py:W002 |
| E | Docker 全栈部署 | d895d7e | Dockerfile + deploy/docker-compose.yml + nginx.conf + pgbouncer + deploy_to_40.py |
| F | db_health 管理命令 + _env 类型修复 | ceb1ee7 | management/commands/db_health.py + config.py |
| G | 文档 + 50 并发压测验证 | (本 commit) | 运行环境.md / ARCHITECTURE.md / CHANGELOG_2026-09-15-v2.md |

## Stage A：env-driven 配置中心

- `my_project/my_project/config.py`：所有可调参数都通过同名环境变量覆盖
  - DB（DEFAULT/REPLICA/PGBOUNCER 三大块）
  - Redis（HOST/PORT/PASSWORD/DB_CACHE/DB_CHANNEL/DB_CELERY/PROTOCOL）
  - ES（HOSTS/USER/PASSWORD/INDEX_PREFIX/FLUSH_INTERVAL/BATCH_SIZE/ENABLED）
  - `_env_bool`：1/true/yes/on 视为 True
- `my_project/.env.example`：完整变量清单 + 注释
- `.gitignore`：新增 `.env` `.env.local` `.env.*.local`
- `settings.py`：所有硬编码常量改读 `config.py`

**零回归**：默认行为不变（DB_REPLICA_ENABLED=false / PGBOUNCER_ENABLED=false）

## Stage B：DB 连接硬化

- `_build_db_options()`：libpq 全面保活
  - `keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=5`
  - `options="-c statement_timeout=30s -c idle_in_transaction_session_timeout=60s"`（PG 会话级超时）
- `_build_db_block(user, pwd, host, port, dbname)`：复用引擎 + CONN_MAX_AGE + CONN_HEALTH_CHECKS
- `db_router.py:PrimaryReplicaRouter`
  - 读走 replica alias（仅当 DATABASES 含 'replica'）
  - 写永远走 default
  - migrate 只在 default 跑

## Stage C：缓存层

- `cacheHelper.TableCacheHelper`
  - `get_or_load(table_name, loader, ttl, scope, suffix)`：先 cache 后 loader
  - `invalidate(table_name, ...)` / `invalidate_pattern(table_name)`（django_redis 走 delete_pattern，locmem 降级）
  - JSON serialize 兜底（默认用 JSON 字符串，load 时 deserialize）
- `cacheInvalidate.invalidate_table(table_name)`：表级失效入口
- `cacheWarmer.warm_all_caches`：Celery 任务，预热 5 张表
  - sys_dict_catelog / sys_dict / sys_menu / tm_district / tm_region
- `celery.py:@worker_ready`：worker 启动后 5s 自动触发预热
- `sys_manage/views.py`：8 个 ViewSet 的 create/update/destroy 成功路径加 `invalidate_table()`

## Stage D：SQL 注入防护

- `safeSQL.py`
  - `ALLOWED_TABLES`（30+ 张业务表）
  - `ALLOWED_DIRECTIONS = {asc, desc, ASC, DESC}`
  - `assert_table_allowed / safe_format_table / safe_order_by / safe_ident / UnsafeIdentifierError`
- `paginationUtility.check_order_by`：方向统一小写后比对，避免大小写绕过
- `demo/manager.py:update_data`：在硬编码列表外再过一道 `UPDATE_FIELD_WHITELIST` 防御
- `checks.py:check_raw_sql_format_usage`（W002）
  - AST 静态扫描 my_app 下所有 cursor.execute("...".format(x)) 类用法
  - 命中后 warning 提示走 safeSQL 白名单

## Stage E：Docker 化

- `my_project/Dockerfile`：python:3.12-slim + libpq/libgdal/libgeos/libproj + gunicorn 23.0.0
  - 默认 4 worker / 16 thread / 60s timeout
- `deploy/docker-compose.yml`
  - web + celery + nginx + redis 默认启
  - postgis / pgbouncer 注释默认关，按需启用
- `deploy/nginx.conf`：least_conn 上游 + 安全响应头
- `deploy/pgbouncer/pgbouncer.ini + Dockerfile`：transaction 池模式 / 10000 client / 20 pool
- `deploy/deploy_to_40.py`：paramiko SSH + scp mirror + `docker-compose up -d --build --scale web=N`
  - 仅当用户显式触发时执行

## Stage F：可观测性

- `management/commands/db_health.py`
  - `python manage.py db_health` / `--alias default|replica`
  - 输出 PG version + active/idle 连接数 + SELECT 1
- `config._env` 类型修复：default 也走 cast（避免 `CONN_MAX_AGE='60'` 启动报错）

## Stage G：文档 + 验证

- `运行环境.md`：补 config.py / db_router / pgbouncer / replica / 安全头 / 续期等说明
- `docs/ARCHITECTURE.md`：把 Stage A-G 从"计划"状态改为"已实施"，加 git commit hash
- 本 CHANGELOG

## 验证结果

| 步骤 | 结果 |
|---|---|
| `manage.py check` | 1 warning（demo/manager.py:201，由 stage D 主动标出，未修） |
| `manage.py db_health` | `[default] PG PostgreSQL 18.4 ...` + `connections: active=1 idle=16` + `SELECT 1 OK` |
| `curl 10846` | 404（Django 没 / 路径，正常） |
| `curl POST loginWithForce` | 200 OK |
| `tools/loadtest.py --users 50 --rounds 5` | 1750 req / 12.4s / 141 req/s / **零 5xx** |

## 已知遗留

1. **AST 扫描告警 W002 demo/manager.py:201** —— 现有代码已加 UPDATE_FIELD_WHITELIST 防御，但 AST 扫描仍标出 `update tt_demo_item set {} where id = %s` 这行 format。后续若要彻底消除告警，可改用列表推导拼接。
2. **Docker 镜像未实际构建/推到 40** —— 按用户要求保留 deploy_to_40.py 等用户手动触发。
3. **pgbouncer / postgis / replica** 默认关闭，需按需启用对应环境变量。
4. **运行 waitress 重启** —— 配置变更后已重启 Django 进程（PID 27224），其它 Django 实例需用户按需重启。

## 下一阶段建议

- **Stage H**：gis_service 模块（PMTiles / COG / STAC ingest）—— config.py 已预留 GIS_* 段
- **Stage I**：把 ES handler 升级到 opensearch-py / 双写 HDFS 归档
- **Stage J**：Postman v5-safe 回归（在 v4-safe 基线 84/155 基础上，启用 DELETE/PUT/PATCH 但用 v5-safe 模式）
- 启用 replica alias：新建 readonly_user，PG 上 grant SELECT 权限
- 启用 pgbouncer：先在 stage 环境跑 1 web → 验证长连接场景无 regression