-- GIS_TABLES_2026_09.sql
-- gis_service 模块的两张状态表（tt_gis_task / tt_gis_layer）
--
-- 用法：
--   1) my_app/module/gis_service/models.py 里两个表都 managed = False，
--      migrate 不会建表，必须手工 psql 执行本文件
--   2) CREATE TABLE IF NOT EXISTS 可重复执行
--   3) 字段顺序固定，新增字段一律尾部追加，不要在中间插，避免 PostgreSQL 8.4 之前的
--      "column does not exist" 风险
--
-- 说明：
--   tt_gis_task：Celery 异步任务的状态表（PMTiles / COG / STAC ingest）
--                task_id 用 celery.AsyncResult.task_id 字符串做去重
--   tt_gis_layer：vector 表注册表（vector/load 灌入的 PostGIS 表元信息）

-- ===== tt_gis_task =====
CREATE TABLE IF NOT EXISTS tt_gis_task (
    id            SERIAL PRIMARY KEY,
    task_id       VARCHAR(64) UNIQUE NOT NULL,
    task_type     VARCHAR(32) NOT NULL,
    status        VARCHAR(16) NOT NULL,
    payload       JSONB,
    result        JSONB,
    current_step  VARCHAR(64),
    error         TEXT,
    create_time   TIMESTAMP DEFAULT NOW(),
    update_time   TIMESTAMP DEFAULT NOW(),
    create_user_id INTEGER
);

-- tt_gis_task 的高频索引
-- pm/list / cog/list / stac/list 都要按 task_type 过滤
CREATE INDEX IF NOT EXISTS idx_tt_gis_task_task_type ON tt_gis_task (task_type);
-- 状态过滤（running / success / failure）
CREATE INDEX IF NOT EXISTS idx_tt_gis_task_status ON tt_gis_task (status);
-- 按时倒序
CREATE INDEX IF NOT EXISTS idx_tt_gis_task_create_time ON tt_gis_task (create_time DESC);

-- ===== tt_gis_layer =====
CREATE TABLE IF NOT EXISTS tt_gis_layer (
    table_name     VARCHAR(64) PRIMARY KEY,
    layer_name     VARCHAR(64) NOT NULL,
    geometry_type  VARCHAR(32),
    srid           INTEGER DEFAULT 4326,
    feature_count  INTEGER DEFAULT 0,
    bbox           VARCHAR(128),
    has_index      BOOLEAN DEFAULT FALSE,
    create_time    TIMESTAMP DEFAULT NOW(),
    create_user_id INTEGER
);