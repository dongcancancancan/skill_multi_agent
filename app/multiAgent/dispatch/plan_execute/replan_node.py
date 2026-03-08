"""
Replan节点：基于LLM反馈更新计划完成进度，并将执行权交还给Supervisor。
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.types import Command
from pydantic import create_model

from app.multiAgent.common.uni_state import StateFields, UniState
from app.multiAgent.dispatch.plan_execute.plan_model import (
    PlanState,
    plan_state_to_dict,
)
from app.utils.llm import get_llm
from app.utils.logger import logger

# 最大步骤重试次数：防止redo死循环
# 如果某个步骤连续被判定为redo达到此上限，将强制advance到下一步骤
MAX_STEP_RETRIES = 2  # 共3次尝试机会（初始执行 + 2次重试）

ReplanOutput = create_model(
    "ReplanOutput",
    completed_steps=(List[str], []),
    progress_mode=(str, "redo"),
)

replan_prompt = ChatPromptTemplate.from_template(
    """你是计划执行进度判定节点，负责判断当前步骤是否已完成。

【计划步骤】
{plan_steps}

【已完成步骤及执行结果】
{past_steps_with_results}

请判断当前步骤的执行情况：
- 如果当前步骤已圆满完成，返回 progress_mode="advance"，并在completed_steps中包含该步骤
- 如果当前步骤需要重做或补充，返回 progress_mode="redo"，保持completed_steps不变
- completed_steps必须是已完成步骤的连续序列（按计划顺序）

输出JSON格式：
{{
  "completed_steps": ["step-001", ...],
  "progress_mode": "advance" 或 "redo"
}}
"""
)


def create_replan_node():
    structured_llm = get_llm().with_structured_output(ReplanOutput, method="json_mode")
    replanner = replan_prompt | structured_llm

    def replan_node(state: UniState, config: RunnableConfig) -> Command:
        plan_data = state.get(StateFields.PLAN)
        if not plan_data:
            raise ValueError("Replan节点被调用时缺少计划数据，无法继续调度。")

        plan = PlanState.model_validate(plan_data)
        messages = list(state.get(StateFields.MESSAGES, []))

        # 团队执行完成后会回到replan，此时提取最后一条消息作为执行结果
        current_step_id = plan.nextStepId or ""
        if current_step_id and messages:
            # 提取最后一条消息内容作为执行结果
            last_message = messages[-1]
            result_text = ""
            if hasattr(last_message, "content") and last_message.content:
                result_text = str(last_message.content)

            # 只有当结果非空时才记录（避免记录空消息）
            if result_text.strip():
                # 更新stepResults（通过model_copy创建新实例）
                step_results = dict(plan.stepResults or {})
                step_results[current_step_id] = result_text
                plan = plan.model_copy(update={"stepResults": step_results})
                logger.info(
                    f"[ReplanNode] 记录步骤[{current_step_id}]执行结果（前50字符）：{result_text[:50]}..."
                )

        # 构建提示输入
        prompt_input = {
            "plan_steps": "\n".join(
                f"{i}. [{step.stepId}] {step.goal}"
                for i, step in enumerate(plan.steps, 1)
            ),
            "past_steps_with_results": _format_past_steps_with_results(plan),
        }

        logger.debug(f"[ReplanNode] 调用LLM判定计划进度：{json.dumps(prompt_input)}")
        decision = replanner.invoke(prompt_input, config)
        decision_data = (
            decision.model_dump()
            if hasattr(decision, "model_dump")
            else dict(decision or {})
        )

        previous_completed = list(plan.completedSteps)
        step_ids = [step.stepId for step in plan.steps]
        step_id_set = set(step_ids)

        expected_current = plan.nextStepId or ""
        if not expected_current:
            for sid in step_ids:
                if sid not in previous_completed:
                    expected_current = sid
                    break

        predicted_steps = decision_data.get("completed_steps", [])
        normalized_steps, is_valid_sequence = _validate_completed(plan, predicted_steps)
        progress_mode_raw = (
            (decision_data.get("progress_mode", "redo") or "redo").strip().lower()
        )
        progress_mode = (
            progress_mode_raw if progress_mode_raw in {"advance", "redo"} else "redo"
        )

        final_mode = progress_mode
        final_completed = list(previous_completed)

        if not is_valid_sequence:
            logger.warning(
                f"[ReplanNode] LLM返回的completed_steps {predicted_steps} 无法匹配计划顺序，保持原状态"
            )
            final_mode = "redo"
        elif progress_mode == "advance":
            new_steps = normalized_steps[len(previous_completed) :]
            if not new_steps:
                logger.warning(
                    f"[ReplanNode] 推进决策却未新增完成步骤（预测={normalized_steps}，历史={previous_completed}），改为redo"
                )
                final_mode = "redo"
            elif (
                previous_completed
                and normalized_steps[: len(previous_completed)] != previous_completed
            ):
                logger.warning(
                    f"[ReplanNode] 推进决策缺少历史前缀（预测={normalized_steps}，历史={previous_completed}），改为redo"
                )
                final_mode = "redo"
            elif expected_current and new_steps[0] != expected_current:
                logger.warning(
                    f"[ReplanNode] 推进决策新增的首个步骤 '{new_steps[0]}' 与当前目标 '{expected_current}' 不一致，改为redo"
                )
                final_mode = "redo"
            else:
                final_completed = normalized_steps
        else:
            final_mode = "redo"

        if final_mode == "redo":
            final_completed = list(previous_completed)
            if len(previous_completed) == len(step_ids) and previous_completed:
                reopened_step = previous_completed[-1]
                final_completed = previous_completed[:-1]
                logger.info(
                    f"[ReplanNode] 计划已全部完成但收到redo，重新开放末尾步骤 {reopened_step}"
                )

        completed_steps = final_completed

        if final_mode == "advance":
            added_steps = completed_steps[len(previous_completed) :]
            if added_steps:
                logger.info(f"[ReplanNode] 本轮确认新增完成步骤: {added_steps}")

        first_incomplete = ""
        for sid in step_ids:
            if sid not in completed_steps:
                first_incomplete = sid
                break

        next_step_id = first_incomplete if first_incomplete else ""
        all_steps_completed = len(completed_steps) == len(step_ids)
        if all_steps_completed:
            next_step_id = ""

        if next_step_id and next_step_id not in step_id_set:
            logger.warning(
                f"[ReplanNode] 校验nextStepId失败：'{next_step_id}' 不在计划步骤中（有效步骤: {step_ids}），将其置空"
            )
            next_step_id = ""

        # ===== 重试次数检查与强制advance逻辑 =====
        step_retry_count = dict(plan.stepRetryCount or {})  # 复制一份，避免修改原对象
        current_step_id = next_step_id or expected_current

        if final_mode == "redo" and current_step_id:
            # redo场景：检查重试次数
            current_retry_count = step_retry_count.get(current_step_id, 0)

            if current_retry_count >= MAX_STEP_RETRIES:
                # 达到重试上限，强制advance
                logger.warning(
                    f"[ReplanNode] 步骤[{current_step_id}]已重试{current_retry_count}次"
                    f"（>= 上限{MAX_STEP_RETRIES}），强制推进到下一步骤"
                )
                final_mode = "advance"
                # 将当前步骤标记为完成
                completed_steps = list(previous_completed) + [current_step_id]

                # 重新计算next_step_id
                first_incomplete = ""
                for sid in step_ids:
                    if sid not in completed_steps:
                        first_incomplete = sid
                        break
                next_step_id = first_incomplete if first_incomplete else ""
                all_steps_completed = len(completed_steps) == len(step_ids)

                # 清除该步骤的重试计数
                step_retry_count.pop(current_step_id, None)

            else:
                # 未达到上限，增加重试计数
                step_retry_count[current_step_id] = current_retry_count + 1
                logger.info(
                    f"[ReplanNode] 步骤[{current_step_id}]需要重试（第{current_retry_count + 1}次）"
                )
        elif final_mode == "advance":
            # advance场景：清除已完成步骤的重试计数
            for completed_step_id in completed_steps:
                step_retry_count.pop(completed_step_id, None)
            logger.debug(f"[ReplanNode] 已清除已完成步骤的重试计数: {completed_steps}")

        updated_plan = plan.model_copy(
            update={
                "completedSteps": completed_steps,
                "nextStepId": next_step_id,
                "stepRetryCount": step_retry_count,
                "updatedAt": datetime.now(timezone.utc),
            }
        )

        # 构建进度日志信息（仅用于日志记录，不再伪造tool_call消息）
        progress_payload = {
            "type": "plan_progress_update",
            "planId": updated_plan.planId,
            "completedSteps": completed_steps,
            "nextStepId": next_step_id,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "progressMode": final_mode,
        }

        logger.info(
            f"[ReplanNode] 更新计划进度：完成{completed_steps}，下一步={next_step_id or '无'}，决策={final_mode}，"
            f"详情={json.dumps(progress_payload, ensure_ascii=False)}"
        )

        current_messages = list(state.get(StateFields.MESSAGES, []))
        if final_mode == "redo" and current_step_id:
            retry_count = step_retry_count.get(current_step_id, 0)
            logger.info(
                f"[ReplanNode] 步骤[{current_step_id}]需要重新执行（第{retry_count}次重试），仅记录日志不再注入SystemMessage"
            )

        # 检查是否所有步骤已完成
        if all_steps_completed and final_mode == "advance":
            # 所有步骤完成，跳转到reporter节点生成最终报告
            logger.info(
                "[ReplanNode] 所有计划步骤已完成，跳转到reporter节点生成最终报告"
            )

            return Command(
                goto="report_summary",
                update={
                    StateFields.PLAN: plan_state_to_dict(updated_plan),
                    StateFields.MESSAGES: current_messages,
                },
            )

        # 继续执行计划的下一步
        next_target = None
        if next_step_id:
            for step in plan.steps:
                if step.stepId == next_step_id:
                    next_target = step.handoffTarget
                    break
            if not next_target:
                raise ValueError(
                    f"计划步骤 {next_step_id} 缺少合法的 handoffTarget，无法派发下一团队。"
                )

        goto_value = END if not next_target else next_target

        return Command[str](
            # goto=goto_value,
            goto="plan_executor",
            update={
                **state,
                StateFields.PLAN: plan_state_to_dict(updated_plan),
                StateFields.MESSAGES: current_messages,
            },
        )

    return replan_node


def _format_past_steps_with_results(plan: PlanState) -> str:
    """格式化已完成步骤及其执行结果（简化版本）"""
    step_map = {s.stepId: s.goal for s in plan.steps}
    parts = []

    # 已完成步骤
    for step_id in plan.completedSteps:
        goal = step_map.get(step_id, "未知目标")
        result = plan.stepResults.get(step_id, "无")
        parts.append(f"[{step_id}] {goal}\n执行结果：{result}")

    # 当前步骤（如果有结果）
    if plan.nextStepId and plan.nextStepId not in plan.completedSteps:
        if plan.nextStepId in plan.stepResults:
            goal = step_map.get(plan.nextStepId, "未知目标")
            result = plan.stepResults[plan.nextStepId]
            parts.append(f"[{plan.nextStepId}] {goal}（当前步骤）\n执行结果：{result}")

    return "\n\n".join(parts) if parts else "无"


def _validate_completed(
    plan: PlanState, predicted: List[str]
) -> Tuple[List[str], bool]:
    """验证并规范化完成步骤列表（简化版本）

    Args:
        plan: 计划状态
        predicted: LLM预测的完成步骤列表

    Returns:
        (规范化列表, 是否有效) - 规范化列表按计划顺序排列，是否有效表示是否为有效前缀序列
    """
    plan_ids = [step.stepId for step in plan.steps]

    # 去重并保留顺序
    valid_steps = []
    for step_id in predicted:
        if step_id in plan_ids and step_id not in valid_steps:
            valid_steps.append(step_id)

    # 确保按计划顺序排列
    ordered = [sid for sid in plan_ids if sid in valid_steps]

    # 验证是否为有效前缀（连续序列）
    is_valid = ordered == plan_ids[: len(ordered)]

    return ordered, is_valid


__all__ = ["create_replan_node"]
