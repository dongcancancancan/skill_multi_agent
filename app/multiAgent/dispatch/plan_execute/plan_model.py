"""
计划数据模型与辅助函数

该模块集中定义Plan-and-Execute流程使用的结构化计划数据结构，
并提供常用的状态读写与更新工具函数。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional, Sequence

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    """执行步骤的极简结构"""

    stepId: str = Field(
        ...,
        description="步骤ID，格式：step-001, step-002, ...",
    )
    goal: str = Field(
        ...,
        description="该步骤要完成的目标或要解决的问题",
    )
    handoffTarget: str = Field(
        ...,
        description="建议交接的团队或工具标识",
    )


class PlanState(BaseModel):
    """结构化计划状态"""

    planId: str
    summary: str
    steps: list[PlanStep]
    completedSteps: list[str] = Field(default_factory=list)
    nextStepId: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    comment: Optional[str] = None
    stepRetryCount: dict[str, int] = Field(
        default_factory=dict,
        description="记录每个步骤的重试次数，键为stepId，值为重试次数。用于防止redo死循环。",
    )
    stepResults: dict[str, str] = Field(
        default_factory=dict,
        description="每个步骤的执行结果摘要，键为stepId，值为执行结果文本。",
    )
    thinking: Optional[str] = Field(
        default=None,
        description="LLM的思考过程记录，便于调试和分析",
    )


def build_plan_state(
    plan_id: str,
    summary: str,
    steps: Sequence[PlanStep],
    thinking: Optional[str] = None,
) -> PlanState:
    """
    根据plan工具输出构造PlanState实例。
    """
    if not steps:
        raise ValueError("plan steps cannot be empty")

    next_step_id = steps[0].stepId
    return PlanState(
        planId=plan_id,
        summary=summary,
        steps=list[PlanStep](steps),
        completedSteps=[],
        nextStepId=next_step_id,
        status="pending",
        comment=None,
        updatedAt=datetime.now(timezone.utc),
        thinking=thinking,
    )


def mark_plan_decision(
    plan: PlanState,
    approved: bool,
    comment: Optional[str] = None,
) -> PlanState:
    """
    根据人工审批结果更新PlanState。
    """
    decision = "approved" if approved else "rejected"
    return plan.model_copy(
        update={
            "status": decision,
            "comment": comment,
            "updatedAt": datetime.now(timezone.utc),
        }
    )


def plan_state_to_dict(plan: PlanState) -> dict:
    """转换为可序列化字典（ISO时间字符串）"""
    # 检查是否是 Pydantic 模型且支持 model_dump 方法
    if hasattr(plan, 'model_dump') and callable(getattr(plan, 'model_dump', None)):
        try:
            return plan.model_dump(mode="json")
        except (AttributeError, TypeError):
            # 如果 model_dump 失败，回退到其他序列化方法
            return _fallback_serialize(plan)
    else:
        # 如果不是 Pydantic 模型，尝试直接转换
        return _fallback_serialize(plan)


def _fallback_serialize(obj) -> dict:
    """回退序列化方法"""
    if hasattr(obj, '__dict__'):
        result = dict(obj.__dict__)
        # 处理 datetime 对象
        for key, value in result.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
        return result
    elif hasattr(obj, 'dict'):
        return obj.dict()
    else:
        return {}


__all__ = [
    "PlanStep",
    "PlanState",
    "build_plan_state",
    "mark_plan_decision",
    "plan_state_to_dict",
]
