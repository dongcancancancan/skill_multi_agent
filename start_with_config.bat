@echo off
echo === 金融助手系统启动脚本 ===
echo 使用环境变量配置启动容器
echo.

REM 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker未运行
    pause
    exit /b 1
)

REM 停止并删除现有容器（如果存在）
docker ps -a --filter "name=financial-agent-custom" --format "{{.Names}}" | findstr "financial-agent-custom" >nul
if not errorlevel 1 (
    echo 停止并删除现有容器...
    docker stop financial-agent-custom >nul 2>&1
    docker rm financial-agent-custom >nul 2>&1
)

REM 检查镜像是否存在
set IMAGE_NAME=financial-agent-pg:final4
docker image inspect %IMAGE_NAME% >nul 2>&1
if errorlevel 1 (
    echo 错误: 镜像 %IMAGE_NAME% 不存在
    echo 请先构建镜像: docker build -t financial-agent-pg:final2 .
    pause
    exit /b 1
)

echo 使用镜像: %IMAGE_NAME%
echo.

REM 设置默认环境变量（如果未设置）
if "%APP_ENV%"=="" set APP_ENV=development
if "%DB_HOST%"=="" set DB_HOST=host.docker.internal
if "%DB_PORT%"=="" set DB_PORT=5432
if "%DB_NAME%"=="" set DB_NAME=aij1
if "%DB_USER%"=="" set DB_USER=root
if "%DB_PASSWORD%"=="" set DB_PASSWORD=root
if "%LLM_MODEL_NAME%"=="" set LLM_MODEL_NAME=ep-20251107112900-zxl5d
if "%LLM_API_KEY%"=="" set LLM_API_KEY=ac0b2e31-4eea-4773-8af6-291197ad32f9
if "%LLM_API_BASE%"=="" set LLM_API_BASE=https://ark.cn-beijing.volces.com/api/v3
if "%KNOWLEDGE_API_BASE%"=="" set KNOWLEDGE_API_BASE=http://127.0.0.1:5001/v1/datasets/
if "%KNOWLEDGE_API_KEY%"=="" set KNOWLEDGE_API_KEY=dataset-sGiOtpCtEOySNMsJRs4M0ZeB
if "%API_PORT%"=="" set API_PORT=8001
if "%POLICY_DATASET_ID%"=="" set POLICY_DATASET_ID=ac814675-271a-42bb-93bd-1be7dc32b449
if "%CASE_DATASET_ID%"=="" set CASE_DATASET_ID=092b897c-3f4a-4369-89cb-0286761f5ce3
if "%CREDIT_DATASET_ID%"=="" set CREDIT_DATASET_ID=092b897c-3f4a-4369-89cb-0286761f5ce3
if "%API_BASE_URL%"=="" set API_BASE_URL=http://localhost:8000
if "%REQUEST_TIMEOUT%"=="" set REQUEST_TIMEOUT=30
if "%MAX_RETRIES%"=="" set MAX_RETRIES=3
if "%EDSS_API_HOST%"=="" set EDSS_API_HOST=localhost
if "%EDSS_API_PORT%"=="" set EDSS_API_PORT=8082
if "%CACHE_ENABLED%"=="" set CACHE_ENABLED=true
if "%CACHE_TTL%"=="" set CACHE_TTL=3600
if "%CACHE_TYPE%"=="" set CACHE_TYPE=memory
if "%LANGCHAIN_TRACING_V2%"=="" set LANGCHAIN_TRACING_V2=true
if "%LANGCHAIN_ENDPOINT%"=="" set LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
if "%LANGCHAIN_API_KEY%"=="" set LANGCHAIN_API_KEY=
if "%LANGCHAIN_PROJECT%"=="" set LANGCHAIN_PROJECT=multi-agent-financial-assistant1
if "%MODEL_NAME%"=="" set MODEL_NAME=blue-green-model

echo 环境变量配置:
echo   APP_ENV: %APP_ENV%
echo   DB_HOST: %DB_HOST%
echo   DB_PORT: %DB_PORT%
echo   DB_NAME: %DB_NAME%
echo   DB_USER: %DB_USER%
echo   LLM_MODEL_NAME: %LLM_MODEL_NAME%
echo   LLM_API_BASE: %LLM_API_BASE%
echo.

REM 启动容器
echo 启动容器...
docker run -d ^
  --name financial-agent-custom ^
  -p 8888:80 ^
  -e APP_ENV="%APP_ENV%" ^
  -e DB_HOST="%DB_HOST%" ^
  -e DB_PORT="%DB_PORT%" ^
  -e DB_NAME="%DB_NAME%" ^
  -e DB_USER="%DB_USER%" ^
  -e DB_PASSWORD="%DB_PASSWORD%" ^
  -e LLM_MODEL_NAME="%LLM_MODEL_NAME%" ^
  -e LLM_API_KEY="%LLM_API_KEY%" ^
  -e LLM_API_BASE="%LLM_API_BASE%" ^
  -e KNOWLEDGE_API_BASE="%KNOWLEDGE_API_BASE%" ^
  -e KNOWLEDGE_API_KEY="%KNOWLEDGE_API_KEY%" ^
  -e API_PORT="%API_PORT%" ^
  -e POLICY_DATASET_ID="%POLICY_DATASET_ID%" ^
  -e CASE_DATASET_ID="%CASE_DATASET_ID%" ^
  -e CREDIT_DATASET_ID="%CREDIT_DATASET_ID%" ^
  -e API_BASE_URL="%API_BASE_URL%" ^
  -e REQUEST_TIMEOUT="%REQUEST_TIMEOUT%" ^
  -e MAX_RETRIES="%MAX_RETRIES%" ^
  -e EDSS_API_HOST="%EDSS_API_HOST%" ^
  -e EDSS_API_PORT="%EDSS_API_PORT%" ^
  -e CACHE_ENABLED="%CACHE_ENABLED%" ^
  -e CACHE_TTL="%CACHE_TTL%" ^
  -e CACHE_TYPE="%CACHE_TYPE%" ^
  -e LANGCHAIN_TRACING_V2="%LANGCHAIN_TRACING_V2%" ^
  -e LANGCHAIN_ENDPOINT="%LANGCHAIN_ENDPOINT%" ^
  -e LANGCHAIN_API_KEY="%LANGCHAIN_API_KEY%" ^
  -e LANGCHAIN_PROJECT="%LANGCHAIN_PROJECT%" ^
  -e MODEL_NAME="%MODEL_NAME%" ^
  -v "%cd%\logs:/app/logs" ^
  -v "%cd%\config:/app/config:ro" ^
  --restart unless-stopped ^
  %IMAGE_NAME%

if errorlevel 1 (
    echo 错误: 容器启动失败
    pause
    exit /b 1
)

echo.
echo 容器已启动: financial-agent-custom
echo 访问地址: http://localhost:8888
echo.
echo 查看日志: docker logs -f financial-agent-custom
echo 停止容器: docker stop financial-agent-custom
echo 删除容器: docker rm financial-agent-custom
echo.
pause
