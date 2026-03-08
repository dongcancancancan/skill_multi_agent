"""
客户经理画像工具模块
"""

from typing import Dict, Any
from langchain_core.tools import tool
from app.utils.logger import logger
from app.multiAgent.tools.common import send_progress_info


@tool(description="客户经理信息查询工具：由AI智能体调用的客户经理基本信息查询功能。"
                  "功能：提供客户经理基本信息查询服务，包括姓名、年龄、工作年限、部门、联系方式等。"
                  "调用要求：AI智能体应根据当前对话上下文生成具体的客户经理查询指令。"
                  "参数结构："
                  "- manager_name（客户经理姓名）：客户经理的姓名，可选参数，默认为'张三'"
                  "示例调用："
                  "- call_customer_manager_info_tool('张三')"
                  "- call_customer_manager_info_tool('李四')"
                  "- call_customer_manager_info_tool()  # 使用默认值"
                  "支持能力："
                  "- 客户经理基本信息查询：包括姓名、年龄、工作年限、所属部门、联系方式等"
                  "- 快速信息检索：无需复杂分析，直接返回客户经理基本信息"
                  "- 默认值支持：当不提供manager_name时，返回默认客户经理信息"
                  "注意：此工具主要用于快速获取客户经理基本信息，适用于需要联系客户经理或了解客户经理背景的场景。")
def call_customer_manager_info_tool(manager_name: str = "张三") -> Dict[str, Any]:
    """客户经理信息查询工具 - 直接接收参数"""
    # 输出进度信息
    progress_data = "👤 客户经理信息查询"
    if manager_name and manager_name != "张三":
        progress_data += f" | 经理：{manager_name}"
    send_progress_info(progress_data)
    logger.info(f"调用客户经理信息查询工具: manager_name={manager_name}")
    
    # 直接返回固定的客户经理信息
    return {
        "status": "success",
        "data": {
            "manager_name": manager_name,
            "age": 35,
            "work_experience": "10年",
            "department": "企业金融部",
            "contact": f"{manager_name.lower()}@bank.com"
        }
    }


# 导出工具
__all__ = ["call_customer_manager_info_tool"]
