"""
信用评估统一查询工具
将credit_agent封装为tool，提供统一的信用评估查询入口
集成interrupt参数验证和智能路由逻辑
使用函数式实现，避免重复模型定义
"""

import os
import sys
from typing import Dict, Any
from langchain_core.tools import tool
from langgraph.types import interrupt

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from app.multiAgent.tools.model.credit_model import CreditQueryRequest
from app.multiAgent.common.tool_decorator import with_error_handling
from app.multiAgent.tools.common import send_progress_info
from app.utils.config import get_config
from app.utils.logger import logger


DEFAULT_INFO_TYPE = "信用评估"  # 默认信息类型


@tool("credit_query_tool", args_schema=CreditQueryRequest,
      description="信用评估统一查询工具："
                  "功能："
                  "- 按照企业名称查询信用等级"
                  "示例调用："
                  "- credit_query_tool('山东船沾南朽累智科技闪财公司')"
                  "禁止调用："
                  "- 没有企业名称禁止调用")
@with_error_handling
def credit_query_tool(company: str) -> Dict[str, Any]:
    # 输出进度信息
    progress_data = f"💳 信用评估查询 | 查询：{company}"
    send_progress_info(progress_data)
    
    return "暂无信用评估服务"


# 导出工具实例
credit_tool = credit_query_tool
