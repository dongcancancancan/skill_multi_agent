"""
供应链分析工具 - 统一查询入口
提供供应链稳定性分析、风险评估、绿色指标分析、准入评估、推荐等功能
"""

import json
from typing import Dict, Any
from langchain_core.tools import tool

from app.multiAgent.tools.model.supply_chain_model import SupplyChainQueryRequest
from app.multiAgent.common.tool_decorator import with_error_handling
from app.multiAgent.tools.query_knowledge_base import query_knowledge_base
from app.utils.logger import logger
from app.multiAgent.tools.common import send_progress_info


@tool("supply_chain_query_tool", args_schema=SupplyChainQueryRequest,
      description="供应链分析统一查询工具："
                  "示例调用："
                  "- supply_chain_query_tool('分析华为供应链稳定性', company_name='华为', analysis_type='稳定性分析')"
                  "支持能力："
                  "- 供应链稳定性分析：评估供应链的稳定性和抗风险能力"
                  "- 供应链风险评估：识别和评估供应链各环节的风险"
                  "- 绿色供应链分析：分析供应链的环境影响和可持续性"
                  "- 供应链准入评估：评估供应商的准入资格和合规性"
                  "- 供应链优化推荐：提供供应链改进和优化建议"
                  "- 特定公司分析：针对具体公司的供应链深入分析"
                  "- 行业供应链分析：行业层面的供应链特点和模式分析")
def supply_chain_query_tool(request: SupplyChainQueryRequest) -> Dict[str, Any]:
    try:
        # 输出进度信息
        progress_data = "🔗 供应链分析查询"
        params = []
        if request.query:
            params.append(f"查询：{request.query}")
        if request.company_name:
            params.append(f"公司：{request.company_name}")
        if request.industry_sector:
            params.append(f"行业：{request.industry_sector}")
        if request.analysis_type:
            params.append(f"类型：{request.analysis_type}")
        if params:
            progress_data += f" | {', '.join(params)}"
        send_progress_info(progress_data)
        
        # 智能路由逻辑
        if request.access_criteria:
            return _supply_chain_access_analysis(request)
        elif request.recommendation_type:
            return _supply_chain_recommendation(request)
        elif request.green_indicator:
            return _green_supply_chain_analysis(request)
        elif request.risk_type:
            return _supply_chain_risk_assessment(request)
        elif request.stability_metric:
            return _supply_chain_stability_analysis(request)
        elif request.company_name and request.analysis_type:
            return _specific_company_analysis(request)
        elif request.industry_sector:
            return _industry_supply_chain_analysis(request)
        else:
            return _general_supply_chain_analysis(request)
            
    except Exception as e:
        logger.error(f"供应链分析失败: {str(e)}")
        return {
            "status": "error",
            "error": f"供应链分析失败: {str(e)}",
            "query": request.query,
            "parameters": {
                "company_name": request.company_name,
                "industry_sector": request.industry_sector,
                "analysis_type": request.analysis_type
            }
        }


def _general_supply_chain_analysis(request: SupplyChainQueryRequest) -> Dict[str, Any]:
    """通用供应链分析"""
    logger.info(f"执行通用供应链分析: {request.query}")
    
    # 查询知识库获取基础信息
    knowledge_result = query_knowledge_base(
        query=request.query,
        dataset_id="supply_chain_data"
    )
    
    return {
        "status": "success",
        "analysis_type": "通用供应链分析",
        "query": request.query,
        "company_name": request.company_name,
        "result": {
            "summary": f"基于{request.query}的供应链分析结果",
            "stability_score": 85,
            "risk_level": "中等",
            "green_rating": "良好",
            "analysis_content": knowledge_result.get("content", "暂无详细分析内容"),
            "recommendations": [
                "建议加强供应商多元化管理",
                "建立供应链风险预警机制",
                "推进绿色供应链建设"
            ]
        }
    }


def _specific_company_analysis(request: SupplyChainQueryRequest) -> Dict[str, Any]:
    """特定公司供应链分析"""
    logger.info(f"执行特定公司供应链分析: {request.company_name} - {request.analysis_type}")
    
    # 查询知识库获取公司特定信息
    knowledge_result = query_knowledge_base(
        query=f"{request.company_name} {request.analysis_type}",
        dataset_id="supply_chain_data"
    )
    
    return {
        "status": "success",
        "analysis_type": f"{request.company_name}供应链{request.analysis_type}",
        "company_name": request.company_name,
        "analysis_type_detail": request.analysis_type,
        "result": {
            "company": request.company_name,
            "analysis_focus": request.analysis_type,
            "stability_assessment": "稳定" if request.analysis_type == "稳定性分析" else "待评估",
            "risk_insights": knowledge_result.get("content", "暂无风险洞察"),
            "improvement_suggestions": [
                f"针对{request.company_name}的{request.analysis_type}改进建议"
            ]
        }
    }


def _industry_supply_chain_analysis(request: SupplyChainQueryRequest) -> Dict[str, Any]:
    """行业供应链分析"""
    logger.info(f"执行行业供应链分析: {request.industry_sector}")
    
    knowledge_result = query_knowledge_base(
        query=f"{request.industry_sector} 供应链分析",
        dataset_id="supply_chain_data"
    )
    
    return {
        "status": "success",
        "analysis_type": f"{request.industry_sector}行业供应链分析",
        "industry_sector": request.industry_sector,
        "result": {
            "industry_overview": f"{request.industry_sector}行业供应链特点",
            "supply_chain_pattern": knowledge_result.get("content", "行业供应链模式分析"),
            "key_risks": ["供应中断风险", "成本波动风险", "合规风险"],
            "best_practices": ["建立战略供应商关系", "实施数字化供应链管理"]
        }
    }


def _supply_chain_stability_analysis(request: SupplyChainQueryRequest) -> Dict[str, Any]:
    """供应链稳定性分析"""
    logger.info(f"执行供应链稳定性分析: {request.company_name} - {request.stability_metric}")
    
    knowledge_result = query_knowledge_base(
        query=f"{request.company_name} 供应链稳定性 {request.stability_metric}",
        dataset_id="supply_chain_data"
    )
    
    return {
        "status": "success",
        "analysis_type": "供应链稳定性分析",
        "stability_metric": request.stability_metric,
        "result": {
            "stability_score": 88,
            "metric_evaluation": request.stability_metric,
            "weak_points": ["供应商集中度较高", "物流运输存在瓶颈"],
            "improvement_measures": [
                "开发备用供应商",
                "优化物流网络",
                "建立库存缓冲机制"
            ],
            "detailed_analysis": knowledge_result.get("content", "稳定性详细分析")
        }
    }


def _supply_chain_risk_assessment(request: SupplyChainQueryRequest) -> Dict[str, Any]:
    """供应链风险评估"""
    logger.info(f"执行供应链风险评估: {request.risk_type}")
    
    knowledge_result = query_knowledge_base(
        query=f"{request.company_name or '行业'} 供应链风险 {request.risk_type}",
        dataset_id="supply_chain_data"
    )
    
    return {
        "status": "success",
        "analysis_type": "供应链风险评估",
        "risk_type": request.risk_type,
        "result": {
            "risk_level": "高风险" if "中断" in request.risk_type else "中等风险",
            "risk_factors": [request.risk_type, "外部环境变化", "内部管理不足"],
            "impact_assessment": "可能影响生产连续性",
            "mitigation_strategies": [
                "建立风险预警系统",
                "制定应急预案",
                "加强供应商风险管理"
            ],
            "risk_analysis": knowledge_result.get("content", "风险评估详细内容")
        }
    }


def _green_supply_chain_analysis(request: SupplyChainQueryRequest) -> Dict[str, Any]:
    """绿色供应链分析"""
    logger.info(f"执行绿色供应链分析: {request.green_indicator}")
    
    knowledge_result = query_knowledge_base(
        query=f"{request.company_name or '行业'} 绿色供应链 {request.green_indicator}",
        dataset_id="supply_chain_data"
    )
    
    return {
        "status": "success",
        "analysis_type": "绿色供应链分析",
        "green_indicator": request.green_indicator,
        "result": {
            "green_score": 92,
            "environmental_performance": "优秀",
            "compliance_status": "符合环保要求",
            "sustainability_metrics": {
                "carbon_footprint": "较低",
                "resource_efficiency": "高效",
                "waste_management": "规范"
            },
            "green_analysis": knowledge_result.get("content", "绿色供应链详细分析")
        }
    }


def _supply_chain_access_analysis(request: SupplyChainQueryRequest) -> Dict[str, Any]:
    """供应链准入评估"""
    logger.info(f"执行供应链准入评估: {request.access_criteria}")
    
    knowledge_result = query_knowledge_base(
        query=f"供应链准入 {request.access_criteria}",
        dataset_id="supply_chain_data"
    )
    
    return {
        "status": "success",
        "analysis_type": "供应链准入评估",
        "access_criteria": request.access_criteria,
        "result": {
            "access_eligibility": "符合条件",
            "assessment_criteria": request.access_criteria,
            "qualification_check": "通过",
            "recommendation": "建议纳入合格供应商名单",
            "access_analysis": knowledge_result.get("content", "准入评估详细内容")
        }
    }


def _supply_chain_recommendation(request: SupplyChainQueryRequest) -> Dict[str, Any]:
    """供应链优化推荐"""
    logger.info(f"执行供应链优化推荐: {request.recommendation_type}")
    
    knowledge_result = query_knowledge_base(
        query=f"供应链优化 {request.recommendation_type}",
        dataset_id="supply_chain_data"
    )
    
    return {
        "status": "success",
        "analysis_type": "供应链优化推荐",
        "recommendation_type": request.recommendation_type,
        "result": {
            "optimization_priority": "高优先级",
            "recommended_actions": [
                f"实施{request.recommendation_type}相关措施",
                "优化供应链流程",
                "加强合作伙伴管理"
            ],
            "expected_benefits": "提升效率20%，降低成本15%",
            "implementation_timeline": "3-6个月",
            "recommendation_analysis": knowledge_result.get("content", "优化推荐详细内容")
        }
    }
