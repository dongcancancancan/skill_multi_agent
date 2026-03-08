#!/bin/bash

# PostgreSQL启动脚本
POSTGRES_DATA_DIR="/opt/miniconda3/var/lib/postgresql/data"
POSTGRES_LOG_FILE="/opt/miniconda3/var/lib/postgresql/logfile"

echo "检查PostgreSQL服务状态..."
/opt/miniconda3/bin/pg_ctl status -D $POSTGRES_DATA_DIR

if [ $? -ne 0 ]; then
    echo "PostgreSQL服务未运行，正在启动..."
    /opt/miniconda3/bin/pg_ctl start -D $POSTGRES_DATA_DIR -l $POSTGRES_LOG_FILE
    echo "PostgreSQL服务已启动"
else
    echo "PostgreSQL服务已在运行"
fi

echo "连接信息："
echo "主机: localhost"
echo "端口: 5432"
echo "数据库: aijl"
echo "用户名: aijl"
echo "密码: Qdccb789"
echo "连接字符串: postgresql://aijl:Qdccb789@localhost:5432/aijl"
