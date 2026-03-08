"""
财务分析工具参数模型
使用Pydantic模型定义参数结构，集成interrupt参数验证
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langgraph.types import interrupt


class FinancialQueryRequest(BaseModel):
    """财务分析查询请求参数模型 - 扩展全量参数"""
    
    query: str = Field(..., description="财务分析查询内容，可以是任意财务相关描述")
    company_name: Optional[str] = Field(None, description="公司名称")
    financial_year: Optional[str] = Field(None, description="财务年度，如：2023")
    financial_quarter: Optional[str] = Field(None, description="财务季度，如：Q1")
    analysis_type: Optional[str] = Field(None, description="分析类型，如：盈利能力、偿债能力、运营能力")
    financial_indicator: Optional[str] = Field(None, description="财务指标，如：ROE、ROA、资产负债率")
    comparison_period: Optional[str] = Field(None, description="对比期间，如：同比、环比")
    industry_benchmark: Optional[bool] = Field(False, description="是否进行行业对标分析")
    risk_assessment: Optional[bool] = Field(False, description="是否进行风险评估")
    trend_analysis: Optional[bool] = Field(False, description="是否进行趋势分析")
    cash_flow_analysis: Optional[bool] = Field(False, description="是否进行现金流分析")
    financial_ratios: Optional[List[str]] = Field(None, description="需要分析的财务比率列表")

    def validate_parameters(self) -> None:
        """使用interrupt进行参数验证，提供简洁的业务提示语"""
        # 验证查询内容不能为空
        if not self.query or self.query.strip() == "":
            interrupt("请提供有效的财务分析查询内容")


class FinancialAccessRequest(BaseModel):
    """财务数据访问请求参数模型"""
    
    company_name: str = Field(..., description="公司名称")
    access_type: str = Field(..., description="访问类型，如：财务报表、财务指标")
    data_source: Optional[str] = Field(None, description="数据来源，如：年报、季报")
    time_range: Optional[str] = Field(None, description="时间范围，如：近3年")


class FinancialRecommendationRequest(BaseModel):
    """财务分析推荐请求参数模型"""
    
    company_profile: Dict[str, Any] = Field(..., description="公司基本信息")
    analysis_goals: List[str] = Field(..., description="分析目标列表")
    preferred_indicators: Optional[List[str]] = Field(None, description="偏好指标列表")


def validate_financial_parameters(query: str) -> FinancialQueryRequest:
    """验证财务分析查询参数"""
    return FinancialQueryRequest(query=query)
