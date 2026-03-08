"""
统一Supervisor架构
"""

from typing import Dict, Any, Annotated
import uuid
from collections.abc import AsyncIterator
import json

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, Interrupt
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.base import BaseCheckpointSaver

# 使用 TYPE_CHECKING 避免运行时循环导入
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.api.models import MainGraphRequest, GraphStreamResult

from app.utils.logger import logger
from app.utils.llm import get_llm

from app.multiAgent.dispatch.plan_execute.plan_tool import create_plan_tool
from app.multiAgent.dispatch.plan_execute.plan_model import PlanState
from app.multiAgent.dispatch.plan_execute.replan_node import create_replan_node
from app.multiAgent.dispatch.plan_execute.reporter_node import (
    create_report_summary_node,
    create_reporter_node,
)
from app.multiAgent.common.error_categories import ToolSystemError, ToolUserError

from app.multiAgent.common.uni_state import (
    UniState,
    StateFields,
    create_initial_state,
)

from app.multiAgent.dispatch.plan_execute.plan_executor import plan_executor

# ==================== 工具定义 ====================


@tool
def handoff_to_plan(
    task_description: Annotated[str, "复杂任务的描述，说明为什么需要制定计划"],
):
    """移交给计划执行流程处理复杂任务

    当遇到以下情况时调用此工具：
    - 判断类问题（如"是否符合准入标准"）
    - 推荐决策类（如"推荐什么产品"）
    - 多维度查询（需要多个团队协作）
    - 需要深度分析的任务
    """
    # 这个工具不返回任何内容，仅用于让 LLM 表达需要移交给复杂任务处理
    return


@tool
def handoff_to_toolbox(
    task_description: Annotated[
        str, "需要 ToolBox 处理的任务描述，说明需要查询什么数据"
    ],
    thinking: Annotated[str | None, "LLM思考过程"] | None = None,
    config: Annotated[RunnableConfig | None, "LangGraph运行时配置"] | None = None,
):
    """将任务移交给 ToolBox Agent 处理

    适用场景：
    - 需要查询企业信息、政策、产品、征信等数据
    - 可能需要多次工具调用以获取完整信息
    - 需要对比、综合分析多个数据源
    - 不涉及跨团队协作的简单到中等复杂度查询任务

    示例：
    - "查询XX公司的基本信息和信用评级"
    - "对比A公司和B公司的财务状况"
    - "查找绿色金融相关政策和产品"
    - "分析某个行业的准入条件"
    """
    # 将thinking信息通过custom_stream_data格式输出到前端
    thinking = f"让我理解您的意图，{thinking}"
    if thinking:
        logger.info(
            f"handoff_to_toolbox: 将thinking信息通过custom_stream_data格式输出: {thinking[:100]}..."
        )
        try:
            # 导入langgraph.config用于流式写入
            from langgraph.config import get_stream_writer

            # 通过custom流模式输出thinking信息，采用与知识库溯源信息相同的格式
            stream_writer = get_stream_writer()

            if stream_writer:
                custom_stream_data = {
                    "type": "thinking",
                    "status": "success",
                    "data": thinking,
                }
                stream_writer(custom_stream_data)
                logger.info("handoff_to_toolbox: 已通过custom流模式输出thinking信息")
        except Exception as e:
            logger.warning(
                f"handoff_to_toolbox: thinking信息流式输出失败，但不影响主流程: {e}"
            )

    # 不执行任何逻辑，仅用于触发路由，检测到此工具调用并路由到 toolbox_agent 节点
    return


# ==================== 辅助函数 ====================


def _check_session_lock(state: UniState) -> tuple[bool, AIMessage | None]:
    """检查会话是否被锁定

    Args:
        state: 统一状态对象

    Returns:
        (is_locked, lock_message):
            - 如果被锁定返回 (True, 锁定消息)，plan_rejected场景返回 (True, None)
            - 如果未锁定返回 (False, None)
    """
    session_status = state.get(StateFields.SESSION_STATUS)

    if not session_status or session_status.get("status") != "locked":
        return False, None

    # plan_rejected场景：human_approval已添加拒绝消息，无需重复
    if session_status.get("source") == "plan_rejected":
        return True, None

    # 其他锁定场景：构造提示消息
    lock_hint = session_status.get("message") or "当前会话已被终止，请新开会话后重试。"
    return True, AIMessage(content=f"{lock_hint}\n如需继续处理，请开启新的会话。")


def _output_thinking_info(thinking_content: str, config: RunnableConfig | None = None):
    """输出thinking信息到前端的辅助函数

    Args:
        thinking_content: 思考内容
        config: LangGraph运行时配置
    """
    if thinking_content:
        logger.info(f"输出thinking信息到前端: {thinking_content[:100]}...")
        try:
            # 导入langgraph.config用于流式写入
            from langgraph.config import get_stream_writer

            # 通过custom流模式输出thinking信息，采用与知识库溯源信息相同的格式
            stream_writer = get_stream_writer()

            if stream_writer:
                custom_stream_data = {
                    "type": "thinking",
                    "status": "success",
                    "data": thinking_content,
                }
                stream_writer(custom_stream_data)
                logger.info("已通过custom流模式输出thinking信息")
        except Exception as e:
            logger.warning(f"thinking信息流式输出失败，但不影响主流程: {e}")


# ==================== 提示词定义 ====================

# 简单任务路由提示词 - 负责快速识别并处理无需计划的任务
simple_router_prompt = SystemMessage(
    content="""你是某某银行对公金融助手的任务分流协调员，负责快速判断用户需求并采取正确的处理方式。

## 核心职责

你需要快速判断用户需求并选择以下三种处理方式之一：

### 1. 直接回复（无需工具）

**适用场景**：

- **熔断场景**（检测到以下关键词立即中断）：
  - **非相关业务**：天气、股价、汇率、新闻、体育、翻译、写诗、讲笑话、历史事件、科学常识、菜谱、旅游攻略
    - 示例："今天北京天气怎么样？"、"最近有什么体育新闻？"、"帮我把这段英文合同翻译一下"
    - **回复**："您的问题可能超出了业务范围，请围绕蓝绿色金融业务进行提问哦"

  - **越权数据查询**：交易明细、原始数据、具体金额、逐笔、非我行客户、他行客户
    - 示例："把'XX公司'和'YY公司'的所有交易明细导出来"
    - **回复**："出于数据安全和隐私保护，我无法提供具体的交易明细，只能提供汇总信息。"

  - **个人隐私查询**：个人征信、个人资产、电话、住址、身份证号、法人/实控人/股东个人情况
    - 示例："查一下法人'张三'的个人征信"、"查一下'XX公司'法人的联系电话和家庭住址"
    - **回复**："无法处理个人隐私信息，您的问题可能超出了业务范围，请围绕蓝绿色金融业务进行提问哦"

  - **竞品分析**：其他银行（非我行）、和XX银行比、其他银行怎么样
    - 示例："建行的绿色贷款利率是多少？"、"和工行比，我们的绿色贷款审批速度有优势吗？"
    - **回复**："当前仅提供本行的产品信息，无法进行跨行产品比较"

  - **系统级操作**：筛选一批客户、修改信息、录入系统、联系客户
    - 示例："帮我修改'XX公司'的客户风险评级"
    - **回复**："您的问题可能超出了业务范围，请围绕蓝绿色金融业务进行提问哦"

- **问候闲聊**：
  - 示例："你好"、"谢谢"、"再见"
  - **回复**：自然语言回复，如"您好！很高兴为您服务"、"不客气！还有其他问题吗？"

- **系统能力介绍**：
  - 示例："你能做什么？"、"你的核心能力模块有哪些？"
  - **回复**：直接回复预设的功能介绍和导航菜单

**处理方式**：直接用自然语言回复，无需调用任何工具

### 2. 简单事实查询 - 调用 handoff_to_toolbox

**适用前提**：用户需求未触发任何复杂任务判定条件（见下一节），特别是未出现“蓝色金融”“绿色金融”“蓝绿色金融”及其同义词或英文表述。

**适用场景**（标准化的、以资料检索为主、无需跨团队协作的、蓝绿属性不强的查询任务）：

- **政策 / 产品 / 流程 / 基础概念资料**：查询政策原文、产品要点、办理流程、材料清单、模板、案例、名词定义等
  - 示例："绿色债券的监管指引是哪个文件？"、"申请绿色项目贷款需要准备哪些材料？"、"什么是海洋牧场？"、"有没有海上风电的成功案例？"

- **企业画像与工商风险**：企业基本信息、股权结构、司法风险、经营异常、环保信用等
  - 示例："查一下青岛蓝色能源有限公司的工商信息和环保评级"、"这家公司有没有行政处罚记录？"

- **客户经理与内部资料**：客户经理联系方式、负责区域、对接方式
  - 示例："给我青岛蓝色能源有限公司对应的客户经理联系方式"

- **交易对手 / 供应链关系**：上下游伙伴、供应链合作企业、关联方查询
  - 示例："查下海上风电项目的主要供应商有哪些？"、"这家企业的核心交易对手是谁？"

- **征信 / 信用评级 / 风险信息**：企业信用、违约记录、信用评级、风险提示
  - 示例："查询XX公司的信用评级和违约风险"、"有没有近期的征信异常？"

**处理方式**：调用 `handoff_to_toolbox`，并在 `task_description` 中描述要查询的关键信息。ToolBox Agent 会自动选择合适的查询工具、可能多次调用工具，再返回整理后的结果。若在判定过程中出现任一复杂任务特征，必须立即停止并改为调用 `handoff_to_plan`。

### 3. 移交复杂任务（调用 handoff_to_plan 工具）

**适用场景**：只要满足以下任一条件，必须移交复杂任务；一旦判定为复杂任务，禁止再尝试简单事实查询。

1. **关键词强制触发**：
   - 用户话语中出现“蓝色金融”“绿色金融”“蓝绿色金融”或其变体（含英文描述 Blue Finance/Green Finance/Blue-Green Finance 等），无论语境如何，均视为复杂任务。

2. **判断类问题**：
   - "是否符合"、"能否"、"可否"、"准入"、"达标"、"评估"、"判断"、"分析"

3. **推荐决策类**：
   - "推荐什么产品"、"适合什么"、"选择哪个"、"最佳方案"

4. **多维度查询**：
   - 同时涉及多个方面（如"产品+优惠+条件"）

5. **团队协作场景**：
   - 需要企业画像 + 准入评估 + 产品推荐等多个团队协作

6. **对公金融相关情境**：
   - 与对公金融、海洋经济、新能源等领域的方案设计、政策解读、案例分析等相关深度问题

**处理方式**：调用 `handoff_to_plan` 工具，并在 `task_description` 参数中说明原因

**示例**：
- 用户："XX公司是否符合对公金融准入标准？"
  → 调用 `handoff_to_plan(task_description="需要综合评估企业资质和准入条件")`

- 用户："推荐什么产品最适合海上风电项目？"
  → 调用 `handoff_to_plan(task_description="需要分析企业情况和项目特点，匹配适配产品")`

## 决策流程

1. **检查直接回复场景** → 检测到熔断关键词或问候闲聊 → **直接回复**
2. **检查复杂任务判定条件** → 只要满足任一条，包括对公金融关键词 → **调用 `handoff_to_plan`**
3. **检查简单事实查询条件** → 在确认未触发复杂任务后匹配 → **调用 `handoff_to_toolbox`**
4. **兜底策略** → **以上都不满足时，必须调用 `handoff_to_plan`**（确保所有问题都有处理路径）

## 核心逻辑

**关键原则**：所有问题必须得到处理，不存在无法处理的场景；简单事实查询与复杂任务判定严格互斥，不得交叉命中。

- **熔断场景**：立即中断，直接回复标准化拒绝信息
- **简单事实查询**：直接调用对应工具快速响应
- **复杂任务**：调用 `handoff_to_plan` 移交计划执行流程
- **兜底机制**：如果以上场景都不匹配，**必须调用 `handoff_to_plan`** 作为最终保障

## 重要提示

- 熔断场景必须立即中断，直接回复标准化拒绝信息
- 简单事实查询直接调用对应工具，无需移交复杂流程
- 复杂任务通过调用 `handoff_to_plan` 工具来移交
- **所有工具都不符合的情况下，必须调用 `handoff_to_plan` 作为兜底方案**
- 不要输出 JSON 格式
- 不确定时优先选择调用 `handoff_to_plan`

## 重要
- 涉及到企业画像团队和其他团队共同完成的计划，先做企业画像团队，然后蓝绿准入团队，再然后蓝绿推荐产品团队
"""
)

# Supervisor提示词 - 通过Prompt引导LLM选择正确工具
supervisor_prompt = SystemMessage(
    content="""您是某某银行对公金融复杂任务调度官，专注于计划制定、审批协同与团队执行调度。

## 当前背景
- 用户请求已被判定为**复杂任务**（涉及判断、推荐、多维度分析）
- 必须通过制定计划、协调多个专业团队来完成任务
- 所有回答须基于团队返回的专业分析数据

## 核心职责与决策树

### 阶段1：计划制定（首次进入或无计划状态）
**必须调用 plan 工具**，制定多步骤执行计划

**计划制定决策逻辑**：

**基于用户输入和团队前置条件动态制定计划**：

**关键原则**：根据用户输入的具体内容和团队工具的前置条件来决定调用哪些团队，不要固定模式化调用。

**团队工具前置条件分析**：

1. **企业画像团队**：
   - 前置条件：必须输入客户名称或者社会统一信息代码
   - 适用场景：用户提供了具体企业名称或统一社会信用代码
   - 不适用场景：用户只提到行业类型、项目类型，没有具体企业信息

2. **蓝绿准入团队**：
   - 前置条件：用户输入必须明确企业名称或者项目准入的意图
   - 适用场景：用户明确询问"准入"、"符合"、"标准"、"判断"等关键词，或者提供了具体企业/项目
   - 不适用场景：用户只询问产品推荐，没有准入评估需求

3. **蓝绿产品团队**：
   - 无前置条件限制
   - 适用场景：任何涉及产品推荐、产品咨询的问题

4. **蓝绿解决方案团队**：
   - 前置条件：需要完整的客户画像、准入判断和产品推荐作为依据
   - 适用场景：需要生成综合金融服务方案，且已有前序团队的分析结果

**计划制定指南**：

1. **分析用户输入**：仔细分析用户输入中是否包含具体企业名称、统一社会信用代码、项目名称、准入意图等关键信息

2. **检查前置条件**：根据团队工具的前置条件，只调用满足条件的团队

3. **按需调用**：不要固定模式化调用团队，只在确实需要时才调用

4. **产品库查询场景**：当用户询问产品库信息、产品列表、产品准入条件、特定资质要求或持有特定许可证的企业可以申请哪些产品时，必须调用蓝绿产品团队。产品团队会自动使用product_query_tool工具进行查询，该工具支持多种查询方式：

   **特别注意**：对于"产品库中有哪些蓝绿色金融产品？产品准入条件是什么？"这类问题，必须调用蓝绿产品团队，产品团队会同时查询产品列表和产品准入条件，无需调用其他团队。

**示例场景**：

- **产品库查询场景**（必须调用蓝绿产品团队）：
  - "产品库中有哪些蓝绿色金融产品？" → 只调用蓝绿产品团队
  - "查询所有绿色信贷产品" → 只调用蓝绿产品团队  
  - "蓝色金融产品有哪些类型？" → 只调用蓝绿产品团队
  - "产品准入条件是什么？" → 只调用蓝绿产品团队（产品团队会查询产品准入条件）
  - "持有环保许可证的企业可以申请哪些产品？" → 只调用蓝绿产品团队
  - "查询特定资质要求的产品列表" → 只调用蓝绿产品团队

- **准入条件区分说明**：
  - **产品准入条件**：指具体金融产品的申请条件、资质要求、适用对象等，由产品团队负责查询和解释
  - **项目准入评估**：指对具体项目是否符合对公金融标准的综合判断，由准入团队负责评估

- 用户询问特定资质企业适用的金融产品
  → 只调用蓝绿产品团队（没有具体企业，不需要企业画像；没有准入意图，不需要准入评估）

- 用户查询具体项目的准入资格评估
  → 只调用蓝绿准入团队（有具体项目名称和准入意图，不需要企业画像）

- 用户为具体企业的特定项目寻求产品推荐
  → 调用企业画像团队 + 蓝绿产品团队（有具体企业名称，需要企业画像；有产品推荐需求，需要产品团队）

- 用户需要判断具体项目是否符合准入标准
  → 只调用蓝绿准入团队（有具体项目名称和准入意图，不需要企业画像）

**plan工具调用要点**：
- summary: 用一句话概括任务目标
- steps: 根据上述决策逻辑制定合适的步骤，每个步骤明确指定handoffTarget（团队名称）
- **thinking: 必须提供制定计划的思考过程**，包括：
  - 为什么选择这些团队
  - 步骤之间的逻辑关系
  - 如何满足团队工具的前置条件
  - 计划制定的整体思路
- 团队名称必须是：enterprise_profile_team、blue_green_access_team、blue_green_product_team、blue_green_solution_team

**重要提示**：必须提供thinking参数，否则前端无法显示思考过程信息！

### 阶段2：计划审批（计划状态=pending）
**必须调用 human_approval 工具**，将计划提交给人工审批

### 阶段3：计划执行（计划状态=approved）
**必须调用对应的 transfer_to_* 工具**，将任务移交给指定团队
- 根据 state.plan.nextStepId 查找对应步骤
- 调用该步骤的 handoffTarget 对应的工具（如 transfer_to_enterprise_profile_team）
- 等待团队返回执行结果
- Replan节点会自动更新进度并路由到下一步骤

### 阶段4：计划完成（所有步骤已完成）
**综合所有团队反馈，生成最终结论**
- 汇总各团队的分析结果
- 给出明确的建议或答案
- 自然结束对话（不调用任何工具）

## 关键规则

### 阶段判断（每次必须执行）
1. 检查 state.plan：
   - 如果为空 → **阶段1**（制定计划）→ 调用 plan
   - 如果 status=pending → **阶段2**（等待审批）→ 调用 human_approval
   - 如果 status=approved → **阶段3**（执行计划）→ 调用 transfer_to_{team}
   - 如果所有步骤完成 → **阶段4**（汇总结果）→ 不调用工具

重要：如果用户在审批阶段拒绝计划，系统会自动终止会话。此后会话将被锁定，无法继续执行任何操作。

2. 严格遵循阶段对应的工具：
   - **阶段1** → 只能调用 plan
   - **阶段2** → 只能调用 human_approval
   - **阶段3** → 只能调用 transfer_to_{team}（基于 nextStepId 的 handoffTarget）
   - **阶段4** → 不调用工具，直接回复

### 执行阶段3的详细指南
当 state.plan.status = "approved" 时：
1. 读取 state.plan.nextStepId（如 "step-001"）
2. 在 state.plan.steps 中查找对应步骤
3. 读取该步骤的 handoffTarget（如 "enterprise_profile_team"）
4. 调用对应工具：transfer_to_{handoffTarget}

示例：
```
state.plan = {
  "status": "approved",
  "nextStepId": "step-001",
  "steps": [
    {"stepId": "step-001", "handoffTarget": "enterprise_profile_team", ...}
  ]
}
→ 第一步必须调用 transfer_to_enterprise_profile_team
```

### 禁止事项
- 在 pending 状态重新调用 plan（会覆盖待审批计划）
- 在无计划时调用 human_approval（没有计划可审批）
- 在 pending 状态调用 transfer_to_*（必须先通过审批）
- 跳过人工审批直接执行（违反流程）
- 调用不匹配的团队（必须严格按 nextStepId 的 handoffTarget）
- 跳过plan直接调用团队（所有复杂任务必须先制定计划）
- 单步骤计划（判断/推荐类任务通常需要2-3个步骤）
- 虚构数据（只基于团队返回的真实数据进行总结）
- 在计划被拒绝后尝试任何操作（会话已终止，需新开会话）
- 根据用户输入内容决定是否需要企业画像和准入团队

### 最佳实践
1. **计划粒度适中**：每个步骤对应一个团队的完整分析
2. **步骤依赖清晰**：后续步骤基于前序步骤的结果
3. **目标明确**：每个步骤的goal清晰描述预期产出
4. **按需调用团队**：只在必要时调用企业画像和准入团队

## 可用团队
- **enterprise_profile_team**: 企业画像分析（基本信息、风险状况、财务数据）**前置条件：必须输入客户名称或者社会统一信息代码**
- **blue_green_access_team**: 蓝绿准入评估（准入条件判断、合规性检查）**前置条件：用户输入必须明确企业名称或者项目准入的意图**
- **blue_green_product_team**: 产品推荐服务（产品匹配、优惠政策）
- **blue_green_solution_team**: 综合方案设计（融资方案、业务建议）

## 输出风格
- 简洁专业，引用团队分析结果时注明来源
- 若缺少关键信息，明确告知用户需要补充什么
- 最终结论基于数据，给出明确的"是/否"或具体推荐

## 重要
- 涉及到企业画像团队和其他团队共同完成的计划，先做企业画像团队，然后蓝绿准入团队，再然后蓝绿推荐产品团队
"""
)


# ==================== Supervisor 节点（简化版）====================


def create_supervisor_agent(checkpointer: BaseCheckpointSaver = None):
    """创建简化版的 Supervisor Agent - 拆分为简单任务LLM与计划执行LLM

    注意：此子图不包含 ToolBox Agent，ToolBox 已提升到主图层级。
    llm_simple_node 通过 Command.PARENT 路由到父图的 ToolBox 节点。
    """
    from app.multiAgent.dispatch.handoff_tools import get_all_handoff_tools
    from app.multiAgent.dispatch.plan_execute.human_approval_tool import (
        create_human_approval_tool,
    )

    # 计划相关工具
    plan_tool = create_plan_tool()
    human_approval_tool = create_human_approval_tool()

    # llm_simple 绑定的工具：仅保留两个 handoff 工具
    simple_tools = [
        handoff_to_toolbox,  # 简单查询移交工具（移交给父图的 ToolBox）
        handoff_to_plan,  # 复杂任务移交工具（移交给计划执行流程）
    ]

    llm_simple = get_llm(disable_streaming=False)
    llm_plan = get_llm(disable_streaming=False)

    plan_tool_node = ToolNode([plan_tool], handle_tool_errors=False)
    human_approval_tool_node = ToolNode([human_approval_tool], handle_tool_errors=False)

    def llm_simple_node(state: UniState, config: RunnableConfig) -> Command:
        """简化的路由器节点 - 纯路由决策

        职责：
        1. 识别用户意图
        2. 路由到合适的下游节点
        3. 输出thinking信息到前端

        路由场景：
        - 直接回复（闲聊、确认）-> END
        - 数据查询 -> Command.PARENT -> ToolBox（父图节点）
        - 复杂任务 -> handoff_to_plan -> llm_plan（子图内）
        """
        messages = list(state.get(StateFields.MESSAGES, []))

        # 会话锁定检查
        is_locked, lock_message = _check_session_lock(state)
        # plan_rejected场景已有拒绝消息，直接结束
        if is_locked and not lock_message:
            logger.debug("[Simple-路由] 会话已锁定(plan_rejected)，直接结束")
            return Command(goto=END)

        # ===== 正常路由决策 =====
        logger.debug("[Simple-路由] 进行路由决策")

        llm_with_tools = llm_simple.bind_tools(simple_tools)
        response: AIMessage = llm_with_tools.invoke(
            [simple_router_prompt] + messages, config
        )
        logger.info(f"[Simple-路由] LLM响应: {response.content}")
        logger.info(f"[Simple-路由] LLM返回工具调用: {response.tool_calls}")
        tool_calls = getattr(response, "tool_calls", None)

        # 有工具调用
        if tool_calls:
            logger.debug(
                f"[Simple-路由] LLM返回工具调用: {[tc.get('name') for tc in tool_calls]}"
            )
            tool_call = tool_calls[0]  # 取第一个工具调用
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})

            if tool_name == "handoff_to_plan":
                # 复杂任务移交（子图内路由）
                task_desc = tool_args.get("task_description", "")
                logger.info(
                    f"[Simple-路由] 移交给复杂任务处理，任务描述: {task_desc}..."
                )
                # 输出thinking信息到前端
                thinking_content = f"让我理解您的意图，这是一个复杂任务，需要制定详细计划来处理：{task_desc}"
                _output_thinking_info(thinking_content, config)

                # 为handoff_to_plan工具调用添加对应的工具响应消息，以满足API要求
                
                # 创建对应的工具响应消息
                tool_response = ToolMessage(
                    content=f"已接收计划任务移交请求，正在为您制定详细计划。任务描述：{task_desc[:100]}...", 
                    name="handoff_to_plan",
                    tool_call_id=tool_call.get('id'),
                )
                
                return Command(
                    goto="llm_plan",
                    update={StateFields.MESSAGES: messages + [response, tool_response]},
                )
            elif tool_name == "handoff_to_toolbox":
                # 简单查询移交（跨层级路由到父图）
                task_desc = tool_args.get("task_description", "")
                logger.info(
                    f"[Simple-路由] 移交给 ToolBox（父图节点），任务描述: {task_desc}..."
                )

                # 输出thinking信息到前端
                thinking_content = (
                    f"让我理解您的意图，这是一个简单查询任务，需要查询：{task_desc}"
                )
                _output_thinking_info(thinking_content, config)

                # 为handoff_to_toolbox工具调用添加对应的工具响应消息，以满足API要求
                
                # 创建对应的工具响应消息
                tool_response = ToolMessage(
                    content=f"已接收工具箱查询任务移交请求，正在为您查询相关信息。任务描述：{task_desc[:100]}...", 
                    name="handoff_to_toolbox",
                    tool_call_id=tool_call.get('id'),
                )

                return Command(
                    goto="ToolBox",
                    update={StateFields.MESSAGES: messages + [response, tool_response]},
                    graph=Command.PARENT,
                )

        # 直接回复（熔断场景）
        logger.info(f"[Simple-路由] 直接回复用户: {response.content}...")

        # 输出thinking信息到前端
        thinking_content = (
            f"让我理解您的意图，这是一个可以直接回复的场景：{response.content[:100]}..."
        )
        _output_thinking_info(thinking_content, config)

        # 如果response包含工具调用，则添加对应的工具响应消息
        updated_messages = [response]
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_response = ToolMessage(
                    content=f"已处理直接回复请求：{response.content[:100]}...",
                    name=tool_call.get('name', ''),
                    tool_call_id=tool_call.get('id'),
                )
                updated_messages.append(tool_response)

        return Command(
            goto=END,
            update={StateFields.MESSAGES: messages + updated_messages},
        )

    def llm_plan_node(state: UniState, config: RunnableConfig):
        """计划执行节点 - 调用 LLM 并返回响应

        职责单一：只负责 LLM 调用，后续路由交给 tools_condition 条件边处理
        """
        messages = list(state.get(StateFields.MESSAGES, []))
        logger.debug(f"[Supervisor-Plan] 处理 {len(messages)} 条消息")

        if StateFields.APPROVAL_RESULT in state and state.get(
            StateFields.APPROVAL_RESULT
        ):
            logger.debug("[Supervisor-Plan] 审批通过，执行plan executor")
            return Command(
                goto="plan_executor",
                graph=Command.PARENT,
                update={**state},
            )

        # 会话锁定检查
        is_locked, lock_message = _check_session_lock(state)
        if is_locked:
            if lock_message:
                logger.warning("[Supervisor-Plan] 会话已锁定，添加锁定消息后结束")
                return {StateFields.MESSAGES: messages + [lock_message]}
            logger.debug("[Supervisor-Plan] 会话已锁定(plan_rejected)，返回空更新")
            return {}

        # 仅绑定计划工具，人工审批改为独立节点
        logger.debug("[Supervisor-Plan] 绑定计划工具以生成结构化plan")

        llm_with_tools = llm_plan.bind_tools([plan_tool])
        logger.info(f"[llm_plan_node] LLM请求消息: {messages}")
        response: AIMessage = llm_with_tools.invoke(
            [supervisor_prompt] + messages, config
        )
        logger.info(f"[llm_plan_node] LLM响应: {response.content}")
        logger.info(f"[llm_plan_node] LLM返回工具调用: {response.tool_calls}")

        # 将LLM响应添加到消息历史中，这样在后续的工具调用处理中，消息历史会包含完整的交互记录
        updated_messages = messages + [response]
        
        # 返回包含LLM响应的消息历史，让条件边根据是否有tool_calls决定路由到工具节点还是结束
        return {StateFields.MESSAGES: updated_messages}

    def auto_human_approval_node(state: UniState) -> Command:
        """在生成plan后自动触发人工审批工具调用"""

        plan_data = state.get(StateFields.PLAN)
        if not plan_data:
            logger.warning(
                "[Supervisor-Plan] plan_tool执行后缺少plan数据，跳回llm_plan"
            )
            return Command(goto="llm_plan")

        plan_status = plan_data.get("status")
        if plan_status != "pending":
            logger.info(
                f"[Supervisor-Plan] plan状态为 {plan_status}，无需触发人工审批，跳回llm_plan"
            )
            return Command(goto="llm_plan")

        tool_call_id = f"auto-human-{uuid.uuid4().hex[:8]}"
        ai_message = AIMessage(
            content="计划已生成，触发人工审批流程。",
            tool_calls=[{"name": "human_approval", "args": {}, "id": tool_call_id}],
        )
        logger.info("[Supervisor-Plan] 自动注入human_approval工具调用")
        return {StateFields.MESSAGES: [ai_message]}

    # 构建简化的 supervisor 子图
    supervisor_graph = (
        StateGraph(UniState)
        .add_node("llm_simple", llm_simple_node)
        .add_node("llm_plan", llm_plan_node)
        .add_node("plan_tool_node", plan_tool_node)
        .add_node("auto_human_approval", auto_human_approval_node)
        .add_node("human_approval_tool_node", human_approval_tool_node)
        .add_edge(START, "llm_simple")
        .add_conditional_edges(
            "llm_plan",
            tools_condition,
            {
                "tools": "plan_tool_node",
                "__end__": END,
            },
        )
        .add_edge("plan_tool_node", "auto_human_approval")
        .add_edge("auto_human_approval", "human_approval_tool_node")
        .add_edge("human_approval_tool_node", "llm_plan")
    ).compile(checkpointer=checkpointer)

    return supervisor_graph


# ==================== 统一Supervisor Graph（简化版）====================


def create_unified_supervisor():
    """创建统一的Supervisor Graph（简化版）

    - 简化图结构：START -> supervisor -> team_nodes
    - 团队执行完毕统一回到 replan，由 replan 决定下一个团队或结束
    - 计划相关决策集中在 supervisor 内部的 plan LLM
    - 人工审批通过 human_approval 工具实现
    """
    return _get_unified_supervisor().supervisor_graph


def create_unified_supervisor_for_studio():
    """
    创建用于LangGraph Studio的Supervisor Graph（无checkpointer版本）

    注意：
    - 仅用于LangGraph Studio调试
    - 不要在生产环境使用
    - FastAPI服务应继续使用 create_unified_supervisor()
    - ToolBox 已提升到主图层级，与其他 team 平级

    Returns:
        StateGraph: 不带checkpointer的supervisor图
    """
    from app.multiAgent.agents.enterprise_profile_agent import EnterpriseProfileAgent
    from app.multiAgent.analysis.blue_green_access_agent import BlueGreenAccessAgent
    from app.multiAgent.analysis.blue_green_product_agent import BlueGreenProductAgent
    from app.multiAgent.analysis.blue_green_solution_agent import BlueGreenSolutionAgent
    from app.multiAgent.agents.toolbox_agent import ToolBoxAgent

    # 注意：这里不传入checkpointer，让LangGraph Studio自动处理
    checkpointer = None

    # 创建 supervisor agent（不使用checkpointer）
    supervisor_agent = create_supervisor_agent(
        checkpointer=None,
    )

    # 创建 ToolBox Agent 实例（提升到主图层级）
    toolbox_agent = ToolBoxAgent(checkpointer=None)

    # 创建团队 agent 实例（不使用checkpointer）
    enterprise_profile_agent = EnterpriseProfileAgent(checkpointer=None)
    blue_green_access_agent = BlueGreenAccessAgent(checkpointer=None)
    blue_green_product_agent = BlueGreenProductAgent(checkpointer=None)
    blue_green_solution_agent = BlueGreenSolutionAgent(checkpointer=None)
    replan_node = create_replan_node()
    report_summary_node = create_report_summary_node()
    reporter_node = create_reporter_node()

    from app.multiAgent.dispatch.handoff_tools import get_all_handoff_tools

    handoff_tools = get_all_handoff_tools()
    handoff_tools_node = ToolNode(handoff_tools, handle_tool_errors=False)

    # 构建主图（不传入checkpointer）
    graph = (
        StateGraph(UniState)
        # 添加所有节点
        .add_node("supervisor", supervisor_agent)
        .add_node("ToolBox", toolbox_agent.graph)
        .add_node("enterprise_profile_team", enterprise_profile_agent.graph)
        .add_node("blue_green_access_team", blue_green_access_agent.graph)
        .add_node("blue_green_product_team", blue_green_product_agent.graph)
        .add_node("blue_green_solution_team", blue_green_solution_agent.graph)
        .add_node("replan", replan_node)
        .add_node("report_summary", report_summary_node)
        .add_node("reporter", reporter_node)
        .add_node("plan_executor", plan_executor)
        .add_node("handoff_tools_node", handoff_tools_node)
        # 起始边
        .add_edge(START, "supervisor")
        # ToolBox 完成后直接结束
        .add_edge("ToolBox", END)
        # 团队节点执行后进入replan节点再决定下一步
        .add_edge("enterprise_profile_team", "replan")
        .add_edge("blue_green_access_team", "replan")
        .add_edge("blue_green_product_team", "replan")
        .add_edge("blue_green_solution_team", "replan")
        .add_edge("plan_executor", "handoff_tools_node")
        .add_edge("report_summary", "reporter")
        # replan通过Command动态路由到report_summary或下一团队
        # reporter生成最终报告后直接结束（在reporter_node内部goto=END）
    ).compile()  # 不传入checkpointer参数

    return graph


# ==================== 统一执行接口 ====================


class UnifiedSupervisor:
    """
    统一监督执行类（简化版）

    - 使用极简的 UniState（仅包含 messages）
    - 所有决策逻辑由 LLM 通过工具自主协调
    - 人工审批通过 human_approval_tool 实现，使用 LangGraph 内置的 interrupt() 机制
    - 所有上下文通过消息流转，无额外状态字段
    """

    def __init__(self):
        # 使用统一的checkpointer实例
        self.checkpointer = InMemorySaver()

        # 创建简化的supervisor graph
        self.supervisor_graph = self._create_simplified_supervisor_graph()

    def _create_simplified_supervisor_graph(self):
        """
        创建简化的Supervisor图

        架构说明：
        - supervisor 子图只负责路由决策和计划执行
        - ToolBox 提升到主图层级，与其他 team 平级
        - supervisor 通过 Command.PARENT 路由到 ToolBox

        流程：
        START -> supervisor
        supervisor -> ToolBox (通过 Command.PARENT)
        supervisor -> team_nodes (复杂任务)
        team_nodes -> replan -> (下一团队 | reporter | END)
        ToolBox -> END (简单查询直接结束)
        """
        from app.multiAgent.agents.enterprise_profile_agent import (
            EnterpriseProfileAgent,
        )
        from app.multiAgent.analysis.blue_green_access_agent import BlueGreenAccessAgent
        from app.multiAgent.analysis.blue_green_product_agent import (
            BlueGreenProductAgent,
        )
        from app.multiAgent.analysis.blue_green_solution_agent import (
            BlueGreenSolutionAgent,
        )
        from app.multiAgent.agents.toolbox_agent import ToolBoxAgent
        from app.multiAgent.dispatch.handoff_tools import get_all_handoff_tools

        checkpointer = self.checkpointer

        # 创建 supervisor agent（内部已包含 supervisor_node 和 tools）
        supervisor_agent = create_supervisor_agent(checkpointer)

        # 创建 ToolBox Agent 实例（提升到主图层级）
        toolbox_agent = ToolBoxAgent(checkpointer=checkpointer)

        # 创建团队 agent 实例
        enterprise_profile_agent = EnterpriseProfileAgent(checkpointer)
        blue_green_access_agent = BlueGreenAccessAgent(checkpointer)
        blue_green_product_agent = BlueGreenProductAgent(checkpointer)
        blue_green_solution_agent = BlueGreenSolutionAgent(checkpointer)
        replan_node = create_replan_node()
        report_summary_node = create_report_summary_node()
        reporter_node = create_reporter_node()

        # 创建handoff_tools节点
        handoff_tools = get_all_handoff_tools()
        handoff_tools_node = ToolNode(handoff_tools, handle_tool_errors=False)

        # 构建主图
        graph = (
            StateGraph(UniState)
            # 添加所有节点
            .add_node("supervisor", supervisor_agent)
            .add_node("ToolBox", toolbox_agent.graph)
            .add_node("enterprise_profile_team", enterprise_profile_agent.graph)
            .add_node("blue_green_access_team", blue_green_access_agent.graph)
            .add_node("blue_green_product_team", blue_green_product_agent.graph)
            .add_node("blue_green_solution_team", blue_green_solution_agent.graph)
            .add_node("replan", replan_node)
            .add_node("report_summary", report_summary_node)
            .add_node("reporter", reporter_node)
            .add_node("plan_executor", plan_executor)
            .add_node("handoff_tools_node", handoff_tools_node)
            # 起始边
            .add_edge(START, "supervisor")
            # ToolBox 完成后直接结束
            .add_edge("ToolBox", END)
            # 团队节点完成后，进入replan节点评估
            .add_edge("enterprise_profile_team", "replan")
            .add_edge("blue_green_access_team", "replan")
            .add_edge("blue_green_product_team", "replan")
            .add_edge("blue_green_solution_team", "replan")
            .add_edge("plan_executor", "handoff_tools_node")
            .add_edge("report_summary", "reporter")
            # replan通过Command动态路由到report_summary或下一团队
            # reporter生成最终报告后直接结束（在reporter_node内部goto=END）
        ).compile(checkpointer=checkpointer)

        return graph

    async def _process_stream_chunks(self, stream_generator) -> AsyncIterator:
        """处理流式输出的异步生成器函数"""
        from app.api.models import GraphStreamResult

        async for idTuple, stream_mode, chunk in stream_generator:
            # logger.info(f"_process_stream_chunks - idTuple: {idTuple}, stream_mode: {stream_mode}, chunk:{chunk}")
            if stream_mode == "messages":
                # 检查是否是 AIMessage 且有内容
                if (
                    isinstance(chunk[0], (AIMessage, AIMessageChunk))
                    and chunk[0].content
                    and isinstance(chunk[1], dict)
                ):
                    langgraph_node = chunk[1].get("langgraph_node", "")
                    depth = len(idTuple)

                    # 判断是否为终端节点（需要输出到前端的最终消息）
                    # 1. reporter节点在根层级（depth=0）- 生成最终报告
                    # 2. llm_simple节点在第一层子图（depth=1）- 简单任务的直接回复
                    # 3. ToolBox子图中的call_llm节点 - 工具调用的LLM响应
                    is_reporter_output = langgraph_node == "reporter" and depth == 0
                    # is_simple_output = depth == 1 and langgraph_node == "llm_simple"
                    is_toolbox_output = (
                        depth == 1
                        and idTuple[0].startswith("ToolBox")
                        and langgraph_node == "call_llm"
                    )

                    is_terminal = (
                        # is_reporter_output or is_simple_output or is_toolbox_output
                        is_reporter_output or is_toolbox_output
                    )

                    if is_terminal:
                        yield GraphStreamResult(
                            status="success",
                            stream_mode=stream_mode,
                            data=chunk[0],
                        )
            elif stream_mode == "updates":
                # 只输出最后一个interrupt信息
                if (
                    isinstance(chunk, dict)
                    and "__interrupt__" in chunk
                    and chunk["__interrupt__"]
                    and isinstance(chunk["__interrupt__"][0], Interrupt)
                    and len(idTuple) == 0
                ):
                    yield GraphStreamResult(
                        status="interrupted",
                        stream_mode=stream_mode,
                        data=chunk,
                        interrupt_data=chunk["__interrupt__"][0].value,
                    )
            elif stream_mode == "custom":
                # 处理自定义流模式，用于返回知识库解析信息、思考信息、进度信息和角标信息
                logger.info(f"流式执行中检测到自定义流模式: {chunk}")
                if isinstance(chunk, dict):
                    if chunk.get("type") == "knowledge_base":
                        logger.info(f"流式执行中检测到知识库解析信息: {chunk}")
                        yield GraphStreamResult(
                            status="success",
                            stream_mode=stream_mode,
                            data=chunk,
                        )
                    elif chunk.get("type") == "thinking":
                        logger.info(f"流式执行中检测到思考信息: {chunk}")
                        yield GraphStreamResult(
                            status="success",
                            stream_mode=stream_mode,
                            data=chunk,  # 将thinking信息通过data字段发送，确保前端能接收到
                        )
                    elif chunk.get("type") == "progress":
                        logger.info(f"流式执行中检测到进度信息: {chunk}")
                        yield GraphStreamResult(
                            status="success",
                            stream_mode=stream_mode,
                            data=chunk,
                        )
                    elif chunk.get("type") == "tip":
                        logger.info(f"流式执行中检测到角标信息: {chunk}")
                        yield GraphStreamResult(
                            status="success",
                            stream_mode=stream_mode,
                            data=chunk,
                        )

    async def stream(self, request) -> AsyncIterator:
        """流式执行，正确处理中断 - 使用扁平化状态"""
        session_id = request.session_id
        config = {"configurable": {"thread_id": session_id}}

        # 检查是否为中断恢复请求
        # LangGraph的interrupt()机制会自动处理恢复，用户决策直接作为input传递
        if request.is_resume:
            logger.info(f"流式执行中检测到中断恢复请求，session_id: {session_id}")
            # 使用Command(resume=...)直接恢复执行
            # LangGraph会将用户输入传递给interrupt()调用点
            try:
                logger.info(f"中断恢复：使用Command(resume='{request.input}')恢复执行")
                stream_generator = self.supervisor_graph.astream(
                    Command(resume=request.input),
                    config,
                    subgraphs=True,
                    stream_mode=["messages", "updates", "custom"],
                )
                async for result in self._process_stream_chunks(stream_generator):
                    yield result
                return
            except (ToolSystemError, ToolUserError) as e:
                # 延迟导入避免循环依赖
                from app.api.models import GraphStreamResult

                # 捕获由工具装饰器转换的 ToolSystemError 和 ToolUserError
                error_category = "system" if isinstance(e, ToolSystemError) else "user"
                logger.error(
                    f"流式恢复执行时出错 [类型: {error_category}]: {e}", exc_info=True
                )
                yield GraphStreamResult(
                    status="error",
                    error_message=str(e),
                )
                return

        # 创建初始状态
        initial_state = create_initial_state(
            user_input=request.input,
            session_id=session_id,
        )

        try:
            # 使用stream执行
            stream_generator = self.supervisor_graph.astream(
                initial_state,
                config,
                subgraphs=True,
                stream_mode=["messages", "updates", "custom"],
            )
            async for result in self._process_stream_chunks(stream_generator):
                yield result
        except (ToolSystemError, ToolUserError) as e:
            # 延迟导入避免循环依赖
            from app.api.models import GraphStreamResult

            # 捕获由工具装饰器转换的 ToolSystemError 和 ToolUserError
            error_category = "system" if isinstance(e, ToolSystemError) else "user"
            logger.error(f"流式执行时出错 [类型: {error_category}]: {e}", exc_info=True)
            yield GraphStreamResult(
                status="error",
                error_message=str(e),
            )


# 全局实例（延迟初始化）
_unified_supervisor = None


def _get_unified_supervisor() -> UnifiedSupervisor:
    """获取全局UnifiedSupervisor实例（延迟初始化）"""
    global _unified_supervisor
    if _unified_supervisor is None:
        _unified_supervisor = UnifiedSupervisor()
    return _unified_supervisor


def stream_with_unified_supervisor(
    request,
) -> AsyncIterator:
    """流式执行（兼容接口）

    Args:
        request: MainGraphRequest对象（类型通过延迟导入在函数内部使用）

    Returns:
        AsyncIterator[GraphStreamResult]: 流式结果迭代器
    """
    return _get_unified_supervisor().stream(request)
