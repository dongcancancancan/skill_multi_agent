# 金融助手系统部署指南

本文档提供了多种部署方式，支持通过环境变量配置系统，无需重新构建镜像。

## 已完成的配置更新

1. ✅ 更新了 `config/default.yaml` 支持环境变量替换
2. ✅ 更新了 `app/utils/config.py` 支持环境变量解析
3. ✅ 创建了环境变量模板 `.env.docker`
4. ✅ 创建了多种启动方式

## 部署方式

### 方式1：使用启动脚本（推荐）

#### Windows系统
```bash
# 1. 复制环境变量模板
copy .env.docker .env

# 2. 编辑.env文件，修改您的配置
notepad .env

# 3. 运行启动脚本
start_with_config.bat
```

#### Linux/Mac系统
```bash
# 1. 复制环境变量模板
cp .env.docker .env

# 2. 编辑.env文件，修改您的配置
nano .env

# 3. 设置执行权限并运行
chmod +x start_with_config.sh
source .env && ./start_with_config.sh
```

### 方式2：直接使用docker run命令

```bash
# 设置环境变量
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=financial_agent
set DB_USER=postgres
set DB_PASSWORD=postgres
set LLM_API_KEY=your_api_key_here

# 运行容器
docker run -d \
  --name financial-agent \
  -p 8888:80 \
  -e DB_HOST=%DB_HOST% \
  -e DB_PORT=%DB_PORT% \
  -e DB_NAME=%DB_NAME% \
  -e DB_USER=%DB_USER% \
  -e DB_PASSWORD=%DB_PASSWORD% \
  -e LLM_MODEL_NAME=%LLM_MODEL_NAME% \
  -e LLM_API_KEY=%LLM_API_KEY% \
  -e LLM_API_BASE=%LLM_API_BASE% \
  -e KNOWLEDGE_API_BASE=%KNOWLEDGE_API_BASE% \
  -e KNOWLEDGE_API_KEY=%KNOWLEDGE_API_KEY% \
  -v "%cd%\logs:/app/logs" \
  -v "%cd%\config:/app/config:ro" \
  --restart unless-stopped \
  financial-agent-pg:final2
```

### 方式3：使用Docker Compose（如果构建正常）

```yaml
# 已创建 docker-compose.yml
# 使用前确保镜像已构建: docker build -t financial-agent-pg:final2 .

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 环境变量配置说明

### 必需配置
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DB_HOST` | 数据库主机地址 | `localhost` |
| `DB_PORT` | 数据库端口 | `5432` |
| `DB_NAME` | 数据库名称 | `financial_agent` |
| `DB_USER` | 数据库用户名 | `postgres` |
| `DB_PASSWORD` | 数据库密码 | `postgres` |
| `LLM_API_KEY` | LLM API密钥 | 无默认值，必须设置 |

### LLM模型配置
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LLM_MODEL_NAME` | 模型名称 | `ep-20251107112900-zxl5d` |
| `LLM_API_BASE` | API基础地址 | `https://ark.cn-beijing.volces.com/api/v3` |

### 知识库配置
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `KNOWLEDGE_API_BASE` | 知识库API地址 | `http://127.0.0.1:5001/v1/datasets/` |
| `KNOWLEDGE_API_KEY` | 知识库API密钥 | `dataset-sGiOtpCtEOySNMsJRs4M0ZeB` |
| `POLICY_DATASET_ID` | 政策数据集ID | `ac814675-271a-42bb-93bd-1be7dc32b449` |
| `CASE_DATASET_ID` | 案例数据集ID | `092b897c-3f4a-4369-89cb-0286761f5ce3` |
| `CREDIT_DATASET_ID` | 信贷数据集ID | `092b897c-3f4a-4369-89cb-0286761f5ce3` |

### 其他配置
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `APP_ENV` | 应用环境 | `development` |
| `API_PORT` | API服务端口 | `8001` |
| `CACHE_ENABLED` | 是否启用缓存 | `true` |
| `CACHE_TYPE` | 缓存类型 | `memory` |
| `MODEL_NAME` | 模型名称 | `blue-green-model` |

## 验证部署

1. 访问前端页面：http://localhost:8888
2. 测试API接口：
   ```bash
   # 测试登录API
   curl -X POST http://localhost:8888/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}'
   ```

3. 查看容器日志：
   ```bash
   docker logs -f financial-agent-custom
   ```

## 故障排除

### 1. 数据库连接失败
- 检查数据库服务是否运行
- 验证数据库连接信息是否正确
- 检查防火墙设置

### 2. API密钥错误
- 确认LLM_API_KEY已正确设置
- 检查API密钥是否有权限访问对应服务

### 3. 容器启动失败
- 检查镜像是否存在：`docker images | grep financial-agent`
- 查看详细错误日志：`docker logs financial-agent-custom`

### 4. 配置文件不生效
- 确保config目录已挂载到容器
- 检查环境变量是否正确传递：`docker exec financial-agent-custom env | grep DB_`

## 更新配置

要更新配置，只需：
1. 修改 `.env` 文件中的环境变量
2. 重启容器：
   ```bash
   docker stop financial-agent-custom
   docker rm financial-agent-custom
   # 重新运行启动脚本
   ```

无需重新构建镜像，所有配置都通过环境变量注入。

## 内网部署说明

对于内网环境：
1. 在有网环境构建镜像并导出：
   ```bash
   docker build -t financial-agent-pg:final2 .
   docker save -o financial-agent-pg.tar financial-agent-pg:final2
   ```

2. 在内网环境导入镜像：
   ```bash
   docker load -i financial-agent-pg.tar
   ```

3. 根据内网环境修改 `.env` 文件中的配置（数据库地址、API地址等）

4. 使用启动脚本部署
