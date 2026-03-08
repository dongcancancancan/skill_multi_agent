"""
结构化报告模板（硬编码，避免 AI 自由发挥）
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Sequence

from pydantic import BaseModel, Field


class ExecutionStepResult(BaseModel):
    """执行步骤结果"""

    step_index: int = Field(description="步骤序号（1, 2, 3...）")
    step_instruction: str = Field(description="任务描述（来自 plan）")
    team_name: str = Field(description="执行团队名称")
    full_result: str = Field(description="完整执行结果")


class StructuredReport:
    """结构化报告生成器（硬编码模板）"""

    _TEAM_DISPLAY_NAME_MAP = {
        "enterprise_profile_team": "企业画像分析团队",
        "blue_green_access_team": "蓝绿准入评估团队",
        "blue_green_product_team": "蓝绿产品推荐团队",
        "blue_green_solution_team": "蓝绿解决方案生成团队",
    }

    _MIN_STEP_HEADING_LEVEL = 4  # 将步骤内标题最低提升至 H4，避免与主报告冲突

    _HEADING_PATTERN = re.compile(r"(?m)^(?P<indent>\s{0,3})(?P<hashes>#{1,6})(?P<space>\s+)")

    @staticmethod
    def generate_markdown_report(
        user_question: str,
        execution_summary: str,
        execution_steps: Sequence[ExecutionStepResult],
    ) -> str:
        """生成结构化 Markdown 报告

        结合 LLM 生成的执行摘要和完整的步骤结果。

        Args:
            user_question: 用户原始问题
            execution_summary: LLM 生成的执行摘要
            execution_steps: 执行步骤结果列表（完整内容）

        Returns:
            格式化的 Markdown 报告
        """
        # 报告头部
        report_lines = [
            "# 对公金融分析报告",
            "",
            "---",
            "",
        ]

        # 一、用户需求部分
        report_lines.extend(
            [
                "## 一、用户需求",
                "",
                user_question,
                "",
                "---",
                "",
            ]
        )

        # 二、执行摘要部分（LLM 生成）
        report_lines.extend(
            [
                "## 二、执行摘要",
                "",
                execution_summary,
                "",
                "---",
                "",
            ]
        )

        # 三、详细分析过程部分（完整 stepResults）
        report_lines.extend(
            [
                "## 三、详细分析过程",
                "",
            ]
        )

        # 遍历每个执行步骤
        for step in execution_steps:
            localized_team_name = StructuredReport._get_team_display_name(step.team_name)
            normalized_result = StructuredReport._normalize_step_result(step.full_result)

            # 步骤标题
            report_lines.extend(
                [
                    f"### {step.step_index}. {step.step_instruction}",
                    "",
                    f"**执行团队**：{localized_team_name}",
                    "",
                    f"**分析结果**：",
                    "",
                    normalized_result,
                    "",
                    "---",
                    "",
                ]
            )

        # 报告尾部
        report_lines.extend(
            [
                f"**报告生成时间**：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}",
                "",
                "---",
                "",
                "*本报告由某某银行对公金融多智能体系统自动生成*",
            ]
        )

        return "\n".join(report_lines)

    @staticmethod
    def _get_team_display_name(team_name: str | None) -> str:
        """将内部英文团队标识映射为对用户友好的中文名称"""
        if not team_name:
            return "未标记团队"
        return StructuredReport._TEAM_DISPLAY_NAME_MAP.get(team_name, team_name)

    @staticmethod
    def _normalize_step_result(content: str | None) -> str:
        """规范步骤结果中的 Markdown 标题层级，避免与主报告冲突"""
        if not content:
            return "（暂无执行结果）"

        text = content if isinstance(content, str) else str(content)

        def _replace(match: re.Match[str]) -> str:
            indent = match.group("indent")
            hashes = match.group("hashes")
            space = match.group("space")
            level = len(hashes)

            if level >= StructuredReport._MIN_STEP_HEADING_LEVEL:
                return match.group(0)

            offset = StructuredReport._MIN_STEP_HEADING_LEVEL - 1
            new_level = min(6, level + offset)
            return f"{indent}{'#' * new_level}{space}"

        return StructuredReport._HEADING_PATTERN.sub(_replace, text)


__all__ = [
    "ExecutionStepResult",
    "StructuredReport",
]
