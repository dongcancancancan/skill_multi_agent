"""
贷款产品查询工具模块
提供对loan_product_info表的统一查询功能
"""

from typing import Dict, List, Optional, Any
from app.utils.logger import logger
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langgraph.types import interrupt
from app.multiAgent.common.postgresql_connection import get_postgresql_connection
from app.multiAgent.tools.model.product_model import ProductQueryRequest, validate_product_parameters
from app.multiAgent.common.tool_decorator import with_error_handling
from app.multiAgent.tools.common import send_progress_info, send_citation_info


@tool("product_query_tool", args_schema=ProductQueryRequest, 
      description="金融产品查询工具：基于loan_product_info表进行全面的产品查询"
                  "核心功能："
                  "- 产品库查询：获取所有产品列表，了解产品库整体情况"
                  "- 分类查询：按贷款类别、产品分类、产品子类等维度筛选产品"
                  "- 精确查询：通过产品代码或产品名称查找特定产品"
                  "- 政策查询：根据优惠政策关键词筛选享受特殊政策的产品"
                  "- 产品准入条件查询：根据企业资质、许可证类型、行业要求等准入条件筛选适配产品"
                  "- 智能推荐：基于多条件组合推荐最适合的产品"
                  "使用指南："
                  "- 当用户询问产品库信息、产品列表、有哪些产品时，直接调用本工具获取完整产品信息"
                  "- 当用户询问产品准入条件、特定资质要求时，使用product_access参数进行筛选"
                  "- 当用户询问持有特定许可证（如取水许可证、排污许可证等）的企业可以申请哪些产品时，使用product_access参数"
                  "- 支持多条件组合查询，提供更精准的产品匹配"
                  "实际产品分类："
                  "- 交易结算产品（4个产品）"
                  "- 信贷类产品（26个产品）"
                  "- 创新混合融资产品（3个产品）"
                  "- 政策工具类（1个产品）"
                  "典型应用场景："
                  "- 查询产品库整体情况：product_query_tool()"
                  "- 查询信贷类产品：product_query_tool(loan_category='信贷类产品')"
                  "- 查询交易结算产品：product_query_tool(loan_category='交易结算产品')"
                  "- 查询产品准入条件：product_query_tool(product_access='取水许可证') 或 product_query_tool(product_access='排污许可证')"
                  "- 查询特定分类产品：product_query_tool(product_classification='环境权益服务方案 - 环贷通')"
                  "- 组合查询：product_query_tool(loan_category='信贷类产品', product_access='碳排放权配额')")
def product_query_tool(
    loan_category: Optional[str] = None,
    product_classification: Optional[str] = None,
    product_subcategory: Optional[str] = None,
    product_name: Optional[str] = None,
    product_code: Optional[str] = None,
    product_access: Optional[str] = None,
    preferential_policy: Optional[str] = None
) -> Dict[str, Any]:
    db = get_postgresql_connection()
    logger.info(f"产品查询参数：loan_category={loan_category}, product_classification={product_classification}, product_subcategory={product_subcategory}, product_name={product_name}, product_code={product_code}, product_access={product_access}, preferential_policy={preferential_policy}")
    
    def query_products_by_category(loan_category: str) -> List[Dict[str, Any]]:
        """根据贷款类别查询产品"""
        query_sql = "SELECT * FROM loan_product_info WHERE loan_category LIKE %s ORDER BY product_name"
        return db.execute_query(query_sql, (f'%{loan_category}%',))
    
    def query_products_by_classification(product_classification: str) -> List[Dict[str, Any]]:
        """根据产品分类查询产品"""
        query_sql = "SELECT * FROM loan_product_info WHERE product_classification LIKE %s ORDER BY product_name"
        return db.execute_query(query_sql, (f'%{product_classification}%',))
    
    def query_products_by_subcategory(product_subcategory: str) -> List[Dict[str, Any]]:
        """根据产品子类查询产品"""
        query_sql = "SELECT * FROM loan_product_info WHERE product_subcategory LIKE %s ORDER BY product_name"
        return db.execute_query(query_sql, (f'%{product_subcategory}%',))
    
    def query_product_by_code(product_code: str) -> Optional[Dict[str, Any]]:
        """根据产品代码查询特定产品（精确匹配）"""
        query_sql = "SELECT * FROM loan_product_info WHERE product_code = %s"
        results = db.execute_query(query_sql, (product_code,))
        return results[0] if results else None
    
    def query_products_by_preferential_policy(policy_keyword: str) -> List[Dict[str, Any]]:
        """根据优惠政策关键词查询产品"""
        query_sql = "SELECT * FROM loan_product_info WHERE preferential_policy LIKE %s ORDER BY product_name"
        return db.execute_query(query_sql, (f'%{policy_keyword}%',))
    
    def get_all_products() -> List[Dict[str, Any]]:
        """获取所有产品"""
        query_sql = "SELECT loan_category AS 贷款类别, product_classification AS 产品分类, product_subcategory AS 产品子类, product_name AS 产品名称, product_code AS 产品代码, product_access AS 产品准入, preferential_policy AS 优惠政策 FROM loan_product_info ORDER BY loan_category, product_classification, product_name"
        return db.execute_query(query_sql)
    
    def recommend_products(criteria: Dict[str, str]) -> List[Dict[str, Any]]:
        """根据多个条件推荐产品"""
        conditions = []
        params = []
        
        if 'loan_category' in criteria:
            conditions.append("loan_category LIKE %s")
            params.append(f'%{criteria["loan_category"]}%')
        
        if 'product_classification' in criteria:
            conditions.append("product_classification LIKE %s")
            params.append(f'%{criteria["product_classification"]}%')
        
        if 'product_subcategory' in criteria:
            conditions.append("product_subcategory LIKE %s")
            params.append(f'%{criteria["product_subcategory"]}%')
        
        if 'product_name' in criteria:
            conditions.append("product_name LIKE %s")
            params.append(f'%{criteria["product_name"]}%')
        
        if 'product_access' in criteria:
            conditions.append("product_access LIKE %s")
            params.append(f'%{criteria["product_access"]}%')
        
        if 'preferential_policy' in criteria:
            conditions.append("preferential_policy LIKE %s")
            params.append(f'%{criteria["preferential_policy"]}%')
        
        if not conditions:
            return get_all_products()
        
        query_sql = f"SELECT loan_category AS 贷款类别, product_classification AS 产品分类, product_subcategory AS 产品子类, product_name AS 产品名称, product_code AS 产品代码, product_access AS 产品准入, preferential_policy AS 优惠政策 FROM loan_product_info WHERE {' AND '.join(conditions)} ORDER BY product_name"
        return db.execute_query(query_sql, tuple(params))
    

    def _intelligent_query_routing() -> List[Dict[str, Any]]:
        """智能路由逻辑：根据参数自动选择最佳查询策略"""
        
        # 1. 精确查询：产品代码优先
        if product_code:
            product = query_product_by_code(product_code)
            return [product] if product else []
        
        # 2. 分类查询：根据具体条件选择
        criteria = {}
        if loan_category:
            criteria['loan_category'] = loan_category
        if product_classification:
            criteria['product_classification'] = product_classification
        if product_subcategory:
            criteria['product_subcategory'] = product_subcategory
        if product_name:
            criteria['product_name'] = product_name
        if product_access:
            criteria['product_access'] = product_access
        if preferential_policy:
            criteria['preferential_policy'] = preferential_policy
        
        if criteria:
            return recommend_products(criteria)
        
        # 3. 如果没有提供任何参数，返回所有产品
        return get_all_products()
    
    def _determine_query_type() -> str:
        """确定查询类型"""
        if product_code:
            return "精确查询（产品代码）"
        elif loan_category or product_classification or product_subcategory or product_name or product_access or preferential_policy:
            return "分类查询"
        else:
            return "全量查询"
        
    # 输出进度信息
    progress_data = "💰 金融产品查询"
    params = []
    params.append(f"查询类型：{_determine_query_type()}")
    if loan_category:
        params.append(f"贷款类别：{loan_category}")
    if product_classification:
        params.append(f"产品分类：{product_classification}")
    if product_name:
        params.append(f"产品名称：{product_name}")
    if product_code:
        params.append(f"产品代码：{product_code}")
    if product_access:
        params.append(f"产品准入：{product_access}")
    if preferential_policy:
        params.append(f"优惠政策：{preferential_policy}")
    progress_data += f" | {', '.join(params)}"
    send_progress_info(progress_data)
    
    # 发送角标信息 - 产品查询使用[s1]格式
    send_citation_info("[s1]", "数据库表: loan_product_info")
    
    # 验证参数
    request = validate_product_parameters(
        loan_category=loan_category,
        product_classification=product_classification,
        product_subcategory=product_subcategory,
        product_name=product_name,
        product_code=product_code,
        product_access=product_access,
        preferential_policy=preferential_policy
    )
    request.validate_parameters()
    
    # 智能路由逻辑：根据传入参数选择最佳查询策略
    results = _intelligent_query_routing()
    
    # 添加来源标记到每个结果
    processed_results = []
    for item in results:
        if isinstance(item, dict):
            # 添加_source字段
            item_with_source = item.copy()
            item_with_source["_source"] = "数据库表: loan_product_info"
            processed_results.append(item_with_source)
        else:
            processed_results.append(item)
    
    # 构建响应，在开头添加角标
    response_text = f"[s1] 产品查询结果：\n\n"
    
    # 添加查询信息
    response_text += f"查询类型：{_determine_query_type()}\n"
    response_text += f"查询结果数量：{len(processed_results)}\n\n"
    
    # 添加产品列表
    if processed_results:
        response_text += "产品列表：\n"
        for i, item in enumerate(processed_results[:10], 1):  # 只显示前10个产品
            if isinstance(item, dict):
                product_name = item.get("产品名称", "未知")
                product_code = item.get("产品代码", "未知")
                loan_category = item.get("贷款类别", "未知")
                response_text += f"{i}. {product_name} ({product_code}) - {loan_category}\n"
    
    if len(processed_results) > 10:
        response_text += f"...等{len(processed_results)}个产品\n"
    
    response_text += f"\n数据来源：数据库表: loan_product_info"
    
    response = {
        "status": "success",
        "query_type": _determine_query_type(),
        "results": processed_results,
        "total_count": len(processed_results),
        "query_parameters": {
            "loan_category": loan_category,
            "product_classification": product_classification,
            "product_subcategory": product_subcategory,
            "product_name": product_name,
            "product_code": product_code,
            "product_access": product_access,
            "preferential_policy": preferential_policy
        },
        "execution_time": "实时",
        "data_source": "loan_product_info表",
        "response_text": response_text  # 添加包含角标的文本响应
    }
    logger.info(f"产品请求结束：{response}")
    return response
