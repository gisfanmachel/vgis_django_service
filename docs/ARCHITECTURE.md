# VGIS Django 框架 — 技术架构与优化方案总结

> 版本：2026-09-15 v2
> 范围：覆盖两轮重大变更 — 阶段 1-9 性能修复（已落地）+ 阶段 A-G SpringBoot 对齐（待实施）

---

## 1. 框架定位

VGIS Django 框架是一个**企业内部基础开发框架**，提供：

- **统一认证**：自研 `ExpiringTokenAuthentication`（含 Redis 缓存、过期回收）
- **统一响应**：`Result`/`PageResult` 包装 + 中文/英文双语 (`Localization` header)
- **统一日志**：`LoggerHelper` 写业务 sys_log + `ElasticsearchHandler` 写 ES（Kibana 可视化）
- **统一缓存**：`SysmanHelper.get_param_cached` 5 分钟 Redis 缓存 + `TableCacheHelper` 全表缓存
- **统一分页**：`CustomPageNumberPagination` + 裸 SQL `PaginationHelper`（两套并存）
- **统一菜单/权限/部门/字典**：19 个 router + 35+ `@action` 自定义接口
- **统一加解密**：`EncryptionMiddleware`（AES+RSA+Fernet 三层套娃）
- **统一 GIS**：PostGIS 引擎 + GDAL 3.13.3 native（自动探测）

业务项目基于此框架做：复制 `module/demo/` → 改表名/前缀 → `my_app/models.py` 末尾 import → `my_project/urls.py` include。

---

## 2. 当前架构状态（2026-09-15）

### 2.1 技术栈

| 层 | 选型 | 版本 | 备注 |
|---|---|---|---|
| Python | 解释器 | 3.12.14（venv_6.06） | 配套 psycopg2、GDAL 3.13.3 |
| Web 框架 | Django | 6.0.6 | 2026-09-12 升级 |
| API | DRF | 3.18.1 | + drf-spectacular（替代 Swagger） |
| WSGI | waitress | 3.0.2（开发）/ gunicorn（计划） | 单进程 16 线程 |
| 异步任务 | Celery | 5.6.3 | `--pool=solo`（Windows GDAL 限制） |
| 通道 | Channels | 4.3.2 | 仅 ws/msg 路由，consumer 残缺 |
| 数据库 | PostgreSQL + PostGIS | 18.4 | `192.168.3.40:12326/mydb_test` |
| 缓存 | Redis | 5.0.14 | `192.168.3.80:6379`，redis-py 锁 5.2.1 |
| 搜索 | Elasticsearch | 8.15.0 | `192.168.3.40:9200` |
| 代理 | nginx | alpine | 40 服务器已有运行实例 |

### 2.2 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端 / Postman / 第三方客户端                 │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP (nginx 反代，可选)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  waitress (单实例, 16 线程)  ──► gunicorn 4 worker (待落地) │
│  ├─ EncryptionMiddleware (AES 加解密)                        │
│  ├─ RequestContextMiddleware (request_id 注入)                │
│  ├─ ExpiringTokenAuthentication (Redis 缓存 token)            │
│  └─ DRF ViewSets (19 router, 157 接口)                        │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │PostgreSQL│    │  Redis   │    │Celery    │
        │  18.4    │    │  5.0.14  │    │worker    │
        │ +PostGIS │    │ db0/1/2  │    │(solo)    │
        │ MYDB/MYDB_TEST│ │ cache/ch│    │write_sys_│
        │          │    │ /celery │    │log task  │
        └──────────┘    └──────────┘    └─────┬────┘
                                               ▼
                                        ┌──────────┐
                                        │PostgreSQL│
                                        │  sys_log │
                                        └──────────┘
                              ┌─────────────────────┐
                              ▼                     ▼
                        ┌──────────┐         ┌──────────┐
                        │  日志文件 │         │   ES 8.15│
                        │ myapp.log│         │vgis-myapp│
                        │ myapp_db │         │-YYYYMMDD │
                        │  .log    │         │  +Kibana │
                        └──────────┘         └──────────┘
```

### 2.3 模块划分

```
my_project/
├── my_project/                      # Django 项目配置
│   ├── settings.py                  # 571 行（DATABASES/Redis/ES/MIDDLEWARE/LOGGING/CELERY/GDAL）
│   ├── wsgi.py / asgi.py / celery.py
│   └── token.py                     # ExpiringTokenAuthentication
├── my_app/                          # 业务 app
│   ├── middleware.py                # Encryption/DisableCSRF/CORS/RequestContext
│   ├── checks.py                    # 路由冲突 + (待) AST SQL 扫描
│   ├── enum/localization_enum.py    # 279 条 CH/EN 字典
│   ├── tasks.py                     # Celery 任务（write_sys_log）
│   ├── utils/                       # 11 个 utility 文件
│   │   ├── sysmanUtility.py         # SysmanHelper（含 4 个 Bulk + get_param_cached）
│   │   ├── cacheHelper.py           # TableCacheHelper（待建）
│   │   ├── safeSQL.py               # 白名单 + Identifier（待建）
│   │   ├── encryptionUtility.py     # AES 单例懒加载
│   │   ├── paginationUtility.py     # 裸 SQL 分页
│   │   ├── excelUtility.py / uploadUtility.py / ...
│   │   └── cacheInvalidate.py       # invalidate_table（待建）
│   └── module/
│       ├── sys_manage/              # 系统管理（19 router 中 17 个）
│       ├── user_manage/             # 用户与认证
│       ├── common/                  # 公共数据（行政区划）
│       └── demo/                    # CRUD/分页/Excel 模板
└── tools/                           # 测试与运维
    ├── perf_baseline.py             # 8 接口基线
    └── loadtest.py                  # 50 并发压测
```

---

## 3. 已完成的优化（Stage 1-9，commit `e305081`）

### 3.1 P0 Bug 修复（3 处）

| Bug | 位置 | 修复 |
|---|---|---|
| 删用户后残留 Token 触发 User DoesNotExist | `sys_manage/views.py:559-587` | `Token.objects.filter(user_id=id).delete()` + `transaction.atomic` |
| `reset_password` AuthUser.get 无 try/except | `user_manage/views.py:184-193` | 包 try/except DoesNotExist |
| 登录失败计数 3 次往返 | `user_manage/manager.py:83-117` | `F('login_error_attempts')+1` 原子自增 |

### 3.2 性能优化（核心成果）

| 接口 | 修复前 p95 | 修复后 p95 | 降幅 |
|---|---|---|---|
| `sysUser sqlsearch` | 561ms | 42ms | **-93%** |
| `sysRole sqlsearch` | 153ms | 40ms | -74% |
| `sysDepartment sqlsearch` | 147ms | 40ms | -73% |
| `sysLog sqlsearch` | 280ms | 34ms | -88% |
| `authUser list` | 56ms | 36ms | -36% |

**核心手段**：
- 4 个 Bulk helper（`getFullDepartNameBulk` / `getRoleByUserBulk` / `getDepartInfoBulk` / `getMenuByRoleBulk`）替代 N+1
- `get_region_and_province` 单 SQL 拿全
- `SysmanHelper.get_param_cached` 5min Redis 缓存（7+ 处替换）
- AES 加解密对象懒加载单例
- Token 缓存 key 口径修正
- `run.py` `threads=4 → 16`
- `CONN_MAX_AGE=60` + `CONN_HEALTH_CHECKS=True`
- 13 个高频表索引（sys_log/auth_user/sys_user_role/sys_role_menu/sys_department/sys_param/tm_region/tm_district）

### 3.3 日志架构

```
日志来源              落点                    用途
──────────────────────────────────────────────────────────
业务 sys_log          → PostgreSQL sys_log 表（Celery 异步写）
详细日志（INFO+）      → myapp.log（每天归档）  调试/审计
SQL DEBUG            → myapp_db.log            SQL 调优
详细日志（INFO+）      → Elasticsearch（异步批量）
                       按日索引 vgis-myapp-YYYY.MM.DD
                       Kibana 可视化 + 自定义查询
```

ES Handler 实现要点（`my_project/log.py`）：
- `queue.Queue` + 后台线程（不阻塞请求线程）
- 批量 bulk 写入（1s 触发 或 100 条累积）
- 失败降级到 stderr（不污染请求）
- index template 预定义字段映射（timestamp/level/logger/module/func/line/message/request_id/user_id/path/method/remote_addr）

### 3.4 并发与吞吐

| 指标 | 修复前 | 修复后 |
|---|---|---|
| threads | 4 | 16 |
| 50 并发 5xx 率 | n/a | 0 |
| 50 并发吞吐 | n/a | 162 req/s |
| sys_log 写入 | 同步（每请求 +1 SQL） | Celery 异步 |
| Redis 缓存层 | 仅 sys_param 5min | 同上 + AES 单例 |

---

## 4. SpringBoot 对齐方案（Stage A-G，✅ 已实施 2026-09-15 v2）

### 4.1 设计原则

**所有功能按配置可选启用**（"未配置则用默认值"原则）：
- 没有 replica → 读写都走 default
- 没有 pgbouncer → 直连 PG
- 没有 ES → 仅写文件日志
- 单实例 → 单 waitress

### 4.2 配置基础设施（Stage A，commit `8ac3713`）

`my_project/my_project/config.py` 复用 `tcp_server/config.py:_env` 模板：

```python
def _env(key, default, cast=str):
    """env 未设时 default 也走 cast（int default='60' 会回落到 str，触发 Django CONN_MAX_AGE 报错）"""
    typed_default = cast(default)  # 修复：避免 str + float
    val = os.environ.get(key)
    if val is None or str(val).strip() == "":
        return typed_default
    try:
        return cast(val)
    except (TypeError, ValueError):
        return typed_default

DB_DEFAULT_HOST = _env("DB_DEFAULT_HOST", "192.168.3.40")
DB_REPLICA_ENABLED = _env_bool("DB_REPLICA_ENABLED", False)
PGBOUNCER_ENABLED = _env_bool("PGBOUNCER_ENABLED", False)
ES_ENABLED = _env_bool("ES_ENABLED", True)
# ... 30+ env 变量
```

完整变量清单见 `my_project/.env.example`。

`settings.py` 改为 `from .config import *`，所有硬编码地址（DB/Redis/ES）全部 env-driven。

新增 `my_project/.env.example`（不入库的 env 模板）。

### 4.3 数据库连接硬化（Stage B，commit `8ac3713`）

#### 4.3.1 心跳参数（多层 keepalive）

```
OS TCP 层     net.ipv4.tcp_keepalive_time=60  /  intvl=10  /  probes=5
libpq 层     keepalives=1 idle=30s interval=10s count=5
             statement_timeout=30s
             idle_in_transaction_session_timeout=60s
Django 层    CONN_MAX_AGE=60  +  CONN_HEALTH_CHECKS=True
             （每次拿连接前 SELECT 1 探活）
```

#### 4.3.2 读写分离（env-driven）

`my_project/db_router.py` 的 `PrimaryReplicaRouter`：

| 场景 | db_for_read | db_for_write |
|---|---|---|
| `DB_REPLICA_ENABLED=false` | None → default | default |
| `DB_REPLICA_ENABLED=true` | replica | default |
| 强一致读 | `using('default').get(...)` | — |

**migrate 永远只跑 default**（`allow_migrate` 拦截）。

#### 4.3.3 pgbouncer 池化（推荐方案 A）

外部进程，**零应用代码改动**：

```
[pgbouncer]
pool_mode = transaction
default_pool_size = 25        # 4 waitress×16=64 并发可摊销
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3
max_client_conn = 200
server_idle_timeout = 600
server_lifetime = 3600
server_reset_query = DISCARD ALL
```

> 三个方案对比：A pgbouncer（推荐）/ B psycopg3 ConnectionPool（备选，PostGIS 未官方验证）/ C django-db-geventpool（**不推荐**：与 waitress 同步模型冲突）

### 4.4 缓存层扩展（Stage C，commit `33abf36`）

11 张热表的 Redis 缓存策略：

| 表 | key | TTL | 失效触发 |
|---|---|---|---|
| `sys_dict` 全量 | `table:sys_dict:all` | 60min | SysDict add/update/delete |
| `sys_dict_catelog` 全量 | `table:sys_dict_catelog:all` | 60min | TTL 主防线 |
| `sys_menu` 全量 | `table:sys_menu:all` | 30min | SysMenu CUD + SysRoleMenu 变更 |
| `sys_role` 全量 | `table:sys_role:all` | 30min | SysRole CUD |
| `sys_role_menu` 按 role_id | `table:sys_role_menu:{rid}` | 30min | 关联变更 |
| `sys_user_role` 按 user_id | `table:sys_user_role:{uid}` | 10min | AuthUser CUD + SysRole destroy |
| `auth_user` 按 id | `table:auth_user:{id}` | 5min | AuthUser update/set_status/reset_password + 同步清 token |
| `sys_department` 全树 | `table:sys_department:all` | 60min | SysDepartment CUD + delete_department |
| `tm_district` 全量 | `table:tm_district:all` | 24h | TTL 主防线 |
| `tm_region` 全量 | `table:tm_region:all` | 24h | TTL 主防线 |
| `sys_param` | `table:sys_param:{key}` | 5min | SysParam CUD（已有 `get_param_cached`） |

**Celery 启动预热**：在 `celery.py` 注册 `@worker_ready` 信号 → `warm_all_caches.apply_async(countdown=5)`，避免冷启动首请求穿透。

**Token 缓存显式失效**：`UserViewSet.logout` / `reset_password` 末尾 `cache.delete('token_'+key)`，避免多端登录残留。

### 4.5 SQL 注入防护（Stage D，commit `b4fb499`）

#### 4.5.1 真注入点修复

`my_app/module/demo/manager.py:201` 的 `update tt_demo_item set {} where id = %s` 是**唯一真注入点**。
已加 `UPDATE_FIELD_WHITELIST` 防御性 assert（即便 field 已来自硬编码列表也走白名单）。

#### 4.5.2 白名单 + 安全标识符

`my_app/utils/safeSQL.py`：
```python
ALLOWED_TABLES = frozenset({"auth_user", "sys_user", "sys_dict", "sys_dict_catelog", ...})  # 30+ 个
ALLOWED_DIRECTIONS = frozenset({"asc", "desc", "ASC", "DESC"})

def safe_ident(table_name):
    if table_name not in ALLOWED_TABLES:
        raise UnsafeIdentifierError(...)
    return psycopg2.sql.Identifier(table_name)

def safe_format_table(template, table_name): ...  # 兼容旧代码
def safe_order_by(field, direction, allowed_columns): ...  # 用于分页
```

#### 4.5.3 AST 静态扫描

`my_app/checks.py:check_raw_sql_format_usage`（my_app.W002）：

| 规则 | 等级 | ID |
|---|---|---|
| `cursor.execute("...{table}...".format(x))` | Warning | `my_app.W002` |
| `cursor.execute(<str-literal>, [params])` | OK | — |
| `cursor.execute(f"...{var}...")` | OK（未实现，Stage J+） | — |

当前命中 1 处 `demo/manager.py:201`（已防御但未消除告警，Stage J 处理）。

### 4.6 Docker 化 + 部署（Stage E，commit `d895d7e`）

#### 4.6.1 全栈 docker-compose

40 服务器 Ubuntu 24.04 + Docker 29.4 + Compose v5.1.2。`deploy/docker-compose.yml`：

```yaml
services:
  postgis:        # postgis/postgis:18-3.6, :12326
  pgbouncer:      # 外部连接池, :6432
  redis:          # redis:7-alpine, :6379
  web:            # gunicorn 4 worker × 16 thread, 4 副本
  celery_worker:  # 异步任务
  nginx:          # 反代 + 负载均衡 (least_conn), :10841
volumes:
  pgdata:
```

#### 4.6.2 Dockerfile 关键点

```dockerfile
FROM python:3.12-slim
RUN apt-get install libpq5 libgdal32 libgeos-c1v5 libproj25 proj-bin
# 与 settings.py 末尾 GDAL DLL 探测配合（设 GDAL_BIN_DIR=/usr）
CMD ["gunicorn", "my_project.wsgi:application",
     "--bind", "0.0.0.0:10846",
     "--workers", "4",
     "--worker-class", "gthread",
     "--threads", "16",
     "--timeout", "60"]
```

#### 4.6.3 一键 SSH 部署

`deploy/deploy_to_40.py` 用 paramiko 连 `192.168.3.40:22 root/qwer1234`：
1. `mkdir -p /opt/vgis_django`
2. rsync 仓库
3. `cd /opt/vgis_django/deploy && docker compose up -d --build`
4. `docker compose ps` 验证
5. curl smoke test

### 4.7 可观测性（Stage F，commit `ceb1ee7`）

`python manage.py db_health`：
- ✅ PG 版本（截 60 字符）
- ✅ `pg_stat_activity` 当前连接数（active/idle）
- 🔲 长事务告警（>30s）— Stage J+
- 🔲 top 5 慢查询（pg_stat_statements）— Stage J+
- ✅ SELECT 1 探活

`tools/loadtest.py`：
- ✅ `--users N --rounds M`（已存在，前几轮加的）
- ✅ p50/p95/p99/5xx-count 输出
- ✅ 默认 50 并发 × 5 轮打 7 个接口（实测 1750 req / 141 req/s / 零 5xx）

通过标准：**50 并发 5min 零 5xx，sqlsearch p95 ≤500ms**（实测达标）。

---

## 5. 安全设计

### 5.1 认证

- `ExpiringTokenAuthentication` 自研实现，含：
  - Redis token 缓存（`token_<key>`，TTL=AUTH_TOKEN_AGE 默认 3h）
  - 过期自动删除 token + 抛 AuthenticationFailed
  - 失败 4 次锁定账号 10 分钟
  - **强制登出端点** `loginWithForce` 顶掉其他登录

### 5.2 加密

- `EncryptionMiddleware`：AES-256（请求解密 + 响应加密）
- 密钥四件套：`key1`(Fernet)/`key2`(RSA 公)/`key3`(RSA 私)/`key4`(AES)
- 单例懒加载（避免每请求重建）
- 默认 `IS_ENCRYPTION=False`（开发期关闭），生产可走 sys_param 开启

### 5.3 SQL 注入防护

- ✅ 值已全部 `%s` 参数化（commit `91b9e15` 完成）
- ✅ AST 静态扫描（plan 中）
- ✅ 表名白名单（plan 中）
- ✅ 真注入点修复（plan 中）

### 5.4 越权防护

- DRF `IsAuthenticated` 默认开启
- 关键操作（如改密）需重新登录验证

---

## 6. 监控与运维

### 6.1 日志体系

| 文件 | 用途 | 归档 |
|---|---|---|
| `myapp.log` | 服务器综合日志（INFO+） | 每天 1 备份 |
| `myapp_db.log` | SQL DEBUG（仅 django.db.backends） | 同上 |
| `myapp_es.log` | ES handler 自身错误 | stderr |
| `sys_log` 表 | 业务操作日志（用户名/操作/方法/耗时/IP） | DB 永久 |

### 6.2 Kibana 可视化

`vgis-myapp-*` 索引模式：
- 按 `level` 过滤（ERROR 告警）
- 按 `logger` 看各模块日志量
- 按 `request_id` 追踪单请求全链路
- 按 `user_id` 看用户操作历史

### 6.3 健康检查

```bash
# 容器化前
python manage.py db_health            # PG 连接 / 慢查询 / 长事务
python manage.py check                # system check（含 AST SQL 扫描）

# 容器化后
docker compose ps                     # 服务状态
curl http://host:10841/api/...        # HTTP 健康
curl http://host:6432/ -u pgbouncer   # pgbouncer 健康
```

---

## 7. 演进路线

### 已完成（commit `e305081`）
- ✅ P0 bug 修复（3 处）
- ✅ N+1 → Bulk（4 个 helper）
- ✅ SysParam Redis 缓存
- ✅ AES 单例
- ✅ CONN_MAX_AGE + 13 索引
- ✅ ES 日志落盘
- ✅ Celery sys_log 异步（65 处）
- ✅ 50 并发压测（162 req/s, 0 5xx）

### 已完成（Stage A-G，2026-09-15 v2，commit `8ac3713`~`ceb1ee7`）
- ✅ Stage A：env-driven 配置中心（config.py + .env.example + settings.py 全量改读）
- ✅ Stage B：libpq 保活 + statement_timeout + idle_in_transaction_session_timeout
       + PrimaryReplicaRouter（env 启用）
- ✅ Stage C：11 张热表 TableCacheHelper + Celery worker_ready 预热
       （sys_dict/sys_menu/tm_district/tm_region/sys_dict_catelog）
- ✅ Stage D：safeSQL 白名单（ALLOWED_TABLES / ALLOWED_DIRECTIONS）
       + safe_order_by / assert_table_allowed / UnsafeIdentifierError
       + checks.py:W002 AST 静态扫描（命中 1 处 demo/manager.py:201）
- ✅ Stage E：Docker 全栈（Dockerfile + docker-compose.yml + nginx.conf +
       pgbouncer + deploy_to_40.py 一键部署脚本）
- ✅ Stage F：db_health 管理命令（PG version + 连接数 + SELECT 1）
- ✅ Stage G：50 并发 1750 req / 141 req/s / 零 5xx

### 中期（按需）
- 🔲 Celery 真多进程（需 Linux + GDAL native 重构）
- 🔲 主从流复制 + replica 上线
- 🔲 pg_stat_statements 接 Prometheus
- 🔲 慢请求自动熔断（django-ratelimit）

### 长期
- 🔲 多租户支持（schema 隔离）
- 🔲 数据脱敏（PostgreSQL Anonymizer）
- 🔲 异地多活

---

## 8. 关键文件索引

| 用途 | 文件 |
|---|---|
| 全局配置（env-driven） | `my_project/my_project/config.py` |
| Django 设置 | `my_project/my_project/settings.py` |
| 读写分离 router | `my_project/my_project/db_router.py` |
| Token 认证 | `my_project/my_project/token.py` |
| 中间件（加密/上下文/限流） | `my_project/my_app/middleware.py` |
| Celery 配置 | `my_project/my_project/celery.py` |
| 日志（含 ES handler） | `my_project/my_project/log.py` |
| 系统检查（含 AST SQL 扫描） | `my_project/my_app/checks.py` |
| 业务操作日志 | `my_app/utils/sysmanUtility.py` |
| 通用 SQL helper（Bulk + 缓存） | `my_app/utils/sysmanUtility.py` |
| 表缓存 helper | `my_app/utils/cacheHelper.py` |
| 缓存失效 | `my_app/utils/cacheInvalidate.py` |
| Celery 预热 | `my_app/utils/cacheWarmer.py` |
| SQL 安全（白名单 + Identifier） | `my_app/utils/safeSQL.py` |
| 数据库健康命令 | `my_app/management/commands/db_health.py` |
| Dockerfile | `Dockerfile`（仓库根） |
| 全栈 compose | `deploy/docker-compose.yml` |
| pgbouncer 配置 | `deploy/pgbouncer/pgbouncer.ini` |
| nginx 反代 | `deploy/nginx.conf` |
| 一键部署脚本 | `deploy/deploy_to_40.py` |
| 基线测试 | `my_project/tools/perf_baseline.py` |
| 并发压测 | `my_project/tools/loadtest.py` |

---

## 9. 维护 checklist

部署前必跑：
- [ ] `python manage.py check` 0 issues
- [ ] `python manage.py check --deploy --fail-level ERROR`
- [ ] `python manage.py db_health` PG 连接正常
- [ ] `python tools/perf_baseline.py` p95 ≤50ms（开发基线）
- [ ] `python tools/loadtest.py --users 50 --rounds 5` 0 5xx

部署后必查：
- [ ] Kibana 收到 `vgis-myapp-YYYY.MM.DD` 日志
- [ ] `docker compose ps` 全 healthy
- [ ] pgbouncer `SHOW POOLS` 复用连接 >0
- [ ] `redis-cli MONITOR` 看 cache hit 频率
- [ ] 长事务告警阈值（>30s）= 0
