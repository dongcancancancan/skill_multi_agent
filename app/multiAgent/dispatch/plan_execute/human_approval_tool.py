"""
计划人工审批工具

作为Supervisor绑定的工具，触发人工“通过/拒绝”确认，并将结果写回state.plan。
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from typing import Annotated, Any, Optional

from langchain_core.messages import ToolMessage, AIMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command, interrupt
from langgraph.graph import END
from langgraph.errors import GraphBubbleUp

from app.multiAgent.common.uni_state import StateFields, UniState
from app.multiAgent.dispatch.plan_execute.plan_model import (
    PlanState,
    mark_plan_decision,
    plan_state_to_dict,
)
from app.utils.logger import logger


def create_human_approval_tool():
    """
    创建人工审批工具，仅支持“通过/拒绝”。
    """

    description = """
人工审批工具
- 读取 state.plan，触发中断等待“通过/拒绝”
- 根据用户选择更新计划并返回 human_approval_result
"""

    def human_approval_impl(
        state: Annotated[UniState, InjectedState] = None,
        tool_call_id: Annotated[str, InjectedToolCallId] = "",
    ) -> Command:
        try:
            plan_data = state.get(StateFields.PLAN)
            if not plan_data:
                raise ValueError("当前状态中不存在待审批的计划")

            plan = PlanState.model_validate(plan_data)
            if plan.status != "pending":
                raise ValueError("当前计划已处理，无需再次审批")

            # 防御性处理：确保计划对象可以被正确序列化
            # 检查是否是 Pydantic 模型且支持 model_dump 方法
            if hasattr(plan, "model_dump") and callable(getattr(plan, "model_dump", None)):
                try:
                    plan_dict = plan.model_dump(mode="json")
                except (AttributeError, TypeError):
                    # 如果 model_dump 失败，回退到其他序列化方法
                    plan_dict = plan_state_to_dict(plan)
            else:
                # 如果不是 Pydantic 模型，尝试直接转换
                plan_dict = plan_state_to_dict(plan)

            # 仅用于向前端展示的副本，避免修改原始计划数据
            plan_display_dict = _build_plan_display(plan_dict)

            interrupt_payload = {
                "type": "human_approval_required",
                "css_type": "radioButton",
                "plan": plan_display_dict,
                "requested_at": datetime.now().isoformat(),
                "available_actions": [
                    {
                        "type": "approve",
                        "label": "通过计划",
                        "description": "确认计划内容并继续执行",
                    },
                    {
                        "type": "reject",
                        "label": "拒绝计划",
                        "description": "拒绝当前计划并终止执行",
                    },
                ],
            }

            logger.info(
                f"[HumanApprovalTool] Triggering interrupt for plan {plan.planId}"
            )
            user_decision = interrupt(interrupt_payload)

            decision, comment = _parse_user_decision(user_decision)
            approved = decision == "approve"
            updated_plan = mark_plan_decision(plan, approved, comment)
            plan_dict = plan_state_to_dict(updated_plan)

            result_payload = {
                "type": "human_approval_result",
                "planId": updated_plan.planId,
                "status": updated_plan.status,
                "comment": comment,
                "completed_at": datetime.now().isoformat(),
            }

            tool_message = ToolMessage(
                content=json.dumps(result_payload, ensure_ascii=False, indent=2),
                name="human_approval",
                tool_call_id=tool_call_id,
            )

            current_messages = list(state.get(StateFields.MESSAGES, []))
            updated_messages = current_messages + [tool_message]

            update_payload = {
                **state,
                StateFields.MESSAGES: updated_messages,
                StateFields.PLAN: plan_dict if approved else None,
            }

            if not approved:
                rejection_reason = (comment or "").strip()
                rejection_text = "人工审批已拒绝该计划，本次流程结束。"
                if rejection_reason:
                    rejection_text += f" 原因：{rejection_reason}"

                rejection_ai_message = AIMessage(content=rejection_text)
                session_status_payload = {
                    "status": "locked",
                    "message": rejection_text,
                    "source": "plan_rejected",
                    "reason": rejection_reason or None,  # 保留用户拒绝原因
                    "locked_at": datetime.now().isoformat(),
                }

                update_payload[StateFields.MESSAGES] = updated_messages + [
                    rejection_ai_message
                ]
                update_payload[StateFields.SESSION_STATUS] = session_status_payload
                command_kwargs = {"update": update_payload, "goto": END}
            else:
                update_payload[StateFields.APPROVAL_RESULT] = True
                command_kwargs = {"update": update_payload}
            return Command(**command_kwargs)

        except GraphBubbleUp:
            raise
        except Exception as exc:
            logger.error(f"[HumanApprovalTool] Error: {exc}", exc_info=True)
            error_payload = {
                "type": "human_approval_error",
                "error": str(exc),
                "timestamp": datetime.now().isoformat(),
            }
            error_message = ToolMessage(
                content=json.dumps(error_payload, ensure_ascii=False),
                name="human_approval",
                tool_call_id=tool_call_id,
            )
            current_messages = list(state.get(StateFields.MESSAGES, []))
            return Command(
                update={StateFields.MESSAGES: current_messages + [error_message]}
            )

    return tool(
        "human_approval",
        description=description,
    )(human_approval_impl)


def _parse_user_decision(decision_input: Any) -> tuple[str, Optional[str]]:
    """
    将输入标准化为 ('approve' | 'reject', comment)。
    """
    decision = None
    comment: Optional[str] = None

    if isinstance(decision_input, dict):
        decision = decision_input.get("decision")
        comment = decision_input.get("comment")
    elif isinstance(decision_input, str):
        decision, comment = _parse_text_decision(decision_input)
    else:
        decision, comment = _parse_text_decision(str(decision_input))

    if decision not in {"approve", "reject"}:
        raise ValueError("人工审批仅支持'approve'或'reject'")

    return decision, comment


def _parse_text_decision(text: str) -> tuple[str, Optional[str]]:
    lowered = text.lower().strip()
    comment = text if text else None

    approve_keywords = [
        "同意",
        "确认",
        "通过",
        "ok",
        "yes",
        "approve",
        "y",
        "confirm",
    ]
    reject_keywords = [
        "拒绝",
        "不同意",
        "否",
        "no",
        "reject",
        "cancel",
        "deny",
    ]

    if any(keyword in lowered for keyword in approve_keywords):
        return "approve", comment
    if any(keyword in lowered for keyword in reject_keywords):
        return "reject", comment

    raise ValueError("无法识别的人工审批输入，请明确回复通过或拒绝")


def _build_plan_display(plan_dict: dict) -> dict:
    """构造仅用于展示的计划副本，为步骤ID提供更友好的中文文案"""
    display_plan = deepcopy(plan_dict)
    steps = display_plan.get("steps") or []

    for idx, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            continue
        original_id = step.get("stepId")
        step["rawStepId"] = original_id
        step["stepId"] = f"步骤{idx}"

    return display_plan


__all__ = ["create_human_approval_tool"]
