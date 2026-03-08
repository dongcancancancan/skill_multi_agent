CREATE TABLE "public"."session_history" (
  "id" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "user_id" varchar(50) COLLATE "pg_catalog"."default",
  "version" int4 NOT NULL DEFAULT 1,
  "create_by" varchar(20) COLLATE "pg_catalog"."default",
  "create_time" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
  "update_by" varchar(20) COLLATE "pg_catalog"."default",
  "update_time" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
  "remark" varchar(500) COLLATE "pg_catalog"."default",
  "query" varchar(1024) COLLATE "pg_catalog"."default",
  "answer" varchar(1024) COLLATE "pg_catalog"."default",
  "windows_no" varchar(128) COLLATE "pg_catalog"."default",
  "del_flag" int2,
  CONSTRAINT "session_history_pkey" PRIMARY KEY ("id")
)
;

ALTER TABLE "public"."session_history" 
  OWNER TO "root";

COMMENT ON COLUMN "public"."session_history"."id" IS '主键ID';

COMMENT ON COLUMN "public"."session_history"."user_id" IS '用户id';

COMMENT ON COLUMN "public"."session_history"."version" IS '版本号(用于乐观锁)';

COMMENT ON COLUMN "public"."session_history"."create_by" IS '创建人ID';

COMMENT ON COLUMN "public"."session_history"."create_time" IS '创建时间';

COMMENT ON COLUMN "public"."session_history"."update_by" IS '更新人ID';

COMMENT ON COLUMN "public"."session_history"."update_time" IS '更新时间';

COMMENT ON COLUMN "public"."session_history"."remark" IS '备注';

COMMENT ON COLUMN "public"."session_history"."query" IS '用户输入';

COMMENT ON COLUMN "public"."session_history"."answer" IS '智能体输出';

COMMENT ON COLUMN "public"."session_history"."windows_no" IS '窗口序号';

COMMENT ON COLUMN "public"."session_history"."del_flag" IS '0否1是';

COMMENT ON TABLE "public"."session_history" IS '历史会话表';