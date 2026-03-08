# Docker 配置详解

## 📋 配置概述

本项目使用 Docker Compose 编排两个核心数据服务：**MySQL** 和 **Redis**，为多智能体金融助手提供数据存储和缓存支持。

## 🗂️ 文件结构

```
deploy/docker/
├── docker-compose.yml    # Docker 编排配置文件
├── docker-setup.sh       # 一键启动脚本
├── env.template          # 环境变量模板
├── redis/
│   └── redis.conf        # Redis 自定义配置
└── README.md            # 本说明文档
```

## 🔧 Docker Compose 配置详解

### 1. 文件头部配置

```yaml
version: '3.8'
```
- **作用**: 指定 Docker Compose 文件格式版本
- **说明**: 3.8 版本支持健康检查、profiles 等高级功能

### 2. MySQL 服务配置

#### 基础配置
```yaml
mysql:
  image: mysql:8.0
  container_name: multi-agent-mysql
  restart: unless-stopped
```

- **image**: 使用官方 MySQL 8.0 镜像，稳定且功能完整
- **container_name**: 固定容器名称，便于管理和连接
- **restart**: 重启策略，除非手动停止，否则总是重启

#### 环境变量配置
```yaml
environment:
  MYSQL_ROOT_PASSWORD: Password
  MYSQL_DATABASE: multi_agent
  MYSQL_USER: multi_agent_user
  MYSQL_PASSWORD: Password
  MYSQL_CHARSET: utf8mb4
  MYSQL_COLLATION: utf8mb4_unicode_ci
```

| 环境变量 | 作用 | 说明 |
|---------|------|------|
| MYSQL_ROOT_PASSWORD | root 用户密码 | 数据库管理员密码 |
| MYSQL_DATABASE | 自动创建的数据库 | 项目主数据库名 |
| MYSQL_USER | 普通用户名 | 应用程序连接用户 |
| MYSQL_PASSWORD | 普通用户密码 | 应用程序连接密码 |
| MYSQL_CHARSET | 字符集 | utf8mb4 支持中文和 emoji |
| MYSQL_COLLATION | 排序规则 | 统一编码标准 |

#### 端口和数据卷
```yaml
ports:
  - "3306:3306"
volumes:
  - mysql_data:/var/lib/mysql
  - ../../scripts/sql:/docker-entrypoint-initdb.d/
```

- **端口映射**: 宿主机 3306 端口映射到容器 3306 端口
- **数据持久化**: `mysql_data` 卷存储数据库文件，容器删除后数据不丢失
- **初始化脚本**: `scripts/sql` 目录下的 SQL 文件会在首次启动时自动执行

#### 启动参数优化
```yaml
command: >
  --default-authentication-plugin=mysql_native_password
  --character-set-server=utf8mb4
  --collation-server=utf8mb4_unicode_ci
  --sql_mode=STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO
  --max_connections=200
  --innodb_buffer_pool_size=256M
```

| 参数 | 作用 | 说明 |
|------|------|------|
| default-authentication-plugin | 认证插件 | 兼容旧版客户端 |
| character-set-server | 服务器字符集 | 确保中文支持 |
| sql_mode | SQL 模式 | 严格模式，提高数据质量 |
| max_connections | 最大连接数 | 支持 200 个并发连接 |
| innodb_buffer_pool_size | 缓冲池大小 | 256MB 内存缓存，提升性能 |

#### 健康检查
```yaml
healthcheck:
  test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-pPassword"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

- **作用**: 检测 MySQL 服务是否正常运行
- **检查方式**: 使用 mysqladmin ping 命令
- **检查频率**: 每 10 秒检查一次
- **启动等待**: 启动后等待 30 秒再开始检查

### 3. Redis 服务配置

#### 基础配置
```yaml
redis:
  image: redis:7-alpine
  container_name: multi-agent-redis
  restart: unless-stopped
```

- **image**: 使用 Alpine 版本，体积小、安全性高
- **版本**: Redis 7.x 最新稳定版

#### 端口和数据卷
```yaml
ports:
  - "6379:6379"
volumes:
  - redis_data:/data
  - ./redis/redis.conf:/etc/redis/redis.conf
command: redis-server /etc/redis/redis.conf
```

- **端口映射**: 标准 Redis 端口 6379
- **数据持久化**: RDB 和 AOF 双重持久化
- **自定义配置**: 使用本地 redis.conf 配置文件

#### Redis 配置文件解析（redis/redis.conf）

```ini
# 基础配置
bind 0.0.0.0          # 允许所有IP连接（Docker内部网络）
port 6379             # 默认端口
protected-mode no     # 关闭保护模式（Docker环境安全）

# 数据持久化
save 900 1            # 900秒内有1个写操作就保存
save 300 10           # 300秒内有10个写操作就保存  
save 60 10000         # 60秒内有10000个写操作就保存

# AOF 持久化
appendonly yes        # 启用AOF持久化
appendfilename "appendonly.aof"
appendfsync everysec  # 每秒同步一次

# 内存管理
maxmemory 512mb       # 最大内存限制
maxmemory-policy allkeys-lru  # LRU淘汰策略
```

### 4. 管理界面服务（可选）

#### profiles 机制
```yaml
profiles:
  - management
```
- **作用**: 分组管理，只有指定 profile 时才启动
- **启动方式**: `docker-compose --profile management up -d`

#### phpMyAdmin 配置
```yaml
phpmyadmin:
  image: phpmyadmin/phpmyadmin:latest
  environment:
    PMA_HOST: mysql
    PMA_PORT: 3306
  ports:
    - "8080:80"
  depends_on:
    mysql:
      condition: service_healthy
```

- **依赖关系**: 等待 MySQL 健康检查通过后启动
- **访问地址**: http://localhost:8080
- **自动连接**: 无需手动配置数据库连接

#### Redis Commander 配置
```yaml
redis-commander:
  environment:
    REDIS_HOSTS: "local:redis:6379"
  ports:
    - "8081:8081"
```

- **连接配置**: 自动连接到 redis 服务
- **访问地址**: http://localhost:8081

### 5. 网络配置

```yaml
networks:
  multi-agent-network:
    driver: bridge
    name: multi-agent-network
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16
```

- **网络类型**: 桥接网络，容器间可直接通过服务名通信
- **子网配置**: 自定义IP段，避免与宿主机网络冲突
- **服务发现**: 容器可通过服务名（如 `mysql`、`redis`）互相访问

### 6. 数据卷配置

```yaml
volumes:
  mysql_data:
    name: multi-agent-mysql-data
    driver: local
  redis_data:
    name: multi-agent-redis-data
    driver: local
```

- **存储位置**: Docker 管理的本地存储
- **数据安全**: 容器删除后数据仍然保留
- **备份**: 可通过 `docker volume` 命令管理

## 🚀 使用指南

### 1. 快速启动
```bash
# 进入 Docker 目录
cd deploy/docker

# 一键启动核心服务
./docker-setup.sh

# 或手动启动
docker-compose up -d mysql redis
```

### 2. 启动管理界面
```bash
# 启动所有服务包括管理界面
docker-compose --profile management up -d

# 或选择性启动管理界面
docker-compose up -d phpmyadmin redis-commander
```

### 3. 常用管理命令
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f mysql
docker-compose logs -f redis

# 停止服务
docker-compose down

# 重启服务
docker-compose restart mysql

# 进入容器
docker-compose exec mysql bash
docker-compose exec redis redis-cli
```

### 4. 数据管理
```bash
# 备份 MySQL 数据
docker-compose exec mysql mysqldump -uroot -pPassword multi_agent > backup.sql

# 查看数据卷
docker volume ls | grep multi-agent

# 清理数据（谨慎操作）
docker-compose down -v
```

## 🔧 自定义配置

### 修改端口
如果默认端口冲突，可修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "13306:3306"  # MySQL 改为 13306
  - "16379:6379"  # Redis 改为 16379
```

### 调整内存限制
```yaml
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M
```

### 修改密码
生产环境建议修改默认密码：
```yaml
environment:
  MYSQL_ROOT_PASSWORD: your_secure_password
```

## 📊 性能监控

### 查看资源使用
```bash
# 查看容器资源使用情况
docker stats multi-agent-mysql multi-agent-redis

# 查看详细信息
docker-compose exec mysql mysqladmin -uroot -pPassword status
docker-compose exec redis redis-cli info memory
```

### 性能调优建议

1. **MySQL 优化**
   - 根据数据量调整 `innodb_buffer_pool_size`
   - 监控慢查询日志
   - 合理设置 `max_connections`

2. **Redis 优化**
   - 根据使用情况调整 `maxmemory`
   - 选择合适的淘汰策略
   - 开启合适的持久化机制

## ⚠️ 注意事项

1. **安全提醒**
   - 生产环境请修改默认密码
   - 考虑启用 Redis 密码认证
   - 限制网络访问范围

2. **数据备份**
   - 定期备份重要数据
   - 测试恢复流程
   - 监控磁盘空间

3. **资源监控**
   - 监控内存使用情况
   - 注意磁盘空间消耗
   - 定期清理日志文件

---

*此配置已针对开发和测试环境优化，生产环境使用前请进行相应的安全加固和性能调优。*
