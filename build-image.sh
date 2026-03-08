#!/bin/bash

# 构建脚本：构建并导出离线镜像包

set -e

# 镜像名称和标签
IMAGE_NAME="financial-agent-pg"
IMAGE_TAG="v1"
OUTPUT_FILE="${IMAGE_NAME}-${IMAGE_TAG}.tar"

echo "=== 开始构建多智能体金融助手镜像 ==="

# 1. 构建 Docker 镜像
echo "步骤1: 构建 Docker 镜像..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

if [ $? -eq 0 ]; then
    echo "✓ 镜像构建成功: ${IMAGE_NAME}:${IMAGE_TAG}"
else
    echo "✗ 镜像构建失败"
    exit 1
fi

# 2. 导出为离线包
echo "步骤2: 导出为离线镜像包..."
docker save -o ${OUTPUT_FILE} ${IMAGE_NAME}:${IMAGE_TAG}

if [ $? -eq 0 ]; then
    echo "✓ 镜像导出成功: ${OUTPUT_FILE}"
    echo "文件大小: $(du -h ${OUTPUT_FILE} | cut -f1)"
else
    echo "✗ 镜像导出失败"
    exit 1
fi

# 3. 创建部署说明文件
echo "步骤3: 创建部署说明..."
cat > DEPLOYMENT.md << 'EOF'
# 多智能体金融助手离线部署指南

## 镜像信息
- 镜像名称: financial-agent-pg:v1
- 导出文件: financial-agent-pg-v1.tar
- 构建时间: $(date)

## 部署步骤

### 1. 在内网服务器导入镜像
```bash
# 导入镜像
docker load -i financial-agent-pg-v1.tar

# 验证镜像
docker images | grep financial-agent-pg
```

### 2. 准备数据库环境
确保服务器上已有 PostgreSQL 数据库，并创建相应的数据库和用户。

### 3. 启动容器

#### 方案A：使用 Host 网络模式（推荐，Linux 系统）
```bash
docker run -d \
  --name agent-system \
  --network host \
  -e DB_HOST=127.0.0.1 \
  -e DB_PORT=5432 \
  -e DB_USER=your_pg_user \
  -e DB_PASSWORD=your_pg_password \
  -e DB_NAME=your_pg_db_name \
  financial-agent-pg:v1
```

#### 方案B：使用端口映射模式
```bash
docker run -d \
  --name agent-system \
  -p 8080:80 \
  -e DB_HOST=192.168.x.x \  # 宿主机IP
  -e DB_PORT=5432 \
  -e DB_USER=your_pg_user \
  -e DB_PASSWORD=your_pg_password \
  -e DB_NAME=your_pg_db_name \
  financial-agent-pg:v1
```

### 4. 验证服务
```bash
# 查看容器状态
docker ps | grep agent-system

# 查看日志
docker logs agent-system

# 测试服务
curl http://localhost:8080/  # 或使用浏览器访问
```

### 5. 环境变量说明

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| DB_HOST | PostgreSQL 主机地址 | 127.0.0.1 |
| DB_PORT | PostgreSQL 端口 | 5432 |
| DB_USER | 数据库用户名 | postgres |
| DB_PASSWORD | 数据库密码 | your_password |
| DB_NAME | 数据库名称 | multi_agent |

### 6. 常用管理命令
```bash
# 停止容器
docker stop agent-system

# 启动容器
docker start agent-system

# 重启容器
docker restart agent-system

# 进入容器
docker exec -it agent-system bash

# 查看日志
docker logs -f agent-system
```

## 注意事项

1. **数据库连接**：确保容器能访问到 PostgreSQL 数据库
2. **端口冲突**：如果使用 Host 模式，确保 80 端口未被占用
3. **文件权限**：确保日志文件目录有写入权限
4. **资源限制**：根据实际情况调整容器资源限制

## 故障排查

1. **容器启动失败**：查看日志 `docker logs agent-system`
2. **数据库连接失败**：检查环境变量和网络连接
3. **服务无法访问**：检查端口映射和防火墙设置
EOF

echo "✓ 部署说明创建成功: DEPLOYMENT.md"

echo ""
echo "=== 构建完成 ==="
echo "1. 镜像文件: ${OUTPUT_FILE}"
echo "2. 部署说明: DEPLOYMENT.md"
echo "3. 下一步: 将以上文件复制到内网服务器进行部署"
