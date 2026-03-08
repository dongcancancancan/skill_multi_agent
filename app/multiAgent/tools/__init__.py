"""
工具模块初始化文件
包含所有多Agent系统的工具定义
"""

# 导入所有工具模块
from app.multiAgent.tools.case import case_query_tool
from app.multiAgent.tools.counterparty import counterparty_query_tool
from app.multiAgent.tools.credit import credit_query_tool
from app.multiAgent.tools.enterprise import enterprise_basic_info_tool, xml_api_tool
from app.multiAgent.tools.greenGold import http_403500, http_403501, http_403502
from app.multiAgent.tools.industry import industry_query_tool
from app.multiAgent.tools.policy import policy_query_tool
from app.multiAgent.tools.product import product_policy_query_tool, product_query_tool
from app.multiAgent.tools.supply_chain import supply_chain_query_tool
from app.multiAgent.tools.customer_manager import customer_manager_profile_tool

# 导入公共模块
from app.multiAgent.tools.common import send_progress_info

# 导入模型模块
from app.multiAgent.tools.model import (
    FinancialQueryRequest,
    CreditQueryRequest,
    IndustryQueryRequest,
    CounterpartyQueryRequest,
    SupplyChainQueryRequest,
    CaseQueryRequest,
    PolicyQueryRequest,
    ProductQueryRequest
)

__all__ = [
    # 工具函数
    "case_query_tool",
    "counterparty_query_tool", 
    "credit_query_tool",
    "enterprise_basic_info_tool",
    "api_query_tool",
    "xml_api_tool",
    "financial_query_tool",
    "http_403500",
    "http_403501", 
    "http_403502",
    "industry_query_tool",
    "product_policy_query_tool",
    "policy_query_tool",
    "product_query_tool",
    "supply_chain_query_tool",
    "customer_manager_profile_tool",
    
    # 公共函数
    "send_progress_info",
    
    # 模型类
    "FinancialQueryRequest",
    "CreditQueryRequest",
    "IndustryQueryRequest",
    "CounterpartyQueryRequest", 
    "SupplyChainQueryRequest",
    "CaseQueryRequest",
    "PolicyQueryRequest",
    "ProductQueryRequest"
]
