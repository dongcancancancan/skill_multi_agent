"""
统一状态定义

在消息驱动架构基础上，为Plan-and-Execute工作流增加结构化plan字段。
"""

from __future__ import annotations

from typing import Optional, TypedDict, NotRequired, Annotated, Any

from langchain_core.messages import HumanMessage
from langgraph.graph.message import AnyMessage, add_messages


class UniState(TypedDict, total=False):
    """
    统一状态结构

    - messages: LangGraph默认的消息累加器
    - plan: 当前会话的结构化计划（可选）
    - agent_first_call_flag: 跟踪每个agent是否已完成首次调用（用于tool_choice优化）
    """

    messages: Annotated[list[AnyMessage], add_messages]
    plan: NotRequired[dict | None]
    session_status: NotRequired[dict | None]
    agent_first_call_flag: NotRequired[dict[str, bool]]
    approval_result: NotRequired[bool]
    report_summary: NotRequired[str | None]
    rag_history: NotRequired[dict | None]
    routing_decision: NotRequired[Any]  # 存储 RouterDecision 对象或其他决策对象


class StateFields:
    """状态字段名称常量"""

    MESSAGES = "messages"
    PLAN = "plan"
    SESSION_STATUS = "session_status"
    AGENT_FIRST_CALL_FLAG = "agent_first_call_flag"
    APPROVAL_RESULT = "approval_result"
    REPORT_SUMMARY = "report_summary"
    RAG_HISTORY = "rag_history"
    ROUTING_DECISION = "routing_decision"


def create_initial_state(user_input: str, session_id: Optional[str] = None) -> UniState:
    initial_message = HumanMessage(
        content=user_input,
        metadata={"session_id": session_id} if session_id else {},
    )

    return {
        StateFields.MESSAGES: [initial_message],
        StateFields.PLAN: None,
    }
