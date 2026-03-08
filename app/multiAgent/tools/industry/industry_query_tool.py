"""
行业研究统一查询工具
提供行业趋势分析、市场竞争分析、行业推荐等功能
使用函数式实现，避免重复模型定义
"""

from typing import Dict, Any
from langchain_core.tools import tool
from langgraph.types import interrupt

from app.multiAgent.tools.model.industry_model import IndustryQueryRequest
from app.multiAgent.common.tool_decorator import with_error_handling
from app.multiAgent.tools.common import send_progress_info


def _company_industry_analysis(request: IndustryQueryRequest) -> Dict[str, Any]:
    """特定公司行业分析"""
    ai_input = f"请进行{request.analysis_type or '行业分析'}：分析{request.company_name}在{request.industry_name or '相关'}行业的市场地位和竞争态势"
    
    return {
        "status": "success",
        "type": "company_industry_analysis",
        "company_name": request.company_name,
        "industry_name": request.industry_name,
        "analysis_type": request.analysis_type,
        "analysis_content": f"对{request.company_name}进行行业分析：{request.query}",
        "recommendations": [
            "关注行业政策变化对该公司的影响",
            "分析该公司在行业中的市场份额和竞争优势",
            "评估行业发展趋势对该公司业务的影响"
        ],
        "data_source": "行业数据库",
        "timestamp": "2024-01-01"
    }


def _specific_industry_analysis(request: IndustryQueryRequest) -> Dict[str, Any]:
    """特定行业分析"""
    ai_input = f"请进行{request.analysis_type}：分析{request.industry_name}行业的发展趋势"
    
    return {
        "status": "success",
        "type": "specific_industry_analysis",
        "industry_name": request.industry_name,
        "analysis_type": request.analysis_type,
        "analysis_content": f"对{request.industry_name}行业进行{request.analysis_type}：{request.query}",
        "key_findings": [
            f"{request.industry_name}行业{request.time_period or '当前'}发展趋势分析",
            "市场竞争格局评估",
            "政策环境影响分析"
        ],
        "data_source": "行业研究报告",
        "timestamp": "2024-01-01"
    }


def _basic_industry_analysis(request: IndustryQueryRequest) -> Dict[str, Any]:
    """行业基础分析"""
    return {
        "status": "success",
        "type": "basic_industry_analysis",
        "industry_name": request.industry_name,
        "analysis_content": f"基础行业分析：{request.query}",
        "market_overview": f"{request.industry_name}行业基本情况",
        "growth_prospects": "行业增长前景分析",
        "risk_assessment": "行业风险评估",
        "data_source": "行业统计数据库",
        "timestamp": "2024-01-01"
    }


def _general_industry_query(request: IndustryQueryRequest) -> Dict[str, Any]:
    """通用行业查询"""
    return {
        "status": "success",
        "type": "general_industry_query",
        "analysis_content": f"通用行业查询：{request.query}",
        "search_results": [
            "相关行业趋势分析报告",
            "市场竞争格局研究",
            "政策法规影响评估"
        ],
        "recommended_industries": ["科技", "金融", "制造业", "医疗健康"],
        "data_source": "综合行业数据库",
        "timestamp": "2024-01-01"
    }


@tool("industry_query_tool", args_schema=IndustryQueryRequest,
      description="行业研究统一查询工具："
                  "示例调用："
                  "- industry_query_tool('分析金融行业发展趋势')"
                  "功能："
                  "- 行业趋势分析：分析行业发展趋势、市场变化和未来前景"
                  "- 市场竞争分析：评估行业竞争格局、主要参与者和市场份额"
                  "- 公司行业分析：针对特定公司进行行业地位和竞争态势分析"
                  "- 风险评估：评估行业投资风险和经营风险"
                  "- 政策影响分析：分析政策法规对行业的影响")
def industry_query_tool(
    query: str,
    industry_name: str = None,
    company_name: str = None,
    analysis_type: str = None,
    time_period: str = None,
    region: str = None,
    market_size: str = None,
    growth_rate: str = None
) -> Dict[str, Any]:
    # 创建IndustryQueryRequest对象
    request = IndustryQueryRequest(
        query=query,
        industry_name=industry_name,
        company_name=company_name,
        analysis_type=analysis_type,
        time_period=time_period,
        region=region,
        market_size=market_size,
        growth_rate=growth_rate
    )
    
    # 验证参数
    request.validate_parameters()
    
    # 输出进度信息
    progress_data = "🏭 行业研究查询"
    params = []
    params.append(f"查询：{query}")
    if industry_name:
        params.append(f"行业：{industry_name}")
    if company_name:
        params.append(f"企业：{company_name}")
    if analysis_type:
        params.append(f"分析类型：{analysis_type}")
    progress_data += f" | {', '.join(params)}"
    send_progress_info(progress_data)
    
    # 智能路由逻辑
    if request.company_name:
        # 特定公司行业分析
        return _company_industry_analysis(request)
    elif request.industry_name and request.analysis_type:
        # 特定行业分析类型
        return _specific_industry_analysis(request)
    elif request.industry_name:
        # 行业基础分析
        return _basic_industry_analysis(request)
    else:
        # 通用行业查询
        return _general_industry_query(request)
    


# 导出工具实例
industry_query = industry_query_tool
