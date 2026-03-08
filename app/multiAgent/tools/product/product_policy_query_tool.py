"""
政策工具查询工具模块 - 重构为统一查询入口
提供对policy_tools表的查询功能，支持多维度检索和政策工具推荐
"""

import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langgraph.types import interrupt
from app.multiAgent.common.postgresql_connection import get_postgresql_connection
from app.utils.logger import logger
from app.multiAgent.tools.model.product_model import ProductPolicyQueryRequest
from app.multiAgent.common.tool_decorator import with_error_handling
from app.multiAgent.tools.common import send_progress_info


@tool("product_policy_query_tool", args_schema=ProductPolicyQueryRequest,
      description='''产品金融工具查询工具：
                    示例调用：product_policy_query_tool("绿色信贷")
                    功能：
                    - 多维度政策工具查询：支持根据政策工具名称、属性、额度、支持市场主体、投资领域、优惠安排等多维度条件进行查询
                    - 政策工具推荐：根据用户需求推荐符合条件的政策工具''')
@with_error_handling
def product_policy_query_tool(
    query: str,
    policy_tool: Optional[str] = None,
    tool_property: Optional[str] = None,
    tool_quota: Optional[str] = None,
    supported_market_entities: Optional[str] = None,
    investment_field: Optional[str] = None,
    discount_arrangement: Optional[str] = None,
    support_objects: Optional[str] = None
) -> str:
    # 输出进度信息
    progress_data = "📋 产品政策工具查询"
    params = []
    if query:
        params.append(f"查询：{query}")
    if policy_tool:
        params.append(f"工具：{policy_tool}")
    if tool_property:
        params.append(f"属性：{tool_property}")
    if tool_quota:
        params.append(f"额度：{tool_quota}")
    if params:
        progress_data += f" | {', '.join(params)}"
    send_progress_info(progress_data)
    
    logger.info(f'''产品政策统一查询工具入口:
                {query} {policy_tool} {tool_property} {tool_quota}
                {supported_market_entities} {investment_field} {discount_arrangement} {support_objects}
            ''')
    db = get_postgresql_connection()
    # 参数验证
    if not query and not any([policy_tool, tool_property, tool_quota, supported_market_entities, 
                            investment_field, discount_arrangement]):
        interrupt("请提供产品政策工具详细要求")
    results = []
    conditions = []
    # 检测输入类型并构建查询条件
    params = []
    
    if policy_tool:
        conditions.append("policy_tool LIKE %s")
        params.append(f'%{policy_tool}%')
         
    if tool_property:
        conditions.append("tool_property LIKE %s")
        params.append(f'%{tool_property}%')
    
    if tool_quota:
        conditions.append("tool_quota LIKE %s")
        params.append(f'%{tool_quota}%')

    if supported_market_entities:
        conditions.append("supported_market_entities LIKE %s")
        params.append(f'%{supported_market_entities}%')

    if investment_field:
        conditions.append("investment_field LIKE %s")
        params.append(f'%{investment_field}%')

    if discount_arrangement:
        conditions.append("discount_arrangement LIKE %s")
        params.append(f'%{discount_arrangement}%')

    if support_objects:
        conditions.append("support_objects LIKE %s")
        params.append(f'%{support_objects}%')


    if len(conditions) > 0:
        query_sql = f"SELECT policy_tool AS 政策工具, tool_property AS 工具性质,tool_quota AS 工具额度,supported_market_entities AS 支持市场主体,investment_field AS 投向领域,discount_arrangement AS 贴息安排,policy_standard_elements AS 符合政策标准要素,highlights AS 亮点,business_points AS 业务要点,support_objects AS 支持对象 FROM policy_tools WHERE {' OR '.join(conditions)} ORDER BY policy_tool"
        logger.info(query_sql)
        results = db.execute_query(query_sql, tuple(params))

    if not results:
        #执行工具查询
        query_sql = "SELECT policy_tool AS 政策工具, tool_property AS 工具性质,tool_quota AS 工具额度,supported_market_entities AS 支持市场主体,investment_field AS 投向领域,discount_arrangement AS 贴息安排,policy_standard_elements AS 符合政策标准要素,highlights AS 亮点,business_points AS 业务要点,support_objects AS 支持对象 FROM policy_tools ORDER BY policy_tool limit 100"
        logger.info(query_sql)
        results = db.execute_query(query_sql)
    logger.info(f"query总数:{len(results)}")
    if len(results) > 100:
         interrupt("请提供产品政策工具详细要求")
    return results
