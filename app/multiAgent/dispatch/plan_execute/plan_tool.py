"""
计划工具实现 - 极简计划结构

核心设计原则：
1. 计划只列出每一步的目标与建议交接对象，不预先推断执行参数
2. 工具保持职责单一：校验基础格式，生成 plan_created_notice 消息
3. 所有执行细节依赖消息上下文，由后续团队或工具在调用时补全
"""

from typing import Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from datetime import datetime
import json
import uuid

from app.multiAgent.common.uni_state import UniState, StateFields
from app.multiAgent.dispatch.plan_execute.plan_model import (
    PlanStep,
    build_plan_state,
    plan_state_to_dict,
)
from app.utils.logger import logger

ALLOWED_HANDOFF_TARGETS = {
    "enterprise_profile_team",
    "blue_green_access_team",
    "blue_green_product_team",
    "blue_green_solution_team",
}


class PlanToolInput(BaseModel):
    """
    计划工具的输入模型

    核心要求：
    1. LLM必须直接生成结构化的steps数组，而非自然语言描述
    2. 每个步骤仅包含步骤目标与建议交接对象
    """

    plan_summary: str = Field(
        ...,
        description="计划的整体摘要，一句话描述要完成什么（展示给用户）"
    )

    steps: list[PlanStep] = Field(
        ...,
        description=(
            "执行步骤列表，必须提供结构化数组。\n"
            "每个步骤必须包含：\n"
            "- stepId: 按顺序编号（step-001, step-002, ...）\n"
            "- goal: 该步骤要完成的目标\n"
            "- handoffTarget: 建议交接的团队或工具标识"
        ),
        min_items=1
    )

    state: Annotated[UniState | None, InjectedState] = Field(
        default=None,
        description="LangGraph运行时自动注入的对话状态，LLM无需填写"
    )
    tool_call_id: Annotated[str | None, InjectedToolCallId] = Field(
        default=None,
        description="LangGraph运行时自动注入的tool_call_id，LLM无需填写"
    )

    thinking: str | None = Field(
        default=None,
        description="制定plan计划的思考过程记录，便于调试和分析",
    )


class PlanTool:
    """
    计划工具的核心实现

    职责：
    1. 验证步骤的基本有效性（stepId连续、目标与交接对象存在）
    2. 构造结构化PlanState并写入状态
    3. 生成轻量通知消息，提示Supervisor计划已生成

    设计约束：
    - 不推断团队或参数：LLM直接给出交接对象，执行阶段再补充细节
    - 不解析自然语言：LLM直接生成结构化的PlanStep对象
    - 只做最小校验：确保步骤顺序正确、目标明确
    """

    def __init__(self):
        self.tool_name = "plan"

    def _validate_steps(self, steps: list[PlanStep]) -> tuple[bool, str]:
        """
        验证步骤的基本有效性

        Args:
            steps: 步骤列表

        Returns:
            (is_valid, error_message) 元组
        """
        if not steps:
            return False, "步骤列表不能为空"

        # 验证stepId格式和顺序
        for i, step in enumerate(steps, 1):
            expected_id = f"step-{i:03d}"
            if step.stepId != expected_id:
                return False, f"步骤ID错误：期望{expected_id}，实际{step.stepId}"

            if not step.goal.strip():
                return False, f"步骤{step.stepId}的goal不能为空"

            if not step.handoffTarget.strip():
                return False, f"步骤{step.stepId}的handoffTarget不能为空"
            if step.handoffTarget not in ALLOWED_HANDOFF_TARGETS:
                allowed = ", ".join(sorted(ALLOWED_HANDOFF_TARGETS))
                return (
                    False,
                    f"步骤{step.stepId}的handoffTarget必须是团队节点之一: {allowed}",
                )

        return True, ""

    def _compress_adjacent_teams(self, steps: list[PlanStep]) -> tuple[list[PlanStep], bool]:
        """
        压缩相邻相同 team 的步骤

        Args:
            steps: 原始步骤列表

        Returns:
            (compressed_steps, was_compressed) 元组
            - compressed_steps: 压缩后的步骤列表（重新编号）
            - was_compressed: 是否发生了压缩
        """
        if not steps:
            return steps, False

        compressed = []
        was_compressed = False

        i = 0
        while i < len(steps):
            current_step = steps[i]
            current_target = current_step.handoffTarget

            # 收集相同 handoffTarget 的连续步骤
            same_target_steps = [current_step]
            j = i + 1
            while j < len(steps) and steps[j].handoffTarget == current_target:
                same_target_steps.append(steps[j])
                j += 1

            # 如果有多个相邻相同 team，合并它们
            if len(same_target_steps) > 1:
                was_compressed = True
                # 合并 goal：使用分号分隔，保持原有目标的完整性
                merged_goal = "; ".join(step.goal for step in same_target_steps)

                # 创建合并后的步骤（保留第一个步骤的 stepId，稍后重新编号）
                merged_step = PlanStep(
                    stepId=current_step.stepId,  # 临时保留，稍后重新编号
                    goal=merged_goal,
                    handoffTarget=current_target
                )
                compressed.append(merged_step)

                logger.info(
                    f"[PlanTool] 压缩相邻步骤：{[s.stepId for s in same_target_steps]} "
                    f"→ 合并为单个步骤（team={current_target}）"
                )
            else:
                # 单个步骤，直接添加
                compressed.append(current_step)

            i = j  # 跳到下一组

        # 重新编号 stepId
        renumbered = []
        for idx, step in enumerate(compressed, start=1):
            new_step = PlanStep(
                stepId=f"step-{idx:03d}",
                goal=step.goal,
                handoffTarget=step.handoffTarget
            )
            renumbered.append(new_step)

        return renumbered, was_compressed

    def create_plan_tool(self):
        """创建plan工具实例"""

        description = """
计划工具
- 生成结构化计划（summary + steps: stepId/goal/handoffTarget）
- 自动压缩相邻相同 team 的步骤（LLM 无需手动优化）
- 将计划写入 state.plan，并广播 plan_created_notice 提示后续人工审批

必填参数：
- plan_summary: 计划概要
- steps: 结构化步骤数组（允许1个或多个步骤，相邻相同team会自动合并）

示例1（自动压缩）：
输入：
{
  "plan_summary": "评估并推荐对公金融方案",
  "steps": [
    {"stepId": "step-001", "goal": "企业基本信息调研", "handoffTarget": "enterprise_profile_team"},
    {"stepId": "step-002", "goal": "企业风险评估", "handoffTarget": "enterprise_profile_team"},
    {"stepId": "step-003", "goal": "蓝绿准入评估", "handoffTarget": "blue_green_access_team"}
  ]
}

压缩后实际执行：
{
  "steps": [
    {"stepId": "step-001", "goal": "企业基本信息调研; 企业风险评估", "handoffTarget": "enterprise_profile_team"},
    {"stepId": "step-002", "goal": "蓝绿准入评估", "handoffTarget": "blue_green_access_team"}
  ]
}

示例2（单步骤计划）：
{
  "plan_summary": "查询企业画像",
  "steps": [
    {"stepId": "step-001", "goal": "调研企业基本信息和风险状况", "handoffTarget": "enterprise_profile_team"}
  ]
}
"""

        def plan_tool_impl(
            plan_summary: Annotated[str, "计划摘要"],
            steps: Annotated[list[PlanStep], "执行步骤列表"],
            thinking: Annotated[str | None, "LLM思考过程"] | None = None,
            state: Annotated[UniState, InjectedState] | None = None,
            tool_call_id: Annotated[str, InjectedToolCallId] | None = None,
            config: Annotated[RunnableConfig | None, "LangGraph运行时配置"] | None = None,
        ) -> Command:
            """
            计划工具的实现函数

            执行流程：
            1. 验证步骤（stepId连续性、目标与交接对象不为空）
            2. 转换为字典（Pydantic模型 → dict）
            3. 构建plan_created_notice消息
            4. 序列化并创建ToolMessage
            5. 写入状态并返回Command

            注意：本函数不做任何业务推断或自然语言解析
            """
            if state is None or tool_call_id is None:
                raise ValueError("plan工具需在LangGraph上下文中使用，缺少state或tool_call_id注入")

            try:
                logger.info(f"Plan tool called with {len(steps)} steps")

                # 1. 验证步骤
                is_valid, error_msg = self._validate_steps(steps)
                if not is_valid:
                    raise ValueError(f"步骤验证失败: {error_msg}")

                # 2. 压缩相邻相同 team 的步骤
                compressed_steps, was_compressed = self._compress_adjacent_teams(steps)

                if was_compressed:
                    logger.info(
                        f"[PlanTool] 计划已压缩：{len(steps)} 步 → {len(compressed_steps)} 步"
                    )
                    # 更新 plan_summary 以反映压缩
                    if plan_summary:
                        plan_summary = f"{plan_summary}（已优化合并相邻步骤）"

                # 使用压缩后的步骤继续
                final_steps = compressed_steps

                # 3. 生成计划ID并构造PlanState
                plan_id = f"plan-{uuid.uuid4().hex[:8]}"
                plan_state = build_plan_state(plan_id, plan_summary, final_steps, thinking)
                plan_dict = plan_state_to_dict(plan_state)

                logger.info(
                    f"Plan created: plan_id={plan_id}, steps={len(plan_state.steps)}, "
                    f"next_step={plan_state.nextStepId}"
                )

                # 4. 创建轻量通知消息，提示计划已生成
                notice_payload = {
                    "type": "plan_created_notice",
                    "planId": plan_id,
                    "summary": plan_summary,
                    "stepCount": len(plan_state.steps),
                    "originalStepCount": len(steps),  # 新增：原始步骤数
                    "wasCompressed": was_compressed,   # 新增：是否压缩
                    "generatedAt": datetime.now().isoformat(),
                }
                json_content = json.dumps(notice_payload, ensure_ascii=False, indent=2)
                tool_message = ToolMessage(
                    content=json_content,
                    name=self.tool_name,
                    tool_call_id=tool_call_id,
                )

                current_messages = list(state.get(StateFields.MESSAGES, []))

                # 5. 将thinking信息通过custom_stream_data格式输出到前端
                thinking = f"让我理解您的意图，{thinking}"
                if thinking:
                    logger.info(f"将thinking信息通过custom_stream_data格式输出: {thinking[:100]}...")
                    try:
                        # 导入langgraph.config用于流式写入
                        from langgraph.config import get_stream_writer
                        
                        # 通过custom流模式输出thinking信息，采用与知识库溯源信息相同的格式
                        stream_writer = get_stream_writer()
                        if stream_writer:
                            custom_stream_data = {
                                "type": "thinking",
                                "status": "success",
                                "data": thinking
                            }
                            stream_writer(custom_stream_data)
                            logger.info("已通过custom流模式输出thinking信息")
                    except Exception as e:
                        logger.warning(f"thinking信息流式输出失败，但不影响主流程: {e}")

                # 正常返回Command
                return Command(
                    update={
                        StateFields.MESSAGES: current_messages + [tool_message],
                        StateFields.PLAN: plan_dict,
                    }
                )

            except Exception as e:
                logger.error(f"Plan tool execution failed: {str(e)}", exc_info=True)

                # 错误处理：生成plan_generation_error JSON
                error_json = {
                    "type": "plan_generation_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

                json_content = json.dumps(error_json, ensure_ascii=False, indent=2)
                error_message = ToolMessage(
                    content=json_content,
                    name=self.tool_name,
                    tool_call_id=tool_call_id
                )

                current_messages = list(state.get(StateFields.MESSAGES, []))
                return Command(
                    update={StateFields.MESSAGES: current_messages + [error_message]}
                )

        # 使用Pydantic的args_schema绑定
        structured_tool = tool(
            self.tool_name,
            args_schema=PlanToolInput,
            description=description
        )(plan_tool_impl)

        return structured_tool


def create_plan_tool():
    """
    工厂函数：创建plan工具实例

    Returns:
        配置好的plan工具函数
    """
    plan_tool_instance = PlanTool()
    return plan_tool_instance.create_plan_tool()
