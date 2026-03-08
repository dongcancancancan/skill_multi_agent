#!/bin/bash

# 启动服务
start_services() {
    conda activate lang_env
    export PYTHONPATH=/Users/hongxin.shao/code/ai/multi-agent-financial-assistant/multi-agent-financial-assistant
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# 停止服务
stop_services() {
    lsof -ti :8000 | xargs kill -9
}

case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac


# 前端
node版本22.18.0
cd /Users/hongxin.shao/code/ai/multi-agent-financial-assistant/multi-agent-financial-assistant/web
chmod -R 755 node_modules


# server启动
conda activate lang_env
cd /Users/hongxin.shao/code/ai/yanshi/multi-agent-financial-assistant && python -m app.server.server

#行内接口
ssh -L 8082:10.1.93.208:8090 shx@10.238.146.99


# studio 启动
cd studio && langgraph dev --allow-blocking




