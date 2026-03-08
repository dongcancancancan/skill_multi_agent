"""
交易对手分析参数模型
定义交易对手风险评估所需的参数结构
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from langgraph.types import interrupt


class CounterpartyQueryRequest(BaseModel):
    """交易对手分析请求参数模型 - 统一查询入口参数"""
    
    query: str = Field(..., description="交易对手分析查询内容，可以是任意交易对手相关描述")
    company_name: Optional[str] = Field(None, description="公司名称，交易对手公司全称")
    credit_code: Optional[str] = Field(None, description="统一社会信用代码")
    risk_type: Optional[str] = Field(None, description="风险类型，如：信用风险、市场风险、操作风险")
    analysis_depth: Optional[str] = Field(None, description="分析深度，如：基础分析、深度分析、全面分析")
    time_horizon: Optional[str] = Field(None, description="时间范围，如：短期、中期、长期")
    industry_sector: Optional[str] = Field(None, description="行业领域，如：金融、制造、科技")
    transaction_amount: Optional[str] = Field(None, description="交易金额，如：100万、500万")

    def validate_parameters(self) -> None:
        """使用interrupt进行参数验证，提供简洁的业务提示语"""
        # 验证查询内容不能为空
        if not self.query or self.query.strip() == "":
            interrupt("请提供有效的交易对手分析查询内容")


class CounterpartyAccessRequest(BaseModel):
    """交易对手数据访问请求参数模型"""
    
    counterparty_id: Optional[str] = Field(None, description="交易对手ID")
    data_source: Optional[str] = Field(None, description="数据来源，如：征信系统、企业数据库")
    data_type: Optional[str] = Field(None, description="数据类型，如：基础信息、财务数据、信用记录")


class CounterpartyRecommendationRequest(BaseModel):
    """交易对手推荐请求参数模型"""
    
    risk_tolerance: Optional[str] = Field(None, description="风险容忍度，如：高风险、中风险、低风险")
    relationship_type: Optional[str] = Field(None, description="关系类型，如：供应商、客户、合作伙伴")
    business_scale: Optional[str] = Field(None, description="业务规模，如：大型、中型、小型")


def validate_counterparty_parameters(
    query: str,
    company_name: Optional[str] = None,
    credit_code: Optional[str] = None,
    risk_type: Optional[str] = None,
    analysis_depth: Optional[str] = None,
    time_horizon: Optional[str] = None,
    industry_sector: Optional[str] = None,
    transaction_amount: Optional[str] = None
) -> CounterpartyQueryRequest:
    """验证交易对手分析查询参数"""
    return CounterpartyQueryRequest(
        query=query,
        company_name=company_name,
        credit_code=credit_code,
        risk_type=risk_type,
        analysis_depth=analysis_depth,
        time_horizon=time_horizon,
        industry_sector=industry_sector,
        transaction_amount=transaction_amount
    )
