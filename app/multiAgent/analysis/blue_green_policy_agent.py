"""
基于LangGraph的蓝绿政策分析Agent
与企业画像agent设计模式保持一致，支持中断功能
"""

from typing import Dict, Any, Annotated
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, MessagesState, END
from langgraph.types import Command, interrupt, Interrupt
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from app.utils.logger import agent_logger as logger
from app.utils.llm import get_llm
from langchain_core.runnables import RunnableConfig
import uuid
from datetime import datetime
import json

# 中断工具
@tool
def human_review_tool(query: str) -> str:
    """用户审查节点，用于批准政策分析请求"""
    answer = interrupt("approve or reject?")
    logger.info(f"获得人工审核结果: {answer}")
    return answer

class BlueGreenPolicyAgent:
    """蓝绿政策分析Agent - 与企业画像agent设计模式完全一致"""
    
    def __init__(self, checkpointer=None):
        self.llm = get_llm()
        self.name = "blue_green_policy_agent"
        self.checkpointer = checkpointer or InMemorySaver()
        
        # 工具列表
        self.tools = [human_review_tool]
        self.tool_node = ToolNode(self.tools)
        
        # 创建LangGraph图
        self.graph = self._build_policy_graph()

    def _build_policy_graph(self):
        """构建政策分析LangGraph图结构 - 与企业画像agent一致的两节点模式"""
        logger.info("构建政策分析LangGraph图结构 - 两节点模式")
        
        # 构建图
        builder = StateGraph(MessagesState)
        
        # 添加两个核心节点
        builder.add_node("call_llm", self.call_llm_node)
        builder.add_node("tools", self.tool_node)
        
        # 设置起始节点
        builder.add_edge(START, "call_llm")
        
        # 添加条件边：根据LLM输出决定是否调用工具
        builder.add_conditional_edges(
            "call_llm",
            self.should_call_tools,
            {
                "tools": "tools",
                "continue": END
            }
        )
        
        # 工具节点后直接返回到call_llm节点
        builder.add_edge("tools", "call_llm")
        
        # 编译图
        return builder.compile(checkpointer=self.checkpointer)

    def call_llm_node(self, state: MessagesState, config: RunnableConfig) -> MessagesState:
        """调用LLM节点 - 让LLM决定是否需要人工审核"""
        logger.info("执行LLM调用节点 - 政策分析")
        
        # 准备系统提示
        system_prompt = SystemMessage(
            "你是一个对公金融政策分析专家。\n\n"
            "INSTRUCTIONS:\n"
            "- 需要先批准用户的政策分析请求\n"
            "- 只处理对公金融政策相关任务\n"
            "- 分析政策适用性、合规性和实施建议\n"
            "- 完成后直接返回分析结果\n"
            "- 只返回工作结果，不要包含其他文本"
        )
        
        # 绑定工具到LLM
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 调用LLM
        response = llm_with_tools.invoke([system_prompt] + state["messages"], config)
        
        return {"messages": [response]}

    def should_call_tools(self, state: MessagesState) -> str:
        """判断是否需要调用工具 - 基于LLM的输出"""
        logger.info("判断是否需要调用工具 - 政策分析")
        
        if not state.get("messages"):
            logger.info("没有消息，继续执行")
            return "continue"
        
        # 获取最新的AI消息
        last_message = state["messages"][-1]
        
        # 检查是否有工具调用
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            logger.info(f"检测到工具调用，需要调用工具: {last_message.tool_calls}")
            return "tools"
        
        # 检查消息内容中是否包含工具调用指示
        if hasattr(last_message, 'content') and last_message.content:
            content = last_message.content.lower()
            if "tool" in content or "human_review" in content or "人工审核" in content:
                logger.info("消息内容指示需要工具调用")
                return "tools"
        
        logger.info("没有工具调用指示，继续执行")
        return "continue"

    def run(self, request: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """执行政策分析 - 与企业画像agent接口完全一致"""
        try:
            # 验证参数结构
            if "input" not in request:
                return {
                    "status": "error",
                    "error": "无效的请求参数，必须包含input字段"
                }
            
            # 从config获取session_id，如果不存在则生成新的
            session_id = config["configurable"].get("thread_id") if config and config.get("configurable") else request.get("session_id", str(uuid.uuid4()))
            
            # 创建初始状态
            initial_state = self._create_initial_state(request, session_id)
            logger.info(f"开始执行政策分析，session_id: {session_id}")
            
            # 执行图
            final_state = self.graph.invoke(initial_state, config)
            
            # 检查是否中断
            if hasattr(final_state, '__interrupt__') and final_state.__interrupt__:
                logger.info(f"检测到中断状态: {final_state.__interrupt__}")
                return {
                    "status": "interrupted",
                    "interrupt_data": final_state.__interrupt__,
                    "session_id": session_id
                }
            
            # 从消息中提取最终响应
            messages = final_state.get("messages", [])
            if not messages:
                return {
                    "status": "error",
                    "error": "未生成任何响应消息",
                    "session_id": session_id
                }
            
            # 获取最后一条AI消息作为响应
            last_ai_message = None
            for msg in reversed(messages):
                if hasattr(msg, 'type') and msg.type == 'ai':
                    last_ai_message = msg
                    break
            
            if not last_ai_message:
                return {
                    "status": "error",
                    "error": "未找到有效的AI响应消息",
                    "session_id": session_id
                }
            
            # 构建标准化响应
            return {
                "status": "success",
                "result": last_ai_message.content,
                "analysis_type": "policy_analysis",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id
            }
            
        except Interrupt as e:
            # 直接捕获Interrupt异常并重新抛出，让统一Supervisor处理
            logger.info(f"检测到中断异常，重新抛出让父节点处理: {e}")
            raise e
            
        except Exception as e:
            logger.error(f"政策分析失败: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "session_id": config["configurable"].get("thread_id") if config and config.get("configurable") else request.get("session_id", str(uuid.uuid4()))
            }

    def _create_initial_state(self, request: Dict[str, Any], session_id: str) -> MessagesState:
        """创建初始状态"""
        request_message = HumanMessage(content=request["input"])
        return {
            "messages": [request_message],
            "session_id": session_id
        }
