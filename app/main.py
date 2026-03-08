"""
应用入口模块，负责启动FastAPI服务
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.utils.logger import app_logger as logger
from app.utils.config import get_config

# 创建FastAPI应用实例
app = FastAPI(
    title="多智能体金融分析平台",
    description="多智能体金融分析平台API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
from app.api.agents import router as agents_router
from app.api.auth import router as auth_router
from app.api.ai import router as ai_router
from app.api.application_chat import router as application_chat_router
app.include_router(agents_router)
app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(application_chat_router)

def start_api():
    """启动API服务"""
    try:
        host = get_config("api.host", "0.0.0.0")
        port = get_config("api.port", 8000)
        logger.info(f"启动API服务: http://{host}:{port}")
        uvicorn.run("app.main:app", host=host, port=port, reload=True)
    except Exception as e:
        logger.error(f"启动API服务失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    start_api()
