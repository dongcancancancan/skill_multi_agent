#!/bin/bash
# 使用环境变量配置启动脚本
# 用法: ./start_with_config.sh 或 source .env && ./start_with_config.sh

set -e

echo "=== 金融助手系统启动脚本 ==="
echo "使用环境变量配置启动容器"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "错误: Docker未运行"
    exit 1
fi

# 停止并删除现有容器（如果存在）
if docker ps -a --filter "name=financial-agent-custom" --format "{{.Names}}" | grep -q "financial-agent-custom"; then
    echo "停止并删除现有容器..."
    docker stop financial-agent-custom > /dev/null 2>&1
    docker rm financial-agent-custom > /dev/null 2>&1
fi

# 检查镜像是否存在
IMAGE_NAME="financial-agent-pg:final2"
if ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo "错误: 镜像 $IMAGE_NAME 不存在"
    echo "请先构建镜像: docker build -t financial-agent-pg:final2 ."
    exit 1
fi

echo "使用镜像: $IMAGE_NAME"

# 设置默认环境变量（如果未设置）
export APP_ENV=${APP_ENV:-development}
export DB_HOST=${DB_HOST:-localhost}
export DB_PORT=${DB_PORT:-5432}
export DB_NAME=${DB_NAME:-financial_agent}
export DB_USER=${DB_USER:-postgres}
export DB_PASSWORD=${DB_PASSWORD:-postgres}
export LLM_MODEL_NAME=${LLM_MODEL_NAME:-ep-20251107112900-zxl5d}
export LLM_API_KEY=${LLM_API_KEY:-ac0b2e31-4eea-4773-8af6-291197ad32f9}
export LLM_API_BASE=${LLM_API_BASE:-https://ark.cn-beijing.volces.com/api/v3}
export KNOWLEDGE_API_BASE=${KNOWLEDGE_API_BASE:-http://127.0.0.1:5001/v1/datasets/}
export KNOWLEDGE_API_KEY=${KNOWLEDGE_API_KEY:-dataset-sGiOtpCtEOySNMsJRs4M0ZeB}
export API_PORT=${API_PORT:-8001}

echo "环境变量配置:"
echo "  APP_ENV: $APP_ENV"
echo "  DB_HOST: $DB_HOST"
echo "  DB_PORT: $DB_PORT"
echo "  DB_NAME: $DB_NAME"
echo "  DB_USER: $DB_USER"
echo "  LLM_MODEL_NAME: $LLM_MODEL_NAME"
echo "  LLM_API_BASE: $LLM_API_BASE"

# 启动容器
echo "启动容器..."
docker run -d \
  --name financial-agent-custom \
  -p 8888:80 \
  -e APP_ENV="$APP_ENV" \
  -e DB_HOST="$DB_HOST" \
  -e DB_PORT="$DB_PORT" \
  -e DB_NAME="$DB_NAME" \
  -e DB_USER="$DB_USER" \
  -e DB_PASSWORD="$DB_PASSWORD" \
  -e LLM_MODEL_NAME="$LLM_MODEL_NAME" \
  -e LLM_API_KEY="$LLM_API_KEY" \
  -e LLM_API_BASE="$LLM_API_BASE" \
  -e KNOWLEDGE_API_BASE="$KNOWLEDGE_API_BASE" \
  -e KNOWLEDGE_API_KEY="$KNOWLEDGE_API_KEY" \
  -e API_PORT="$API_PORT" \
  -e POLICY_DATASET_ID="$POLICY_DATASET_ID" \
  -e CASE_DATASET_ID="$CASE_DATASET_ID" \
  -e CREDIT_DATASET_ID="$CREDIT_DATASET_ID" \
  -e API_BASE_URL="$API_BASE_URL" \
  -e REQUEST_TIMEOUT="$REQUEST_TIMEOUT" \
  -e MAX_RETRIES="$MAX_RETRIES" \
  -e EDSS_API_HOST="$EDSS_API_HOST" \
  -e EDSS_API_PORT="$EDSS_API_PORT" \
  -e CACHE_ENABLED="$CACHE_ENABLED" \
  -e CACHE_TTL="$CACHE_TTL" \
  -e CACHE_TYPE="$CACHE_TYPE" \
  -e LANGCHAIN_TRACING_V2="$LANGCHAIN_TRACING_V2" \
  -e LANGCHAIN_ENDPOINT="$LANGCHAIN_ENDPOINT" \
  -e LANGCHAIN_API_KEY="$LANGCHAIN_API_KEY" \
  -e LANGCHAIN_PROJECT="$LANGCHAIN_PROJECT" \
  -e MODEL_NAME="$MODEL_NAME" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/config:/app/config:ro" \
  --restart unless-stopped \
  "$IMAGE_NAME"

echo "容器已启动: financial-agent-custom"
echo "访问地址: http://localhost:8888"
echo ""
echo "查看日志: docker logs -f financial-agent-custom"
echo "停止容器: docker stop financial-agent-custom"
echo "删除容器: docker rm financial-agent-custom"
