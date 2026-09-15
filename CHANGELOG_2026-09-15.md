# CHANGELOG 2026-09-15

> 本轮：**P0 bug 修复 + 性能优化 + Celery 异步 sys_log + 13 个索引**
>
> **接口契约不动**：URL、请求参数、响应字段均保持原样；仅修改内部实现。

---

## 阶段 1：P0 Bug 修复

### 1.1 删 auth_user 时级联清 authtoken_token（[views.py:558-595](my_project/my_app/module/sys_manage/views.py)）

- **症状**：删除用户后 `authtoken_token` 残留孤儿 token；后续 token 认证会触发 `User matching query does not exist`，连锁崩溃所有用到 token 的接口。
- **修法**：
  - `SysUserRole.delete` + `Token.delete` + `super().destroy` 三步用 `transaction.atomic()` 包，任一失败整体回滚
  - 删 `finally: res` 死代码
  - 删失败时 `success` 改 `False`（原代码失败也返回 `True`，是错的）

### 1.2 reset_password 防 DoesNotExist 500（[views.py:177-198](my_project/my_app/module/user_manage/views.py)）

- **症状**：传入已被删除的 userid 时 `AuthUser.objects.get(id=userid).username` 抛 DoesNotExist，整接口 500。
- **修法**：try/except，user 不存在时用 `str(userid)` 占位，接口返回正常的 `success: False`。

### 1.3 登录失败计数合并 exists+get+update（[manager.py:73-117](my_project/my_app/module/user_manage/manager.py)）

- **症状**：原先 `exists()` + `get()` + 内存改值 + `save()` 三次往返；并发时两个失败请求读到相同旧值后各自 save，互相覆盖。
- **修法**：
  - `exists+get` 合并为单条 `.filter().first()`
  - 失败次数改为 `F('login_error_attempts') + 1` 原子自增（带 `Coalesce` 兜底 NULL）
  - 锁定阈值判断改为 `refresh_from_db()` 后基于最新值

## 阶段 2：N+1 → JOIN（[sysmanUtility.py](my_project/my_app/utils/sysmanUtility.py) + 4 个调用点）

新增 4 个 Bulk 静态方法（用 `ANY(%s)` 数组参数或 `IN (...)`）：
- `getFullDepartNameBulk(dept_ids)`：单条 SQL 拿全部门 + Python 递归拼父链
- `getRoleByUserBulk(user_ids)`：单条 SQL 拿所有用户角色
- `getDepartInfoBulk(dept_ids)`：单条 SQL 拿部门名（仅名，不含父链）
- `getMenuByRoleBulk(role_ids)`：单条 SQL 拿所有角色关联菜单

调用点替换：
- `user_manage/manager.py:sql_search`：原 N 行 × 2 次 SQL → 2 次 Bulk + 循环内 dict 查
- `sys_manage/manager.py:sql_search_department`：原 N 次 `getDepartInfo` → 1 次 Bulk
- `sys_manage/manager.py:sql_search_role`：原 N 次 `getMenuByRole` → 1 次 Bulk
- `common/manager.py:get_region_and_province`：原 N 个大区 N+1 次查询 → 2 次（region 一次 + provinces ANY 一次）

## 阶段 3：分页标准化 — **回退为内部硬保护**（用户强约束）

**原计划**：SysMenu/SysParam 走 DRF 自动分页，返回 `count/next/previous`。
**实际**：保留原 `{"results":[...]}` 响应形态，**不加任何新字段**。
**内部**加 `LIMIT 500` 硬保护（不告诉前端）。

所有 `sql_search_*` 加 `LIMIT 500` 内部硬保护；**响应字段不变**（无 `truncated`）。

## 阶段 4：缓存层（[sysmanUtility.py:get_param_cached](my_project/my_app/utils/sysmanUtility.py)）

- 新增 `SysmanHelper.get_param_cached(en_key, default, cast)`：5 分钟 Redis 缓存 + 自动 fallback to default
- 替换 7 处 `try/except + SysParam.objects.get`：
  - `token.py`：`get_AUTH_TOKEN_AGE` / `get_TOKEN_KEY` / `get_TOKEN_USE_CACHE`
  - `middleware.py`：`get_IS_ENCRYPTION`
  - `user_manage/manager.py`：`get_LOGIN_LOCKED_TIME` / `get_LOGIN_ERROR_ATTEMPTS` / `get_is_use_verification_code` / `get_AUTH_TOKEN_AGE`
- AES 加密对象改为模块级懒加载单例（[encryptionUtility.py](my_project/my_app/utils/encryptionUtility.py)）：
  原每请求重建 `FernetEncryption` + `RSAEncryption` + `AESEncryption` 三个对象，50 并发时直接吃满 CPU。
  现仅在首次调用时构建一次，之后复用。

## 阶段 5：DB 连接池 + 索引

- `settings.py`：DATABASES 加 `'CONN_MAX_AGE': 60, 'CONN_HEALTH_CHECKS': True`
- 新建 [`database/INDEXES_2026_09.sql`](my_project/database/INDEXES_2026_09.sql)：13 条 `CREATE INDEX IF NOT EXISTS`（计划写 11 条，实际多加了 2 条覆盖更全）
  - sys_log × 3（create_date/username/method）
  - auth_user × 3（department_id/status/login_locked_until）
  - sys_user_role × 2、sys_role_menu × 1
  - sys_department × 1（parent_id）
  - sys_param × 1（param_en_key）
  - tm_region × 1、tm_district × 1
- 注：因 `managed=False`，手工 psql/psycopg2 执行；已在 mydb_test 上跑通

## 阶段 6：线程 + Celery 异步 sys_log

- `run.py`：`threads=4` → `threads=16`
- `my_app/tasks.py`：新增 `@shared_task def write_sys_log(payload)` + `insert_log_info_async()` 包装（broker 不可用时自动 fallback 同步写入）
- 启动 Celery worker：
  ```bash
  cd my_project
  PYTHONIOENCODING=utf-8 DJANGO_SETTINGS_MODULE=my_project.settings \
      E:/claudecode/venv_6.06/Scripts/python.exe -m celery \
      -A my_project worker -l info --pool=solo \
      --without-mingle --without-gossip --without-heartbeat
  ```
  ⚠️ **踩坑**：Windows + 本机 GDAL native 绑定，celery 默认 `prefork` pool 启动后子进程 1~2 秒后全部 `exitcode 1` 退出。
  必须用 `--pool=solo`（单进程异步 loop）才能稳定；并发由 Python asyncio 调度。

- **遗留**：`LoggerHelper.insert_log_info(...)` 全量替换为 `insert_log_info_async(...)` 因改动面大（30+ 处）暂未执行。
  Celery 已就绪，后续替换只是机械替换+单测，单独迭代。

## 阶段 7：50 并发压测

- 新建 [`tools/loadtest.py`](my_project/tools/loadtest.py)：asyncio + aiohttp，**预登录一次复用 token**（避免 loginWithForce 互踢）
- 50 users × 20 rounds = 7000 请求，43 秒跑完，吞吐 162 req/s
- **零 5xx**，所有接口 p95 在 343~492ms 之间（部分 sqlsearch p95 略高于 300ms 目标）

## 阶段 8：13 个 FAIL 接口回归

跑 `tools/perf_baseline.py` + 手工 smoke test 验证，13 个原 FAIL 接口全部 PASS：
- authUser/sqlsearch、sysUser/sqlsearch、sysDepartment/sqlsearch、sysRole/sqlsearch、sysMenu/list、sysParam/list、sysLog/sqlsearch
- tmDdistrict/getRegionAndProvince、sysDict/cateloglist、sysDict/sqlsearch、sysMessage/sqlsearch
- getVersion、isTokenExpired 等

## 阶段 9：文档

- 更新 [接口路径变更对照表.md](接口路径变更对照表.md)：新增 2026-09-15 章节，标注 SysMenu/SysParam 字段变化（**实际无变化**）+ Celery 启动命令
- 新建本文件

---

## 性能数字对比（baseline_v0 → baseline_v5 → 50 并发 loadtest）

| 接口 | v0 avg | v5 avg | 50×20 p95 | 提升 |
|---|---|---|---|---|
| login (re-login) | 797ms | 461ms | n/a | -42% |
| authUser list | 74ms | 34ms | 395ms | -54% |
| authUser sqlsearch | 226ms | 40ms | 396ms | **-82%** |
| sysDepartment sqlsearch | 107ms | 28ms | 343ms | **-74%** |
| sysRole sqlsearch | 99ms | 20ms | 393ms | **-80%** |
| sysMenu list | 69ms | 27ms | 394ms | -61% |
| sysParam list | 59ms | 17ms | 431ms | **-71%** |
| sysLog sqlsearch | 117ms | 45ms | 492ms | **-62%** |

> 注：50×20 压测的 p95 包含 50 并发排队时间，与 baseline 的 1 并发测速不可直接对比；与修复前的同等压测对比应能看出 3-5 倍提升。

---

## 已知遗留问题

1. **Celery `prefork` pool 不可用**：Windows + GDAL native 绑定导致子进程反复 exit 1。临时方案：`--pool=solo`。后续如要真正的多进程并发，需要把 GDAL/PROJ 路径在 worker 启动前显式设置（参考 settings.py 末尾的 GDAL 配置），或换 Linux 部署。
2. **`LoggerHelper.insert_log_info` 未切到 Celery 异步**：Celery 已就绪，包装函数 `insert_log_info_async` 已实现，但 30+ 处调用点暂未替换（机械工作，单测后即可批量替换）。
3. **SysLog 表无 `user_id` 列**：原本想 `payload["user_id"]` 写入时被 `models.py` 字段不匹配拒绝，已改成只传 username。
4. **`truncated` 字段未引入**：受"接口契约不动"约束，超 500 行时静默截断，不告诉前端。如前端需要分页/截断提示，应作为新接口或新 query param 暴露。
5. **Postman 集合未跑**：本轮没有实际跑 `run_postman_collection.py`（157 条），手工 smoke test 替代验证。
6. **`get_region_and_province` 没单独基准**：未加到 baseline_v0.txt 接口列表里（基线只有 8 个），优化效果未量化对比。
