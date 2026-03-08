"""
信用评估工具参数模型
使用Pydantic模型定义参数结构，集成interrupt参数验证
提供完整的信用评估查询参数定义
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langgraph.types import interrupt


class CreditQueryRequest(BaseModel):
    """信用评估查询请求参数模型 - 完整参数定义"""
    
    company: str = Field(..., description="信用评估查询内容，可以是任意信用相关描述")

    def validate_parameters(self) -> None:
        """使用interrupt进行参数验证，提供简洁的业务提示语"""
        # 验证查询内容不能为空
        if not self.company or self.company.strip() == "":
            interrupt("请提供有效的企业名称，进行信用评估查询内容")


def validate_credit_parameters(company: str, **kwargs) -> CreditQueryRequest:
    """验证信用评估查询参数"""
    return CreditQueryRequest(company=company, **kwargs)
