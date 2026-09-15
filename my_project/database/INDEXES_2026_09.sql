-- INDEXES_2026_09.sql
-- 阶段 5：在 mydb_test 上为热表加索引
--
-- 注意：
--   1) my_app/models.py 里所有表 managed = False，migrate 不会建索引，
--      必须手工 psql 执行本文件。
--   2) 全部使用 CREATE INDEX IF NOT EXISTS，可重复执行不会报错。
--   3) 大表建索引时会持锁；执行前请在低峰期跑，并确认无慢查询。

-- ===== sys_log =====
-- sysLog.sqlsearch 按 create_date DESC 排序 + 时间范围查询
CREATE INDEX IF NOT EXISTS idx_sys_log_create_date ON sys_log (create_date DESC);
-- sysLog.sqlsearch 按 username 模糊匹配
CREATE INDEX IF NOT EXISTS idx_sys_log_username ON sys_log (username);
-- sysLog.sqlsearch 按 method 过滤
CREATE INDEX IF NOT EXISTS idx_sys_log_method ON sys_log (method);

-- ===== auth_user =====
-- 用户列表/部门树关联查询
CREATE INDEX IF NOT EXISTS idx_auth_user_department_id ON auth_user (department_id);
-- 用户列表按 status 过滤
CREATE INDEX IF NOT EXISTS idx_auth_user_status ON auth_user (status);
-- 登录锁定检查按 login_locked_until
CREATE INDEX IF NOT EXISTS idx_auth_user_login_locked_until ON auth_user (login_locked_until);

-- ===== sys_user_role / sys_role_menu =====
-- sysUserRole 反查 user_id 的角色
CREATE INDEX IF NOT EXISTS idx_sys_user_role_user_id ON sys_user_role (user_id);
-- sysUserRole 反查 role_id 的用户
CREATE INDEX IF NOT EXISTS idx_sys_user_role_role_id ON sys_user_role (role_id);
-- sysRoleMenu 反查 role_id 的菜单
CREATE INDEX IF NOT EXISTS idx_sys_role_menu_role_id ON sys_role_menu (role_id);

-- ===== sys_department =====
-- 部门列表按 parent_id 递归
CREATE INDEX IF NOT EXISTS idx_sys_department_parent_id ON sys_department (parent_id);

-- ===== sys_param =====
-- SysParam 按 en_key 查询（5 分钟缓存后兜底也是这个）
CREATE INDEX IF NOT EXISTS idx_sys_param_en_key ON sys_param (param_en_key);

-- ===== tm_region / tm_district =====
-- getRegionAndProvince 按 region_code 查省份
CREATE INDEX IF NOT EXISTS idx_tm_region_region_code ON tm_region (region_code);
-- getCityByProvince / getCountyByCity 按 parent_code
CREATE INDEX IF NOT EXISTS idx_tm_district_parent_code ON tm_district (parent_code);
