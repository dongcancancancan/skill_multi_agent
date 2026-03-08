"""
产品库查询参数模型
定义产品库查询所需的完整参数结构
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langgraph.types import interrupt


class ProductQueryRequest(BaseModel):
    """产品库统一查询请求参数模型 - 包含所有查询参数"""
    
    # 分类查询参数
    loan_category: Optional[str] = Field(None, description="贷款类别，如：企业贷款、个人贷款")
    product_classification: Optional[str] = Field(None, description="产品分类，如：经营贷、项目贷")
    product_subcategory: Optional[str] = Field(None, description="产品子类，如：短期、中期、长期")
    product_name: Optional[str] = Field(None, description="产品名称，用于精确或模糊匹配")
    
    # 精确查询参数
    product_code: Optional[str] = Field(None, description="产品代码，用于精确查询特定产品")
    
    # 准入相关参数
    product_access: Optional[str] = Field(None, description="产品准入条件，用于根据企业资质、许可证类型、行业要求等筛选适配产品。当用户询问产品准入条件、特定资质要求或持有特定许可证（如取水许可证、排污许可证、碳排放权配额等）的企业可以申请哪些产品时使用此参数")
    
    # 政策相关参数
    preferential_policy: Optional[str] = Field(None, description="优惠政策关键词，如：贴息、利率优惠")

    def validate_parameters(self) -> None:
        """使用interrupt进行参数验证，提供简洁的业务提示语"""
        # 验证至少有一个有效的查询条件
        has_valid_condition = (
            self.loan_category or
            self.product_classification or
            self.product_subcategory or
            self.product_name or
            self.product_code or
            self.product_access or
            self.preferential_policy
        )
        
        if not has_valid_condition:
            # 不再直接中断，而是允许工具返回所有产品
            # 这样可以让agent基于返回的所有产品进行智能推荐
            # 而不是中断整个流程
            pass


def validate_product_parameters(
    loan_category: Optional[str] = None,
    product_classification: Optional[str] = None,
    product_subcategory: Optional[str] = None,
    product_name: Optional[str] = None,
    product_code: Optional[str] = None,
    product_access: Optional[str] = None,
    preferential_policy: Optional[str] = None
) -> ProductQueryRequest:
    """验证产品查询参数"""
    return ProductQueryRequest(
        loan_category=loan_category,
        product_classification=product_classification,
        product_subcategory=product_subcategory,
        product_name=product_name,
        product_code=product_code,
        product_access=product_access,
        preferential_policy=preferential_policy
    )


class ProductPolicyQueryRequest(BaseModel):
    """政策查询请求参数模型"""
    
    query: str = Field(..., description="政策查询内容，可以是任意政策相关描述")
    policy_tool: Optional[str] = Field(None, description="政策工具名称，如：再贷款、专项债")
    tool_property: Optional[str] = Field(None, description="工具性质，如：货币政策工具、财政政策工具")
    tool_quota: Optional[str] = Field(None, description="工具额度关键词")
    supported_market_entities: Optional[str] = Field(None, description="支持市场主体关键词")
    investment_field: Optional[str] = Field(None, description="投向领域关键词")
    discount_arrangement: Optional[str] = Field(None, description="贴息安排关键词")
    support_objects: Optional[str] = Field(None, description="支持对象关键词")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "查询支持绿色项目的货币政策工具",
                "policy_tool": "再贷款",
                "tool_property": "货币政策工具",
                "investment_field": "绿色项目"
            }
        }
