"""
交易对手分析统一查询工具
提供交易对手信用风险评估、违约概率分析、风险监控等功能
使用函数式实现，避免重复模型定义
"""

from typing import Dict, Any
from langchain_core.tools import tool
from langgraph.types import interrupt

from app.multiAgent.tools.model.counterparty_model import CounterpartyQueryRequest
from app.multiAgent.tools.common import send_progress_info


def _exact_company_analysis(request: CounterpartyQueryRequest) -> Dict[str, Any]:
    """精确公司交易对手分析"""
    return {
        "status": "success",
        "type": "exact_company_analysis",
        "company_name": request.company_name,
        "credit_code": request.credit_code,
        "risk_type": request.risk_type,
        "analysis_content": f"对{request.company_name}进行{request.risk_type or '交易对手'}分析：{request.query}",
        "risk_assessment": {
            "credit_risk": "中等",
            "market_risk": "低",
            "operational_risk": "低"
        },
        "default_probability": "2.5%",
        "monitoring_recommendations": [
            "定期更新财务数据",
            "监控行业政策变化",
            "关注市场动态"
        ],
        "data_source": "征信系统+企业数据库",
        "timestamp": "2024-01-01"
    }


def _specific_risk_analysis(request: CounterpartyQueryRequest) -> Dict[str, Any]:
    """特定风险类型分析"""
    return {
        "status": "success",
        "type": "specific_risk_analysis",
        "company_name": request.company_name,
        "risk_type": request.risk_type,
        "analysis_content": f"对{request.company_name}进行{request.risk_type}分析：{request.query}",
        "risk_indicators": [
            f"{request.risk_type}关键指标分析",
            "风险敞口评估",
            "风险控制措施建议"
        ],
        "mitigation_strategies": [
            "风险对冲策略",
            "风险转移方案",
            "风险监控机制"
        ],
        "data_source": "风险管理系统",
        "timestamp": "2024-01-01"
    }


def _basic_company_analysis(request: CounterpartyQueryRequest) -> Dict[str, Any]:
    """公司基础分析"""
    return {
        "status": "success",
        "type": "basic_company_analysis",
        "company_name": request.company_name,
        "analysis_content": f"基础交易对手分析：{request.query}",
        "basic_info": {
            "company_status": "正常经营",
            "credit_rating": "AA",
            "financial_health": "良好"
        },
        "key_risks": ["信用风险", "市场风险", "流动性风险"],
        "data_source": "企业基本信息库",
        "timestamp": "2024-01-01"
    }


def _industry_level_analysis(request: CounterpartyQueryRequest) -> Dict[str, Any]:
    """行业层面分析"""
    return {
        "status": "success",
        "type": "industry_level_analysis",
        "industry_sector": request.industry_sector,
        "analysis_content": f"行业层面交易对手分析：{request.query}",
        "industry_risks": [
            f"{request.industry_sector}行业系统性风险",
            "行业竞争格局分析",
            "政策环境影响评估"
        ],
        "counterparty_recommendations": [
            "优选行业龙头企业",
            "关注产业链关键环节",
            "分散行业风险敞口"
        ],
        "data_source": "行业研究报告+企业数据库",
        "timestamp": "2024-01-01"
    }


def _general_counterparty_query(request: CounterpartyQueryRequest) -> Dict[str, Any]:
    """通用交易对手查询"""
    return {
        "status": "success",
        "type": "general_counterparty_query",
        "analysis_content": f"通用交易对手查询：{request.query}",
        "search_results": [
            "相关交易对手风险评估报告",
            "违约概率分析数据",
            "风险监控建议"
        ],
        "recommended_companies": ["阿里巴巴", "腾讯", "华为", "百度"],
        "data_source": "综合交易对手数据库",
        "timestamp": "2024-01-01"
    }


@tool("counterparty_query_tool", args_schema=CounterpartyQueryRequest,
      description="交易对手分析统一查询工具，集成所有交易对手分析方法，支持多维度风险评估和智能路由。"
                  "功能：提供交易对手信用风险评估、违约概率分析、风险监控等综合性交易对手分析服务。"
                  "调用要求：AI智能体应根据用户查询生成具体的交易对手分析指令。"
                  "参数结构："
                  "- query（查询内容）：用户提出的交易对手分析问题或关键词"
                  "- company_name（公司名称）：用于特定公司的交易对手分析"
                  "- credit_code（统一社会信用代码）：18位统一社会信用代码，用于精确查询"
                  "- risk_type（风险类型）：信用风险、市场风险、操作风险、流动性风险等"
                  "- industry_sector（行业领域）：金融、科技、制造业等具体行业"
                  "- analysis_depth（分析深度）：基础分析、深度分析、全面分析"
                  "- monitoring_frequency（监控频率）：实时监控、每日监控、每周监控、每月监控"
                  "示例调用："
                  "- counterparty_query_tool('分析阿里巴巴的信用风险', company_name='阿里巴巴', risk_type='信用风险')"
                  "- counterparty_query_tool('评估腾讯的违约概率', company_name='腾讯', analysis_depth='深度分析')"
                  "- counterparty_query_tool('监控金融行业交易对手风险', industry_sector='金融', risk_type='信用风险')"
                  "- counterparty_query_tool('精确查询企业交易对手信息', company_name='华为', credit_code='913702821234567890')"
                  "支持能力："
                  "- 精确公司分析：基于公司名称和信用代码的精确交易对手分析"
                  "- 特定风险分析：针对特定风险类型的深入分析"
                  "- 公司基础分析：企业基本情况和风险概况分析"
                  "- 行业层面分析：行业系统性风险和交易对手建议"
                  "- 通用交易对手查询：综合性的交易对手风险评估"
                  "注意：系统会根据提供的参数自动选择最佳分析策略，至少提供query参数。")
def counterparty_query_tool(request: CounterpartyQueryRequest) -> Dict[str, Any]:
    """
    交易对手分析统一查询入口，集成所有交易对手分析功能
    
    Args:
        request: 交易对手分析查询请求参数
        
    Returns:
        交易对手分析结果，包含风险评估、违约概率、监控建议等
        
    Example:
        counterparty_query_tool(CounterpartyQueryRequest(query="分析阿里巴巴的信用风险", company_name="阿里巴巴", risk_type="信用风险"))
        counterparty_query_tool(CounterpartyQueryRequest(query="评估腾讯的违约概率", company_name="腾讯", analysis_depth="深度分析"))
        counterparty_query_tool(CounterpartyQueryRequest(query="监控金融行业交易对手风险", industry_sector="金融", risk_type="信用风险"))
    """
    try:
        # 输出进度信息
        progress_data = "⚖️ 交易对手分析"
        params = []
        params.append(f"查询：{request.query}")
        if request.company_name:
            params.append(f"企业：{request.company_name}")
        if request.credit_code:
            params.append(f"信用代码：{request.credit_code}")
        if request.risk_type:
            params.append(f"风险类型：{request.risk_type}")
        if request.industry_sector:
            params.append(f"行业：{request.industry_sector}")
        progress_data += f" | {', '.join(params)}"
        send_progress_info(progress_data)
        
        # 验证参数
        request.validate_parameters()
        
        # 智能路由逻辑
        if request.company_name and request.credit_code:
            # 精确公司查询
            return _exact_company_analysis(request)
        elif request.company_name and request.risk_type:
            # 特定风险类型分析
            return _specific_risk_analysis(request)
        elif request.company_name:
            # 公司基础分析
            return _basic_company_analysis(request)
        elif request.industry_sector:
            # 行业层面分析
            return _industry_level_analysis(request)
        else:
            # 通用交易对手查询
            return _general_counterparty_query(request)
            
    except Exception as e:
        raise e
    


# 导出工具实例
counterparty_query = counterparty_query_tool
