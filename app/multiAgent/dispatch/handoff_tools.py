"""
Handoff工具模块
"""

from typing import Annotated

from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langgraph.types import Command, Send

from app.multiAgent.common.uni_state import UniState

from app.utils.logger import tool_logger as logger


def create_handoff_tool(*, agent_name: str, description: str | None = None):
    """创建handoff工具，用于将任务转移到指定的Agent
    
    Args:
        agent_name: 目标Agent名称
        description: 工具描述，如果为None则使用默认描述
        
    Returns:
        handoff_tool: 配置好的handoff工具
    """
    name = f"transfer_to_{agent_name}"
    description = description or f"将任务分配给{agent_name}进行处理"
    
    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[UniState, InjectedState],
        # tool_call_id: Annotated[str, InjectedToolCallId],
        task_description: Annotated[
            str,
            "结合上下文详细描述下一个Agent专家团队的工作内容，要综合考虑用户提问及当前的规划内容生成此内容",
        ],
    ) -> Command:
        # tool_message = ToolMessage(
        #     content=f"任务已成功转移到 {agent_name}",
        #     name=name,
        #     tool_call_id=tool_call_id,
        # )
        task_description_message = {"role": "user", "content": task_description}
        logger.info(
            f"handoff_tool: task_description_message: {task_description_message}"
        )
        agent_input = {**state, "messages": [task_description_message]}
        logger.info(
            f"handoff_tool: 将任务分配给{agent_name}进行处理，agent_input: {agent_input}"
        )
        return Command(
            goto=Send(agent_name, agent_input),
        )

    return handoff_tool


# 团队级别的 handoff 工具（具有子图的复杂 Agent）
transfer_to_enterprise_profile_team = create_handoff_tool(
    agent_name="enterprise_profile_team",
    description="""将任务分配给企业画像团队。
前置条件：必须输入客户名称或者社会统一信息代码。如果不满足则不允许转移。
功能：负责对目标企业进行全方位的数字刻画。
整合企业基础信息、股权结构、高管背景、财务状况和信用评级，聚焦企业身份识别、行业归属、绿色属性判定、股权与控制权分析，可联动政策库确认绿色属性的政策依据。
构建动态、立体的客户视图，从海量企业中筛选出高潜力、高匹配度的目标客户，并对其进行精准分层（如按规模分为1000万以下、1000-3000万、3000万以上），为后续所有营销动作提供决策依据。
核心能力：整合企业征信、财务、供应链等信息，生成包含企业规模、行业类型、经营状况、风险等级等关键特征的360度客户画像，并进行客户分层。""",
)

transfer_to_blue_green_access_team = create_handoff_tool(
    agent_name="blue_green_access_team",
    description="""将任务分配给蓝绿项目准入评估团队。
前置条件：用户输入必须明确企业名称或者项目准入的意图，否则不允许转移。
功能：以'政策标准+风险校验'为双核心，判定企业/项目是否符合蓝绿色贷款准入。
深度内化《某某银行蓝色金融产业认定标准》及各版本《绿色产业指导目录》，将企业的所属行业、贷款投向与政策标准进行比对，给出明确的'准入/不准入'判断，并解读政策背后的含义，如识别符合'碳减排支持工具'的项目。
结合企业征信agent的'环境评价信息'，排查近3年重大环保违规（单次处罚超50万元触发否决），实行'一票否决'机制。
核心能力：调用行业分析Agent、企业征信agent和政策库Agent，对照蓝绿色金融产业认定标准，判断目标企业或项目是否符合准入条件，排查近3年重大环保违规信息，并说明判断依据。""",
)

transfer_to_blue_green_product_team = create_handoff_tool(
    agent_name="blue_green_product_team",
    description="""将任务分配给蓝绿产品推荐团队。
功能：内嵌全行所有蓝绿产品的详情、金融产品准入条件和优惠利率。
基于客户画像的分层结果和产品准入判断，从产品库中筛选出最匹配的产品，并结合政策库信息，组织综合融资方案。
按'企业规模+业务场景+政策优惠'三维度匹配产品，实现'精准推荐+成本测算'。
针对不同规模企业提供差异化方案：
- 1000万元以下小微企业：匹配山东省版碳减排政策工具（补贴后资金成本2.35%）
- 3000万元以上大项目：推荐央行碳减排支持工具（60%本金成本1.5%，加权平均利率2.44%）
- 海上风电/海洋养殖项目：优先匹配'青出于蓝'海洋金融特色产品（渔船贷、海殖宝）
核心能力：基于客户画像和准入结果，调用产品库Agent和政策库Agent，匹配并推荐最合适的金融产品，说明产品优势和优惠政策。""",
)

transfer_to_blue_green_solution_team = create_handoff_tool(
    agent_name="blue_green_solution_team",
    description="""将任务分配给蓝绿解决方案团队。
功能：整合前面所有Agent的分析结果，为客户量身定制一份逻辑严密、亮点突出的综合金融服务方案。
将金融产品包装成解决客户痛点的'一揽子解决方案'，并从案例库中调取成功案例作为佐证，提供业务拓展技巧。
核心能力：整合客户画像、蓝绿色项目准入判断和产品推荐、产品准入结果，调用案例库Agent，生成一份包含融资结构、还款安排、风险提示和成功案例参考的个性化金融服务方案。
前置条件：需要完整的客户画像、准入判断和产品推荐作为依据。""",
)

def get_all_handoff_tools() -> list:
    """
    获取所有团队级别的 handoff 工具（具有子图的复杂 Agent）

    专业分析工具现在是直接调用，不再使用 handoff 机制
    """
    return [
        transfer_to_enterprise_profile_team,
        transfer_to_blue_green_access_team,
        transfer_to_blue_green_product_team,
        transfer_to_blue_green_solution_team,
    ]
