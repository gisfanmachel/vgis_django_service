-- ----------------------------
-- Table structure for tb_user
-- ----------------------------
DROP SEQUENCE IF EXISTS "public"."tt_satellite_indicator_id_seq";
CREATE SEQUENCE "public"."tt_satellite_indicator_id_seq"
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;
DROP TABLE IF EXISTS "public"."tt_satellite_indicator";
CREATE TABLE "public"."tt_satellite_indicator" (
  "id" int8 NOT NULL DEFAULT nextval('tt_satellite_indicator_id_seq'::regclass),
  "create_user_id" int8,
  "create_time" timestamp(6) DEFAULT NULL,
  "modify_user_id" int8,
  "modify_time" timestamp(6),
  "indicator_id" int8 NOT NULL,
  "parent_id" int8,
  "indicator_name" varchar(255),
  "indicator_desc" text,
  "order_num" int4,
  "is_show" varchar(1)
);
ALTER TABLE "tt_satellite_indicator" OWNER TO "postgres";
COMMENT ON COLUMN "tt_satellite_indicator"."id" IS '业务主键ID';
COMMENT ON COLUMN "tt_satellite_indicator"."create_user_id" IS '创建人';
COMMENT ON COLUMN "tt_satellite_indicator"."create_time" IS '创建时间';
COMMENT ON COLUMN "tt_satellite_indicator"."modify_user_id" IS '更新人';
COMMENT ON COLUMN "tt_satellite_indicator"."modify_time" IS '修改时间';
COMMENT ON COLUMN "tt_satellite_indicator"."indicator_id" IS '指标ID';
COMMENT ON COLUMN "tt_satellite_indicator"."parent_id" IS '父指标ID';
COMMENT ON COLUMN "tt_satellite_indicator"."indicator_name" IS '指标名称';
COMMENT ON COLUMN "tt_satellite_indicator"."indicator_desc" IS '指标描述';
COMMENT ON COLUMN "tt_satellite_indicator"."order_num" IS '指标排序';
COMMENT ON COLUMN "tt_satellite_indicator"."is_show" IS '是否显示';
COMMENT ON TABLE "tt_satellite_indicator" IS '卫星保险指标表';



DROP SEQUENCE IF EXISTS "public"."tt_satellite_info_id_seq";
CREATE SEQUENCE "public"."tt_satellite_info_id_seq"
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;
DROP TABLE IF EXISTS "public"."tt_satellite_info";
CREATE TABLE "public"."tt_satellite_info" (
  "id" int8 NOT NULL DEFAULT nextval('tt_satellite_info_id_seq'::regclass),
  "satellite_cname" varchar(255) COLLATE "pg_catalog"."default",
  "satellite_type" varchar(255) COLLATE "pg_catalog"."default",
  "manufacturer" varchar(255) COLLATE "pg_catalog"."default",
  "satellite_platform" varchar(255) COLLATE "pg_catalog"."default",
  "whole_star_mass" varchar(255) COLLATE "pg_catalog"."default",
  "create_user_id" int8,
  "create_time" timestamp(6) DEFAULT NULL,
  "modify_user_id" int8,
  "modify_time" timestamp(6),
  "whole_star_lifetime" varchar(255) COLLATE "pg_catalog"."default",
  "carrier_rocket" varchar(255) COLLATE "pg_catalog"."default",
  "transmission_time" varchar(255) COLLATE "pg_catalog"."default",
  "track_type" varchar(255) COLLATE "pg_catalog"."default",
  "track_height" varchar(255) COLLATE "pg_catalog"."default",
  "track_semi_major_axis" varchar(255) COLLATE "pg_catalog"."default",
  "track_angle" varchar(255) COLLATE "pg_catalog"."default",
  "satellite_ename" varchar(255) COLLATE "pg_catalog"."default"
);
ALTER TABLE "tt_satellite_info" OWNER TO "postgres";
COMMENT ON COLUMN "tt_satellite_info"."id" IS '业务主键ID';
COMMENT ON COLUMN "tt_satellite_info"."satellite_cname" IS '卫星中文名称';
COMMENT ON COLUMN "tt_satellite_info"."satellite_type" IS '卫星分类';
COMMENT ON COLUMN "tt_satellite_info"."manufacturer" IS '制造商';
COMMENT ON COLUMN "tt_satellite_info"."satellite_platform" IS '卫星平台';
COMMENT ON COLUMN "tt_satellite_info"."whole_star_mass" IS '整星质量(kg)';
COMMENT ON COLUMN "tt_satellite_info"."create_user_id" IS '创建人';
COMMENT ON COLUMN "tt_satellite_info"."create_time" IS '创建时间';
COMMENT ON COLUMN "tt_satellite_info"."modify_user_id" IS '更新人';
COMMENT ON COLUMN "tt_satellite_info"."modify_time" IS '修改时间';
COMMENT ON COLUMN "tt_satellite_info"."whole_star_lifetime" IS '整星寿命';
COMMENT ON COLUMN "tt_satellite_info"."carrier_rocket" IS '运载火箭';
COMMENT ON COLUMN "tt_satellite_info"."transmission_time" IS '发射时间';
COMMENT ON COLUMN "tt_satellite_info"."track_type" IS '轨道类型';
COMMENT ON COLUMN "tt_satellite_info"."track_height" IS '轨道高度';
COMMENT ON COLUMN "tt_satellite_info"."track_semi_major_axis" IS '轨道半长轴';
COMMENT ON COLUMN "tt_satellite_info"."track_angle" IS '轨道倾角';
COMMENT ON COLUMN "tt_satellite_info"."satellite_ename" IS '卫星英文名称';
COMMENT ON TABLE "tt_satellite_info" IS '卫星基础信息表';



DROP SEQUENCE IF EXISTS "public"."tt_satellite_policy_id_seq";
CREATE SEQUENCE "public"."tt_satellite_policy_id_seq"
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;
DROP TABLE IF EXISTS "public"."tt_satellite_policy";
CREATE TABLE "public"."tt_satellite_policy" (
  "id" int8 NOT NULL DEFAULT nextval('tt_satellite_policy_id_seq'::regclass),
  "sub_insurance_policy_number" varchar(255) COLLATE "pg_catalog"."default",
  "satellite_id" int8,
  "satellite_indicator_id" int8,
  "policy_design_indicator_value" varchar(255) COLLATE "pg_catalog"."default",
  "policy_constructive_total_loss_value" varchar(255) COLLATE "pg_catalog"."default",
  "create_user_id" int8,
  "create_time" timestamp(6) DEFAULT NULL,
  "modify_user_id" int8,
  "modify_time" timestamp(6)
);
ALTER TABLE "tt_satellite_policy" OWNER TO "postgres";
COMMENT ON COLUMN "tt_satellite_policy"."id" IS '业务主键ID';
COMMENT ON COLUMN "tt_satellite_policy"."sub_insurance_policy_number" IS '投保单号';
COMMENT ON COLUMN "tt_satellite_policy"."satellite_id" IS '卫星编号';
COMMENT ON COLUMN "tt_satellite_policy"."satellite_indicator_id" IS '卫星指标编号';
COMMENT ON COLUMN "tt_satellite_policy"."policy design_indicator_value" IS '保单设计指标值';
COMMENT ON COLUMN "tt_satellite_policy"."policy_constructive_total_loss_value" IS '保单推定全损值';
COMMENT ON COLUMN "tt_satellite_policy"."create_user_id" IS '创建人';
COMMENT ON COLUMN "tt_satellite_policy"."create_time" IS '创建时间';
COMMENT ON COLUMN "tt_satellite_policy"."modify_user_id" IS '更新人';
COMMENT ON COLUMN "tt_satellite_policy"."modify_time" IS '修改时间';
COMMENT ON TABLE "tt_satellite_policy" IS '卫星保单信息表';

