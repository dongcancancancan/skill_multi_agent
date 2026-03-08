"""
Reporter流程拆分：Summary节点负责生成执行摘要，Reporter节点负责渲染最终报告。

Summary节点：
1. 提取用户原始问题
2. 从 plan_state.stepResults 获取执行结果
3. 调用 LLM 生成执行摘要，并写入 state.report_summary

Reporter节点：
1. 读取 summary 节点产出的执行摘要
2. 使用硬编码 Markdown 模板生成结构化报告
3. 清空计划状态并结束流程，仅输出最终报告
"""

from __future__ import annotations

from typing import Any, Sequence

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.types import Command
from pydantic import ValidationError

from app.multiAgent.common.uni_state import StateFields, UniState
from app.multiAgent.dispatch.plan_execute.plan_model import PlanState
from app.multiAgent.dispatch.plan_execute.report_template import (
    ExecutionStepResult,
    StructuredReport,
)
from app.utils.llm import get_llm
from app.utils.logger import logger


def create_report_summary_node():
    """创建Summary节点：负责生成执行摘要并写入state.report_summary"""

    llm = get_llm(temperature=0)

    def summary_node(state: UniState, config: RunnableConfig) -> Command:
        messages = list(state.get(StateFields.MESSAGES, []))
        plan_data = state.get(StateFields.PLAN)

        user_question = _extract_user_question(messages)
        execution_summary = "（无可用执行摘要）"

        try:
            plan_state = PlanState.model_validate(plan_data)
            execution_steps = _extract_steps_from_plan_state(plan_state)
        except ValidationError as exc:
            logger.warning(f"[Reporter-Summary] 计划数据解析失败：{exc}")
            return {
                StateFields.REPORT_SUMMARY: execution_summary,
            }

        if not execution_steps:
            logger.warning("[Reporter-Summary] 无可用执行步骤，跳过摘要生成")
            return {
                StateFields.REPORT_SUMMARY: execution_summary,
            }

        step_results_text = _format_step_results_for_llm(execution_steps)
        summary_messages = [
            {
                "role": "system",
                "content": (
                    "你是某某银行对公金融分析系统的报告总结专家。"
                    "你的任务是根据各团队的执行结果，生成一段简明专业的执行摘要。\n\n"
                    "要求：\n"
                    "1. 语气专业、严谨，符合金融行业规范\n"
                    "2. 突出关键发现和核心结论\n"
                    "3. 字数控制在 200-400 字\n"
                    "4. 不要使用表情符号\n"
                    "5. 使用清晰的段落结构"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"用户问题：{user_question}\n\n"
                    f"各团队执行结果：\n{step_results_text}\n\n"
                    f"请生成执行摘要："
                ),
            },
        ]

        try:
            summary_response = llm.invoke(summary_messages, config)
            execution_summary = summary_response.content.strip()
            logger.info("[Reporter-Summary] 执行摘要生成完成")
        except Exception as exc:
            logger.error(
                f"[Reporter-Summary] 执行摘要生成失败：{exc}",
                exc_info=True,
            )

        return {
            StateFields.REPORT_SUMMARY: execution_summary,
        }

    return summary_node


def create_reporter_node():
    """创建Reporter节点：根据执行摘要生成最终报告"""

    def reporter_node(state: UniState, config: RunnableConfig) -> Command:
        messages = list(state.get(StateFields.MESSAGES, []))
        plan_data = state.get(StateFields.PLAN)

        user_question = _extract_user_question(messages)
        execution_steps: list[ExecutionStepResult] = []

        try:
            plan_state = PlanState.model_validate(plan_data)
            execution_steps = _extract_steps_from_plan_state(plan_state)
            logger.info(f"[Reporter] 提取到 {len(execution_steps)} 个执行步骤结果")
        except ValidationError as exc:
            logger.warning(f"[Reporter] 计划数据解析失败：{exc}")

        if not execution_steps:
            logger.warning("[Reporter] 无可用的执行步骤结果")
            markdown_report = _generate_empty_report(user_question)
        else:
            execution_summary = state.get(StateFields.REPORT_SUMMARY) or "（无可用执行摘要）"
            try:
                markdown_report = StructuredReport.generate_markdown_report(
                    user_question=user_question,
                    execution_summary=execution_summary,
                    execution_steps=execution_steps,
                )
                logger.info("[Reporter] 结构化报告生成完成")
                logger.info(f"[Reporter] 生成的报告内容：\n{markdown_report}")
            except Exception as exc:
                logger.error(f"[Reporter] 报告生成失败: {exc}", exc_info=True)
                markdown_report = _generate_error_report(user_question, str(exc))

        # 发送完整 RAG 溯源信息到前端
        try:
            from langgraph.config import get_stream_writer
            from app.multiAgent.tools.rag_history_formatter import (
                format_rag_history_to_knowledge_base,
            )

            rag_history = state.get(StateFields.RAG_HISTORY)
            if rag_history:
                knowledge_base_data = format_rag_history_to_knowledge_base(rag_history)
                if knowledge_base_data:
                    stream_writer = get_stream_writer()
                    if stream_writer:
                        # 直接发送转换后的数据（已包含完整的嵌套结构）
                        stream_writer(knowledge_base_data)
                        logger.info("[Reporter] 已发送完整 RAG 溯源信息到前端")
        except Exception as e:
            logger.warning(f"[Reporter] RAG 溯源发送失败，但不影响主流程: {e}")

        response = AIMessage(content=markdown_report)
        return Command(
            goto=END,
            update={
                StateFields.MESSAGES: messages + [response],
                StateFields.PLAN: None,
                StateFields.REPORT_SUMMARY: None,
            },
        )

    return reporter_node


def _extract_user_question(messages: Sequence[Any]) -> str:
    """提取用户原始问题"""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            content = msg.content
            if isinstance(content, str):
                return content.strip()
    return "（未找到用户问题）"


def _extract_steps_from_plan_state(plan_state: PlanState) -> list[ExecutionStepResult]:
    """从 PlanState 提取执行步骤结果"""
    execution_steps = []

    for idx, step in enumerate(plan_state.steps, 1):
        # 从 stepResults 获取完整结果
        full_result = plan_state.stepResults.get(
            step.stepId, "（未获得该步骤的执行结果）"
        )

        # 使用 handoffTarget 作为团队名称
        team_name = step.handoffTarget if step.handoffTarget else "unknown_team"

        execution_steps.append(
            ExecutionStepResult(
                step_index=idx,
                step_instruction=step.goal,  # 用 step.goal 作为步骤标题
                team_name=team_name,
                full_result=full_result,
            )
        )

    return execution_steps


def _format_step_results_for_llm(execution_steps: list[ExecutionStepResult]) -> str:
    """将执行步骤结果格式化为文本，供 LLM 生成摘要"""
    lines = []
    for step in execution_steps:
        lines.append(f"步骤 {step.step_index}：{step.step_instruction}")
        lines.append(f"执行团队：{step.team_name}")
        lines.append(f"执行结果：{step.full_result}")
        lines.append("")
    return "\n".join(lines)


def _generate_empty_report(user_question: str) -> str:
    """生成空报告（当没有执行结果时）"""
    return f"""# 对公金融分析报告

---

## 一、用户需求

**原始需求**：{user_question}

---

## 二、执行状态

无可用的团队执行结果。

---

*本报告由某某银行对公金融多智能体系统自动生成*
"""


def _generate_error_report(user_question: str, error_message: str) -> str:
    """生成错误报告（当报告生成失败时）"""
    return f"""# 对公金融分析报告

---

## 一、用户需求

**原始需求**：{user_question}

---

## 二、报告生成状态

报告生成失败。错误信息：{error_message}

请稍后重试或联系技术支持。

---

*本报告由某某银行对公金融多智能体系统自动生成*
"""


__all__ = ["create_report_summary_node", "create_reporter_node"]
