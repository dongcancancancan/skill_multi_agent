"""
案例库查询工具 - 知识库查询入口
提供案例库查询功能，支持对公金融相关案例库查询
"""

import json
from typing import Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.multiAgent.tools.query_knowledge_base import query_knowledge_base
from app.multiAgent.common.tool_decorator import with_error_handling
from app.multiAgent.tools.common import send_progress_info
import asyncio
from app.utils.logger import logger
from app.utils.config import get_config


# 从配置文件读取案例库ID
# 环境配置通过config/[sit|uat].yaml管理
DATASET_ID = get_config("knowledge.case_dataset_id")

if not DATASET_ID:
    logger.warning(
        "案例库ID未配置！请在config文件中设置knowledge.case_dataset_id\n"
        "工具将以占位符模式加载，实际调用时可能失败。"
    )
    DATASET_ID = "case_dataset_placeholder"  # 使用占位符，允许模块加载
elif "placeholder" in DATASET_ID.lower():
    logger.warning(
        f"案例库ID使用占位符: {DATASET_ID}\n"
        f"请在config/{{env}}.yaml中配置实际的case_dataset_id"
    )


class CaseQueryInput(BaseModel):
    """案例查询输入参数模型"""
    query: str = Field(description="查询关键词")
    case_type: str = Field(description="案例类型", default=None)
    industry_sector: str = Field(description="行业领域", default=None)


@tool("case_query_tool", args_schema=CaseQueryInput,
      description="案例库查询工具："
                  "示例调用："
                  "- case_query_tool('对公金融典型案例分析')"
                  "功能："
                  "- 绿色信贷案例查询：绿色项目融资、环保企业贷款等成功案例"
                  "- 环保项目案例查询：节能减排、生态保护、清洁能源等项目案例"
                  "- 可持续发展案例查询：企业社会责任、绿色转型等案例"
                  "- 行业案例分析：特定行业的对公金融实践案例"
                  "- 最佳实践分享：对公金融领域的成功经验和模式")
@with_error_handling
def case_query_tool(query: str, case_type: str = None, industry_sector: str = None) -> Dict[str, Any]:
    # 输出进度信息
    progress_data = "📚 案例库查询"
    params = []
    params.append(f"关键词：{query}")
    if case_type:
        params.append(f"类型：{case_type}")
    if industry_sector:
        params.append(f"行业：{industry_sector}")
    progress_data += f" | {', '.join(params)}"
    send_progress_info(progress_data)
    
    search_query = query
    if case_type:
        search_query = f"{case_type} {search_query}"
    if industry_sector:
        search_query = f"{industry_sector} {search_query}"
    
    # 查询知识库获取案例信息（使用异步调用）
    knowledge_result = asyncio.run(query_knowledge_base(
        query=search_query,
        dataset_id=DATASET_ID
    ))
    
    return {
        "status": "success",
        "query": query,
        "search_query": search_query,
        "dataset_id": DATASET_ID,
        "result": {
            "content": knowledge_result.get("content", "未找到相关案例"),
            "metadata": {
                "case_type": case_type,
                "industry_sector": industry_sector,
                "search_timestamp": "2025-09-24T00:00:00Z"
            }
        }
    }
