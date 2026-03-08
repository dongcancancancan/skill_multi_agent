"""
AI相关API路由
"""
import uuid
from fastapi import APIRouter, HTTPException
from app.utils.logger import logger

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/start")
async def start_session():
    """
    开始新的AI会话
    返回一个唯一的会话ID
    """
    try:
        # 生成唯一的会话ID
        session_id = str(uuid.uuid4())
        
        logger.info(f"创建新会话: {session_id}")
        
        return {
            "data": session_id,
            "message": "会话创建成功",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"创建会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建会话失败")


@router.post("/knowledge")
async def knowledge_search():
    """
    知识库搜索接口（占位符）
    """
    return {
        "data": "knowledge_search_placeholder",
        "message": "知识库搜索功能待实现",
        "status": "success"
    }


@router.post("/text2sql")
async def text_to_sql():
    """
    文本转SQL接口（占位符）
    """
    return {
        "data": "text2sql_placeholder", 
        "message": "文本转SQL功能待实现",
        "status": "success"
    }
