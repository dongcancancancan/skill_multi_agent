"""
供应链分析参数模型
定义供应链风险评估所需的参数结构
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from langgraph.types import interrupt


class SupplyChainQueryRequest(BaseModel):
    """供应链分析请求参数模型 - 统一查询入口参数"""
    
    query: str = Field(..., description="供应链分析查询内容，可以是任意供应链相关描述")
    company_name: Optional[str] = Field(None, description="公司名称，供应链核心企业")
    industry_sector: Optional[str] = Field(None, description="行业领域，如：制造业、零售业、科技")
    analysis_type: Optional[str] = Field(None, description="分析类型，如：稳定性分析、风险评估、绿色指标")
    risk_category: Optional[str] = Field(None, description="风险类别，如：供应风险、物流风险、环境风险")
    geographic_scope: Optional[str] = Field(None, description="地理范围，如：国内、国际、区域")
    time_horizon: Optional[str] = Field(None, description="时间范围，如：短期、中期、长期")
    supplier_count: Optional[str] = Field(None, description="供应商数量，如：少量、中等、大量")

    def validate_parameters(self) -> None:
        """使用interrupt进行参数验证，提供简洁的业务提示语"""
        # 验证查询内容不能为空
        if not self.query or self.query.strip() == "":
            interrupt("请提供有效的供应链分析查询内容")


class SupplyChainAccessRequest(BaseModel):
    """供应链数据访问请求参数模型"""
    
    supply_chain_id: Optional[str] = Field(None, description="供应链ID")
    data_source: Optional[str] = Field(None, description="数据来源，如：供应商数据库、物流系统")
    data_type: Optional[str] = Field(None, description="数据类型，如：供应商信息、物流数据、风险评估")


class SupplyChainRecommendationRequest(BaseModel):
    """供应链推荐请求参数模型"""
    
    optimization_goal: Optional[str] = Field(None, description="优化目标，如：成本优化、风险降低、绿色转型")
    budget_constraint: Optional[str] = Field(None, description="预算约束，如：有限预算、充足预算")
    timeline_requirement: Optional[str] = Field(None, description="时间要求，如：紧急、常规、长期")


def validate_supply_chain_parameters(
    query: str,
    company_name: Optional[str] = None,
    industry_sector: Optional[str] = None,
    analysis_type: Optional[str] = None,
    risk_category: Optional[str] = None,
    geographic_scope: Optional[str] = None,
    time_horizon: Optional[str] = None,
    supplier_count: Optional[str] = None
) -> SupplyChainQueryRequest:
    """验证供应链分析查询参数"""
    return SupplyChainQueryRequest(
        query=query,
        company_name=company_name,
        industry_sector=industry_sector,
        analysis_type=analysis_type,
        risk_category=risk_category,
        geographic_scope=geographic_scope,
        time_horizon=time_horizon,
        supplier_count=supplier_count
    )
