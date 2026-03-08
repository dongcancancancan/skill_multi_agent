"""
简化版 Demo Agent 实现
直接使用 create_react_agent 调度所有工具，让 LLM 根据工具说明自动选择
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from app.utils.logger import logger

# 导入所有工具
from app.multiAgent.tools.case.case_query_tool import case_query_tool
from app.multiAgent.tools.credit.credit_query_tool import credit_query_tool
from app.multiAgent.tools.industry.industry_query_tool import industry_query_tool
from app.multiAgent.tools.counterparty.counterparty_query_tool import counterparty_query_tool
from app.multiAgent.tools.supply_chain.supply_chain_query_tool import supply_chain_query_tool
from app.multiAgent.tools.product.product_policy_query_tool import product_policy_query_tool
from app.multiAgent.tools.product.product_query_tool import product_query_tool
from app.multiAgent.tools.policy.policy_query_tool import policy_query_tool
from app.multiAgent.tools.customer_manager.customer_manager_profile_tool import call_customer_manager_info_tool
from app.multiAgent.tools.enterprise.enterprise_basic_info_tool import enterprise_basic_info_tool_function
from app.multiAgent.tools.blue_green_access.access_query_tool import access_query_tool_function

# 创建内存检查点器
checkpointer = InMemorySaver()

# LLM配置
llm = ChatOpenAI(
    temperature=0.6,
    model="deepseek-chat",
    openai_api_key="sk-058d38c3d7d24749b7325",
    openai_api_base="https://api.deepseek.com/v1",
)

# 定义所有工具列表
ALL_TOOLS = [
    # case_query_tool,
    # credit_query_tool,
    # industry_query_tool,
    # counterparty_query_tool,
    # supply_chain_query_tool,
    # product_policy_query_tool,
    # product_query_tool,
    # call_customer_manager_info_tool,
    # enterprise_basic_info_tool_function,
    # equity_structure_tool_function,
    access_query_tool_function,
    # policy_query_tool
]

# 创建代理 - 直接使用原始工具，让 LLM 根据工具说明自动选择
demo_agent = create_react_agent(
    model=llm,
    tools=ALL_TOOLS,
    prompt=(
        "你是一个多工具调度代理，可以调用各种金融分析工具。\n\n"
        "指令：\n"
        "- 根据用户需求智能选择最合适的工具\n"
        "- 自动生成工具调用参数\n"
        "- 清晰报告工具执行结果\n"
        "- 如果需要人工审批，请在工具中实现中断机制\n"
    ),
    checkpointer=checkpointer,
)

def execute_demo_agent(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行 Demo Agent
    
    Args:
        request: 包含用户输入和会话ID的请求字典
        
    Returns:
        执行结果或中断信息
    """
    session_id = request.get("session_id", str(uuid.uuid4()))
    if not session_id:
        session_id = str(uuid.uuid4())
    user_input = request.get("input", "")
    
    config = {
        "configurable": {
            "thread_id": session_id,
        }
    }
    
    messages = [{"role": "user", "content": user_input}]
    
    logger.info(f"Demo Agent 执行开始 - session_id: {session_id}, input: {user_input}")
    
    try:
        result = demo_agent.invoke(
            {"messages": messages},
            config=config,
        )
        
        # 检查是否包含中断
        if hasattr(result, '__interrupt__') and result.__interrupt__:
            interrupt_data = result.__interrupt__
            logger.info(f"Demo Agent 执行中断 - session_id: {session_id}, 中断类型: {interrupt_data.get('type', 'unknown')}")
            
            return {
                "session_id": session_id,
                "status": "interrupted",
                "message": "需要人工审批工具执行",
                "interruption_type": "tool_approval",
                "interrupt_data": interrupt_data,
                "tool_name": interrupt_data.get("tool", "unknown"),
                "parameters": interrupt_data.get("parameters", {})
            }
        
        logger.info(f"Demo Agent 执行完成 - session_id: {session_id}")
        return {
            "session_id": session_id,
            "result": result,
            "status": "completed",
            "tools_used": _extract_tools_used(result)
        }
        
    except Exception as e:
        if "interrupt" in str(e).lower():
            logger.info(f"Demo Agent 执行中断（异常） - session_id: {session_id}")
            return {
                "session_id": session_id,
                "status": "interrupted",
                "message": "工具执行需要人工审批",
                "interruption_type": "tool_approval"
            }
        else:
            logger.error(f"Demo Agent 执行异常 - session_id: {session_id}, 错误: {str(e)}")
            raise e

def restore_demo_agent(session_id: str, human_feedback: str) -> Dict[str, Any]:
    """
    恢复 Demo Agent 会话
    
    Args:
        session_id: 会话ID
        human_feedback: 人工反馈（审批结果）
        
    Returns:
        恢复后的执行结果
    """
    config = {
        "configurable": {
            "thread_id": session_id,
        }
    }
    
    logger.info(f"Demo Agent 会话恢复 - session_id: {session_id}, feedback: {human_feedback}")
    
    try:
        # 解析人工反馈
        if isinstance(human_feedback, str):
            try:
                feedback_data = json.loads(human_feedback)
            except:
                feedback_data = {"status": human_feedback}
        else:
            feedback_data = human_feedback
            
        # 使用 Command 恢复执行
        result = demo_agent.invoke(
            Command(resume=feedback_data),
            config=config,
        )
        
        logger.info(f"Demo Agent 会话恢复完成 - session_id: {session_id}")
        return {
            "session_id": session_id,
            "result": result,
            "status": "completed",
            "tools_used": _extract_tools_used(result)
        }
        
    except Exception as e:
        logger.error(f"Demo Agent 会话恢复失败 - session_id: {session_id}, 错误: {str(e)}")
        raise e

def _extract_tools_used(result) -> List[str]:
    """从结果中提取使用的工具列表"""
    tools_used = []
    
    if isinstance(result, dict) and 'messages' in result:
        for message in result['messages']:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tools_used.append(tool_call.get('name', 'unknown'))
    
    return list(set(tools_used))

# 请求模型
class DemoAgentRequest(BaseModel):
    """Demo Agent 请求模型"""
    input: str = Field(..., description="用户输入内容")
    session_id: Optional[str] = Field(None, description="会话ID，如不提供将自动生成")

class DemoAgentRestoreRequest(BaseModel):
    """Demo Agent 恢复请求模型"""
    session_id: str = Field(..., description="需要恢复的会话ID")
    human_feedback: str = Field(..., description="人工反馈内容")

if __name__ == "__main__":
    # 测试代码
    test_request = {
        "input": "查询某公司的财务数据和征信信息",
        "session_id": "test_session_001"
    }
    
    result = execute_demo_agent(test_request)
    print("测试结果:", json.dumps(result, indent=2, ensure_ascii=False))
