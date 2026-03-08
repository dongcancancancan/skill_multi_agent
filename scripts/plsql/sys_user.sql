CREATE TABLE "public"."sys_user" (
  "id" varchar(64) COLLATE "pg_catalog"."default" NOT NULL,
  "username" varchar(50) COLLATE "pg_catalog"."default",
  "email" varchar(100) COLLATE "pg_catalog"."default",
  "phone" varchar(20) COLLATE "pg_catalog"."default",
  "password_hash" varchar(255) COLLATE "pg_catalog"."default",
  "salt" varchar(50) COLLATE "pg_catalog"."default",
  "real_name" varchar(100) COLLATE "pg_catalog"."default",
  "nick_name" varchar(100) COLLATE "pg_catalog"."default",
  "avatar_url" varchar(500) COLLATE "pg_catalog"."default",
  "gender" int2,
  "birthday" date,
  "version" int4 NOT NULL DEFAULT 1,
  "create_by" varchar(20) COLLATE "pg_catalog"."default",
  "create_time" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
  "update_by" varchar(20) COLLATE "pg_catalog"."default",
  "update_time" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
  "remark" varchar(500) COLLATE "pg_catalog"."default",
  "del_flag" int2,
  CONSTRAINT "sys_user_pkey" PRIMARY KEY ("id")
)
;

ALTER TABLE "public"."sys_user" 
  OWNER TO "root";

COMMENT ON COLUMN "public"."sys_user"."id" IS '主键ID';

COMMENT ON COLUMN "public"."sys_user"."username" IS '用户名';

COMMENT ON COLUMN "public"."sys_user"."email" IS '邮箱';

COMMENT ON COLUMN "public"."sys_user"."phone" IS '手机号';

COMMENT ON COLUMN "public"."sys_user"."password_hash" IS '密码哈希';

COMMENT ON COLUMN "public"."sys_user"."salt" IS '密码盐值';

COMMENT ON COLUMN "public"."sys_user"."real_name" IS '真实姓名';

COMMENT ON COLUMN "public"."sys_user"."nick_name" IS '昵称';

COMMENT ON COLUMN "public"."sys_user"."avatar_url" IS '头像URL';

COMMENT ON COLUMN "public"."sys_user"."gender" IS '性别: 0-未知, 1-男, 2-女';

COMMENT ON COLUMN "public"."sys_user"."birthday" IS '生日';

COMMENT ON COLUMN "public"."sys_user"."version" IS '版本号(用于乐观锁)';

COMMENT ON COLUMN "public"."sys_user"."create_by" IS '创建人ID';

COMMENT ON COLUMN "public"."sys_user"."create_time" IS '创建时间';

COMMENT ON COLUMN "public"."sys_user"."update_by" IS '更新人ID';

COMMENT ON COLUMN "public"."sys_user"."update_time" IS '更新时间';

COMMENT ON COLUMN "public"."sys_user"."remark" IS '备注';

COMMENT ON COLUMN "public"."sys_user"."del_flag" IS '0否1是';

COMMENT ON TABLE "public"."sys_user" IS '系统用户表';