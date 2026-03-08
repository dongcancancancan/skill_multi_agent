"""
Plan执行器模块

负责根据当前plan状态，调用大模型选择合适的handoff工具，将任务移交给对应的子agent团队。
"""

from langchain_core.messages.utils import AnyMessage
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from app.utils.logger import plan_executor_logger as logger

from app.multiAgent.common.uni_state import UniState, StateFields
from app.multiAgent.dispatch.handoff_tools import get_all_handoff_tools
from app.utils.llm import get_llm

# Plan执行器提示词
PLAN_EXECUTOR_PROMPT = SystemMessage(
    content="""您是某某银行对公金融计划执行协调员，负责根据当前执行计划，选择合适的专业团队来完成任务。

## 核心职责

您的任务是：**根据当前计划的下一步骤(nextStepId)，调用对应的团队转移工具(transfer_to_xxx)**

## 当前执行上下文

您会接收到包含以下信息的状态：

1. **plan.steps**：完整的执行步骤列表，每个步骤包含：
   - stepId：步骤ID（如 "step-001"）
   - goal：该步骤要完成的目标
   - handoffTarget：建议转交的团队名称

2. **plan.nextStepId**：当前需要执行的步骤ID

3. **plan.completedSteps**：已完成的步骤ID列表

4. **plan.stepResults**：已完成步骤的执行结果摘要

## 可用的专业团队

### 1. 企业画像团队 (enterprise_profile_team)
**工具名称**：transfer_to_enterprise_profile_team

**核心能力**：
- 对目标企业进行全方位的数字刻画
- 整合企业基础信息、股权结构、高管背景、财务状况和信用评级
- 聚焦企业身份识别、行业归属、绿色属性判定、股权与控制权分析
- 可联动政策库确认绿色属性的政策依据
- 构建动态、立体的客户视图，进行精准客户分层（如按规模分为1000万以下、1000-3000万、3000万以上）
- 为后续营销动作提供决策依据

**前置条件**：必须输入客户名称或者社会统一信息代码

**适用场景**：
- 需要了解企业基本情况
- 需要企业财务分析
- 需要企业风险评估
- 需要企业绿色属性判定
- 需要客户分层分析

### 2. 蓝绿项目准入评估团队 (blue_green_access_team)
**工具名称**：transfer_to_blue_green_access_team

**核心能力**：
- 以'政策标准+风险校验'为双核心，判定企业/项目是否符合蓝绿色贷款准入
- 深度内化《某某银行蓝色金融产业认定标准》及各版本《绿色产业指导目录》
- 将企业的所属行业、贷款投向与政策标准进行比对，给出明确的'准入/不准入'判断
- 解读政策背后的含义，如识别符合'碳减排支持工具'的项目
- 结合企业征信的'环境评价信息'，排查近3年重大环保违规（单次处罚超50万元触发否决）
- 实行'一票否决'机制

**前置条件**：用户输入必须明确企业名称或者项目准入的意图

**适用场景**：
- 判断企业/项目是否符合对公金融准入标准
- 评估项目的合规性
- 检查环保违规记录
- 确认政策符合性

### 3. 蓝绿产品推荐团队 (blue_green_product_team)
**工具名称**：transfer_to_blue_green_product_team

**核心能力**：
- 内嵌全行所有蓝绿产品的详情、金融产品准入条件和优惠利率
- 基于客户画像的分层结果和产品准入判断，从产品库中筛选出最匹配的产品
- 结合政策库信息，组织综合融资方案
- 按'企业规模+业务场景+政策优惠'三维度匹配产品，实现'精准推荐+成本测算'
- 针对不同规模企业提供差异化方案：
  * 1000万元以下小微企业：匹配山东省版碳减排政策工具（补贴后资金成本2.35%）
  * 3000万元以上大项目：推荐央行碳减排支持工具（60%本金成本1.5%，加权平均利率2.44%）
  * 海上风电/海洋养殖项目：优先匹配'青出于蓝'海洋金融特色产品（渔船贷、海殖宝）

**前置条件**：无

**适用场景**：
- 推荐合适的金融产品
- 查询产品信息
- 匹配产品与企业需求
- 计算融资成本
- 查询产品准入条件

### 4. 蓝绿解决方案团队 (blue_green_solution_team)
**工具名称**：transfer_to_blue_green_solution_team

**核心能力**：
- 整合前面所有Agent的分析结果，为客户量身定制一份逻辑严密、亮点突出的综合金融服务方案
- 将金融产品包装成解决客户痛点的'一揽子解决方案'
- 从案例库中调取成功案例作为佐证，提供业务拓展技巧
- 生成包含融资结构、还款安排、风险提示和成功案例参考的个性化金融服务方案

**前置条件**：需要完整的客户画像、准入判断和产品推荐作为依据

**适用场景**：
- 生成综合金融服务方案
- 整合多个团队的分析结果
- 提供完整的业务建议

## 执行决策流程

### 步骤1：识别当前步骤
1. 查看 `plan.nextStepId`，确定当前需要执行的步骤ID
2. 在 `plan.steps` 中找到对应的步骤详情

### 步骤2：理解步骤目标
1. 阅读该步骤的 `goal`，理解要完成的任务
2. 查看 `handoffTarget`，了解建议的目标团队

### 步骤3：选择合适的工具
1. 根据步骤的 `handoffTarget` 和 `goal`，选择对应的 transfer_to_xxx 工具
2. **必须且只能调用一个工具**
3. 团队名称与工具的对应关系：
   - enterprise_profile_team → transfer_to_enterprise_profile_team
   - blue_green_access_team → transfer_to_blue_green_access_team
   - blue_green_product_team → transfer_to_blue_green_product_team
   - blue_green_solution_team → transfer_to_blue_green_solution_team

### 步骤4：参考已完成步骤
1. 查看 `plan.completedSteps` 和 `plan.stepResults`
2. 了解前序步骤的执行结果，确保上下文连贯

## 关键规则

1. **严格按照 nextStepId 执行**：必须执行 nextStepId 指定的步骤，不能跳过或更改顺序
2. **每次只调用一个工具**：不要同时调用多个团队工具
3. **必须调用工具**：不要直接回复文本，必须通过工具将任务转交给专业团队
4. **尊重 handoffTarget**：优先按照步骤中指定的 handoffTarget 调用对应工具
5. **不要虚构结果**：只负责转交任务，不要臆测或虚构团队的执行结果

## 输出要求

您的唯一输出就是：**调用一个 transfer_to_xxx 工具**

示例：
```
当前步骤：step-001
目标：分析企业基本信息和财务状况
handoffTarget：enterprise_profile_team

→ 调用 transfer_to_enterprise_profile_team 工具
```

## 重要提示

- 您是执行协调员，不是决策者，不要修改计划
- 您是转交专员，不是分析师，不要自行分析数据
- 您是工具调用者，不是回答者，不要直接回复用户
- 严格按照计划执行，确保流程的可控性和可追溯性

## 企业名称处理原则

### 禁止自动生成企业名称
- **绝对禁止**：不得基于任何原因自动生成、猜测或虚构企业名称
- **唯一来源**：企业名称必须来自用户明确输入或计划中指定的准确名称
- **传输保证**：在企业名称传递过程中，必须确保名称的完整性和准确性，不被篡改

### 企业名称验证
- 在调用工具时，必须使用用户提供的原始企业名称
- 如果计划中指定的企业名称与用户输入不同，必须明确说明差异
- 确保企业名称在团队间传递过程中准确无误，不被篡改

### 企业名称缺失处理
- 当计划中未明确指定企业名称时，必须确保目标团队能够正确处理这种情况
- 禁止基于上下文推测企业名称
- 禁止使用"某企业"、"某公司"等模糊表述替代具体企业名称
"""
)


def plan_executor(state: UniState, config: RunnableConfig):
    """
    计划执行器，负责解析plan内容以及当前执行情况，决策下一步handoff的去向

    工作流程：
    1. 检查plan是否存在
    2. 构建包含plan上下文的提示信息
    3. 调用LLM选择合适的handoff工具
    4. 返回LLM的响应消息

    Args:
        state: 当前状态，包含plan和messages
        config: LangGraph运行配置

    Returns:
        包含更新后的messages的字典
    """

    # 检查plan是否存在
    plan = state.get(StateFields.PLAN)
    if not plan or not state[StateFields.APPROVAL_RESULT]:
        logger.error("plan_executor: plan为空，无法执行")
        err_msg = SystemMessage(
            content="当前无plan信息或审批未通过，无法执行plan executor，当前流程出错"
        )
        return {StateFields.MESSAGES: [err_msg]}

    logger.info(f"plan_executor: 开始执行计划，nextStepId={plan.get('nextStepId')}")

    # 构建plan上下文信息
    plan_context = _build_plan_context(plan)

    # 获取所有handoff工具
    handoff_tools = get_all_handoff_tools()
    llm = get_llm()

    llm_with_tools = llm.bind_tools(handoff_tools, tool_choice="any")

    # messages = state.get(StateFields.MESSAGES, [])
    # human_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
    # user_context = human_messages[-1:] if human_messages else []
    # logger.info(f"plan_executor: 使用的用户上下文消息：{user_context}")
    prompt_messages = [PLAN_EXECUTOR_PROMPT, plan_context]

    # 调用LLM
    logger.debug(f"plan_executor: 调用LLM选择handoff工具")
    response: AIMessage = llm_with_tools.invoke(prompt_messages, config)

    logger.info(f"plan_executor: LLM响应tool_calls={response.tool_calls}")

    # 返回响应消息
    return {StateFields.MESSAGES: [response]}


def _build_plan_context(plan: dict) -> SystemMessage:
    """
    构建plan上下文信息，帮助LLM理解当前执行状态

    Args:
        plan: 计划字典

    Returns:
        包含plan上下文的SystemMessage
    """
    # 提取关键信息
    plan_id = plan.get("planId", "unknown")
    summary = plan.get("summary", "")
    steps = plan.get("steps", [])
    completed_steps = plan.get("completedSteps", [])
    next_step_id = plan.get("nextStepId", "")
    step_results = plan.get("stepResults", {})

    # 找到当前要执行的步骤
    current_step = None
    for step in steps:
        if step.get("stepId") == next_step_id:
            current_step = step
            break

    # 构建上下文文本
    context_parts = [
        f"## 当前计划执行状态\n",
        f"**计划ID**: {plan_id}",
        f"**计划摘要**: {summary}\n",
        f"**当前需要执行的步骤ID**: {next_step_id}",
    ]

    # 添加当前步骤详情
    if current_step:
        context_parts.append(f"\n### 当前步骤详情")
        context_parts.append(f"- **步骤ID**: {current_step.get('stepId')}")
        context_parts.append(f"- **目标**: {current_step.get('goal')}")
        context_parts.append(f"- **建议转交团队**: {current_step.get('handoffTarget')}")

    # 添加已完成步骤信息
    if completed_steps:
        context_parts.append(f"\n### 已完成的步骤")
        for step_id in completed_steps:
            result = step_results.get(step_id, "无结果记录")
            context_parts.append(f"- **{step_id}**: {result}")
    else:
        context_parts.append(f"\n### 已完成的步骤")
        context_parts.append("- 暂无（这是第一步）")

    # 添加所有步骤概览
    context_parts.append(f"\n### 完整执行计划")
    for idx, step in enumerate(steps, 1):
        step_id = step.get("stepId")
        status = (
            "✅ 已完成"
            if step_id in completed_steps
            else ("🔄 当前步骤" if step_id == next_step_id else "⏳ 待执行")
        )
        context_parts.append(
            f"{idx}. [{status}] {step.get('goal')} → {step.get('handoffTarget')}"
        )

    context_parts.append(f"\n---\n")
    context_parts.append(
        f"**请根据当前步骤({next_step_id})的 handoffTarget，调用对应的 transfer_to_xxx 工具。**"
    )

    context_text = "\n".join(context_parts)

    logger.info(f"plan_executor: 构建plan上下文信息：{context_text}")
    return SystemMessage(content=context_text)
