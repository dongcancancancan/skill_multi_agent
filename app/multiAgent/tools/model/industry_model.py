"""
行业研究工具参数模型
使用Pydantic模型定义参数结构，集成interrupt参数验证
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langgraph.types import interrupt


class IndustryQueryRequest(BaseModel):
    """行业研究查询请求参数模型 - 统一查询入口参数"""
    
    query: str = Field(..., description="行业研究查询内容，可以是任意行业相关描述")
    industry_name: Optional[str] = Field(None, description="行业名称，如：金融、科技、制造业")
    company_name: Optional[str] = Field(None, description="公司名称，用于特定公司行业分析")
    analysis_type: Optional[str] = Field(None, description="分析类型，如：趋势分析、竞争分析、风险评估")
    time_period: Optional[str] = Field(None, description="时间周期，如：2023年、近三年")
    region: Optional[str] = Field(None, description="地区范围，如：全国、华东地区、北京市")
    market_size: Optional[str] = Field(None, description="市场规模，如：大型、中型、小型")
    growth_rate: Optional[str] = Field(None, description="增长率，如：高速增长、稳定增长、负增长")

    def validate_parameters(self) -> None:
        """使用interrupt进行参数验证，提供简洁的业务提示语"""
        # 验证查询内容不能为空
        if not self.query or self.query.strip() == "":
            interrupt("请提供有效的行业研究查询内容")


class IndustryAccessRequest(BaseModel):
    """行业数据访问请求参数模型"""
    
    industry_code: Optional[str] = Field(None, description="行业代码，如：A01、B06")
    industry_category: Optional[str] = Field(None, description="行业分类，如：第一产业、第二产业、第三产业")
    data_type: Optional[str] = Field(None, description="数据类型，如：基础数据、统计数据、分析报告")


class IndustryRecommendationRequest(BaseModel):
    """行业推荐请求参数模型"""
    
    investment_amount: Optional[str] = Field(None, description="投资金额，如：100万、500万")
    risk_preference: Optional[str] = Field(None, description="风险偏好，如：高风险、中风险、低风险")
    investment_horizon: Optional[str] = Field(None, description="投资期限，如：短期、中期、长期")
    target_return: Optional[str] = Field(None, description="目标回报率，如：10%、15%")


def validate_industry_parameters(
    query: str,
    industry_name: Optional[str] = None,
    company_name: Optional[str] = None,
    analysis_type: Optional[str] = None,
    time_period: Optional[str] = None,
    region: Optional[str] = None,
    market_size: Optional[str] = None,
    growth_rate: Optional[str] = None
) -> IndustryQueryRequest:
    """验证行业研究查询参数"""
    return IndustryQueryRequest(
        query=query,
        industry_name=industry_name,
        company_name=company_name,
        analysis_type=analysis_type,
        time_period=time_period,
        region=region,
        market_size=market_size,
        growth_rate=growth_rate
    )
