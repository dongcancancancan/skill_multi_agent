from typing import Optional
from pydantic import BaseModel, Field, field_validator
from langgraph.types import interrupt


class CaseQueryRequest(BaseModel):
    """案例库查询请求参数模型 - 支持全量参数"""
    query: str = Field(..., description="案例查询内容，可以是任意案例相关描述")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """验证查询内容"""
        if not v or len(v.strip()) < 10:
            interrupt("案例查询内容不能为空且至少需要2个字符")
        return v.strip()
    
    def validate_parameters(self):
        """验证参数完整性"""
        if not self.query:
            interrupt("查询内容不能为空")
