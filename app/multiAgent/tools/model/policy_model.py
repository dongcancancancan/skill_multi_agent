"""
政策查询参数模型定义
用于政策工具查询的统一参数验证
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PolicyQueryRequest(BaseModel):
    """政策查询请求参数模型"""
    query: str = Field(..., description="政策查询内容，可以是任意政策相关描述")
    config: Optional[Dict[str, Any]] = Field(None, description="LangGraph配置参数，用于流式输出")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "查询支持绿色项目的货币政策",
            }
        }
