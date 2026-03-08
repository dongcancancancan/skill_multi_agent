"""
Agent 名称映射工具

将内部英文 agent/team 标识映射为对用户友好的中文名称
"""

from typing import Dict

# Agent/Team 名称映射表（英文标识 -> 中文名称）
AGENT_DISPLAY_NAME_MAP: Dict[str, str] = {
    # Team nodes（节点名称，用于图构建）
    "enterprise_profile_team": "企业画像分析团队",
    "blue_green_access_team": "蓝绿准入评估团队",
    "blue_green_product_team": "蓝绿产品推荐团队",
    "blue_green_solution_team": "蓝绿解决方案生成团队",
    # Agent instances（实例名称，LLM 调用工具时传递的值）
    "enterprise_profile_agent": "企业画像分析团队",
    "blue_green_access_agent": "蓝绿准入评估团队",
    "blue_green_product_agent": "蓝绿产品推荐团队",
    "blue_green_solution_agent": "蓝绿解决方案生成团队",
    # Toolbox agent
    "toolbox_agent": "工具箱助手",
    # Overall（用于没有具体 agent 时）
    "overall": "总体分析",
}


def get_agent_display_name(agent_name: str | None) -> str:
    if not agent_name:
        return "未标记团队"
    return AGENT_DISPLAY_NAME_MAP.get(agent_name, agent_name)


__all__ = ["AGENT_DISPLAY_NAME_MAP", "get_agent_display_name"]
