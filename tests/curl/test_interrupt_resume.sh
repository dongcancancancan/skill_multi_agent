#!/bin/bash

# 测试中断恢复场景的 curl 命令脚本
# 模拟 test_complex_task_stream 测试用例

set -e

# 配置
API_HOST="http://localhost:8000"
API_PATH="/api/agents/main_graph"
API_URL="${API_HOST}${API_PATH}"

# 生成唯一的 session_id
SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')

echo "=========================================="
echo "测试中断恢复场景"
echo "=========================================="
echo "API URL: ${API_URL}"
echo "Session ID: ${SESSION_ID}"
echo ""

# 第一步：发送复杂任务请求，触发中断
echo "=========================================="
echo "步骤1: 发送复杂任务请求（触发计划审批中断）"
echo "=========================================="
echo ""
echo "请求内容: 产品库中有哪些蓝绿色金融产品？产品准入条件是什么？"
echo ""

# 创建临时文件保存响应
RESPONSE_FILE=$(mktemp)

echo "正在发送请求..."
echo ""

curl -N -X POST "${API_URL}" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": \"产品库中有哪些蓝绿色金融产品？产品准入条件是什么？\",
    \"session_id\": \"${SESSION_ID}\",
    \"is_resume\": false
  }" 2>&1 | tee "$RESPONSE_FILE"

echo ""
echo ""

# 检查是否检测到中断
if grep -q "interrupted" "$RESPONSE_FILE"; then
    echo "✅ 检测到中断事件！"
    echo ""
    
    # 等待用户确认
    echo "=========================================="
    echo "步骤2: 模拟用户审批"
    echo "=========================================="
    echo ""
    echo "现在需要发送恢复请求（模拟用户同意计划）"
    read -p "按回车键继续发送 'yes' 恢复请求..."
    echo ""
    
    # 第二步：发送恢复请求
    echo "=========================================="
    echo "正在发送恢复请求..."
    echo "=========================================="
    echo ""
    
    curl -N -X POST "${API_URL}" \
      -H "Content-Type: application/json" \
      -d "{
        \"input\": \"yes\",
        \"session_id\": \"${SESSION_ID}\",
        \"is_resume\": true
      }"
    
    echo ""
    echo ""
    echo "=========================================="
    echo "✅ 中断恢复测试完成！"
    echo "=========================================="
else
    echo "⚠️  未检测到中断事件，可能任务直接完成了"
fi

# 清理临时文件
rm -f "$RESPONSE_FILE"

echo ""
echo "测试结束"


