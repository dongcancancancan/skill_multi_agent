#!/bin/bash

# 导出离线镜像包脚本
# 使用说明：
# 1. 在有网环境构建镜像
# 2. 运行此脚本导出镜像包
# 3. 将镜像包传输到内网服务器部署

set -e

echo "=== 多智能体金融分析平台离线镜像导出脚本 ==="
echo ""

# 1. 构建镜像
echo "1. 构建镜像..."
docker build -t financial-agent-pg:latest .

# 2. 导出镜像
echo "2. 导出镜像到 financial-agent-pg.tar..."
docker save -o financial-agent-pg.tar financial-agent-pg:latest

# 3. 计算文件大小
FILE_SIZE=$(du -h financial-agent-pg.tar | cut -f1)
echo "3. 镜像包大小: $FILE_SIZE"

echo ""
echo "=== 导出完成 ==="
echo "镜像文件: financial-agent-pg.tar"
echo ""
echo "=== 内网部署步骤 ==="
echo "1. 将 financial-agent-pg.tar 上传到内网服务器"
echo "2. 在内网服务器执行以下命令："
echo ""
echo "   # 导入镜像"
echo "   docker load -i financial-agent-pg.tar"
echo ""
echo "   # 启动容器（使用 host 网络模式）"
echo "   docker run -d \\"
echo "     --name financial-agent \\"
echo "     --network host \\"
echo "     -e DB_HOST=127.0.0.1 \\"
echo "     -e DB_PORT=5432 \\"
echo "     -e DB_USER=your_pg_user \\"
echo "     -e DB_PASSWORD=your_pg_password \\"
echo "     -e DB_NAME=your_pg_db_name \\"
echo "     financial-agent-pg:latest"
echo ""
echo "   # 或者使用端口映射模式（如果不能使用 host 模式）"
echo "   docker run -d \\"
echo "     --name financial-agent \\"
echo "     -p 8080:80 \\"
echo "     -e DB_HOST=192.168.x.x \\"
echo "     -e DB_PORT=5432 \\"
echo "     -e DB_USER=your_pg_user \\"
echo "     -e DB_PASSWORD=your_pg_password \\"
echo "     -e DB_NAME=your_pg_db_name \\"
echo "     financial-agent-pg:latest"
echo ""
echo "3. 访问应用："
echo "   - 前端界面: http://服务器IP:8080"
echo "   - API文档: http://服务器IP:8080/api/docs"
