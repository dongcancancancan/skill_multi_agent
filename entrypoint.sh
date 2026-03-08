#!/bin/bash

# 1. 启动挡板服务 (Mock Server) - 后台运行
# 作用：模拟外部金融接口，供后端调用
echo "Starting Mock Server..."
cd /app && nohup python -m app.server.server > /var/log/mock.log 2>&1 &

# 2. 启动后端 API (FastAPI) - 后台运行
# 注意：监听 127.0.0.1 即可，通过 Nginx 转发
echo "Starting Backend API..."
# 确保安装了 pg 驱动 (防止 requirements.txt 漏掉)
pip install psycopg2-binary --no-index --find-links=/tmp/wheels || true

# 启动命令 (根据您提供的命令调整)
# 生产环境建议去掉 --reload 以提升性能
# 注意：需要监听 0.0.0.0 才能从容器外部访问
cd /app && nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > /var/log/backend.log 2>&1 &

# 等待后端启动初始化
sleep 5

# 3. 启动 Nginx (前端) - 前台运行，作为守护进程
echo "Starting Nginx..."
nginx -g "daemon off;"
