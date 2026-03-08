# 中断恢复场景测试命令

## 方式一：使用自动化脚本（推荐）

```bash
# 添加执行权限
chmod +x tests/curl/test_interrupt_resume.sh

# 运行脚本
./tests/curl/test_interrupt_resume.sh
```

## 方式二：手动执行 curl 命令

### 步骤1: 生成 session_id

```bash
# macOS / Linux
SESSION_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
echo "Session ID: ${SESSION_ID}"
```

### 步骤2: 发送初始请求（触发中断）

```bash
curl -N -X POST "http://localhost:8000/api/agents/main_graph" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": \"产品库中有哪些蓝绿色金融产品？产品准入条件是什么？\",
    \"session_id\": \"${SESSION_ID}\",
    \"is_resume\": false
  }"
```

**预期输出**: 会看到 SSE 流式输出，最后会收到类似以下的中断事件：

```
event: update
data: {"status":"interrupted","stream_mode":"updates","data":{"__interrupt__":[...]}}
```

### 步骤3: 发送恢复请求（用相同的 SESSION_ID）

```bash
curl -N -X POST "http://localhost:8000/api/agents/main_graph" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": \"yes\",
    \"session_id\": \"${SESSION_ID}\",
    \"is_resume\": true
  }"
```

**预期输出**: 会继续执行计划，返回最终的结果。

## 方式三：使用完整的 curl 命令（复制粘贴）

### 第一次请求

```bash
curl -N -X POST "http://localhost:8000/api/agents/main_graph" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "产品库中有哪些蓝绿色金融产品？产品准入条件是什么？",
    "session_id": "test-interrupt-001",
    "is_resume": false
  }'
```

### 恢复请求（等待上面的请求中断后）

```bash
curl -N -X POST "http://localhost:8000/api/agents/main_graph" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "yes",
    "session_id": "test-interrupt-001",
    "is_resume": true
  }'
```

**注意**: 两次请求必须使用相同的 `session_id`

## 测试拒绝场景

如果想测试用户拒绝计划的场景，将恢复请求中的 `input` 改为 `"no"`:

```bash
curl -N -X POST "http://localhost:8000/api/agents/main_graph" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "no",
    "session_id": "test-interrupt-001",
    "is_resume": true
  }'
```

**预期输出**: 会话将被锁定，返回错误信息。

## 其他测试场景

### 简单查询（不会触发中断）

```bash
curl -N -X POST "http://localhost:8000/api/agents/main_graph" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "你好",
    "session_id": "test-simple-001",
    "is_resume": false
  }'
```

### ToolBox 查询（不会触发中断）

```bash
curl -N -X POST "http://localhost:8000/api/agents/main_graph" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "查询青岛蓝色能源有限公司的工商信息",
    "session_id": "test-toolbox-001",
    "is_resume": false
  }'
```

## 查看 SSE 流式输出

curl 命令会持续输出 SSE 事件流，格式如下：

```
event: message
data: {"status":"success","stream_mode":"messages","data":{"content":"..."}}

event: custom
data: {"status":"success","stream_mode":"custom","data":{"type":"thinking","data":"..."}}

event: update
data: {"status":"interrupted","stream_mode":"updates","interrupt_data":{...}}
```

## 注意事项

1. **必须使用 `-N` 参数**: 禁用缓冲，才能看到实时的流式输出
2. **session_id 必须一致**: 恢复请求必须使用与初始请求相同的 session_id
3. **is_resume 参数**: 恢复请求必须设置为 `true`
4. **等待中断**: 必须等第一个请求返回中断事件后，再发送恢复请求

## 调试技巧

### 保存响应到文件

```bash
curl -N -X POST "http://localhost:8000/api/agents/main_graph" \
  -H "Content-Type: application/json" \
  -d '{...}' > response.txt 2>&1
```

### 只显示响应体

```bash
curl -N -s -X POST "http://localhost:8000/api/agents/main_graph" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### 显示详细的调试信息

```bash
curl -N -v -X POST "http://localhost:8000/api/agents/main_graph" \
  -H "Content-Type: application/json" \
  -d '{...}'
```


