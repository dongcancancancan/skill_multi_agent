"""基于LangGraph的蓝绿准入评估Agent
采用结构化决策模式，支持三阶段提示词分离和RAG引用
"""

from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver
from app.utils.logger import agent_logger as logger
from app.utils.llm import get_llm
from langchain_core.runnables import RunnableConfig
from app.multiAgent.tools.blue_green_access.access_query_tool import (
    access_query_tool_function,
)
from app.multiAgent.tools.credit.credit_query_tool import credit_query_tool
from app.multiAgent.tools.policy.policy_query_tool import policy_query_tool

# 导入状态定义
from app.multiAgent.common.uni_state import UniState, StateFields


class RouterDecision(BaseModel):
    """路由决策结构化输出"""

    should_call_tool: bool = Field(
        description="是否需要调用工具。如果需要查询数据或执行操作则为True，否则为False"
    )
    is_request_completed: bool = Field(
        description="请求是否已完成。如果工具已执行且结果已返回，则为True；如果还需要进一步操作，则为False"
    )
    reasoning: str = Field(description="决策理由，简要说明为什么做出这个判断")


class BlueGreenAccessAgent:
    """蓝绿准入评估Agent - 采用结构化决策模式"""

    def __init__(self, checkpointer=None):
        self.llm = get_llm()
        self.name = "blue_green_access_agent"
        self.checkpointer = checkpointer or InMemorySaver()

        # 工具列表 - 蓝绿准入团队内部统一编排征信、政策和准入评估
        self.tools = [
            credit_query_tool,
            policy_query_tool,
            access_query_tool_function,
        ]
        self.tool_node = ToolNode(
            self.tools, handle_tool_errors=False
        )  # 关键工具异常需冒泡，交由上层处理

        # 创建用于路由决策的 LLM（结构化输出）
        self.decision_llm = get_llm().with_structured_output(RouterDecision, method="json_mode")

        # 创建用于工具调用的 LLM
        self.tool_llm = get_llm().bind_tools(
            self.tools, tool_choice="auto", parallel_tool_calls=False
        )

        # 创建LangGraph图
        self.graph = self._build_access_graph()

    def _get_decision_system_prompt(self) -> str:
        """获取决策系统提示词 - 简洁的决策指导"""
        return """ 你是一个专业的蓝绿色金融准入评估路由助手。
你需要分析用户请求，通过了解使用场景和核心职责，根据以下规则做出决策：

## 使用场景
你专门处理对公金融项目的准入评估任务，包括：
- 绿色或蓝色项目准入条件判断
- 基于政策和准入工具做出合规性检查
- 绿色或蓝色项目准入政策标准评估
- 基于政策和信用做出项目是否符合对公金融标准的综合判断
- 对公金融项目准入评估和产品推荐
- 项目融资方案评估和优惠政策查询

## 核心职责
- 分析用户请求，判断是否需要调用工具进行准入评估
- 根据请求类型决定是否进入工具调用阶段或总结阶段
- 确保准入评估流程的完整性和准确性
- 识别包含具体项目名称的请求，并调用准入工具进行评估

## 工具调用决策流程

**标准执行流程**：
1. 先查询政策库确定项目的蓝绿色类型
2. 根据政策查询结果调用相应的准入工具
3. 如果项目既是蓝色也是绿色，需要调用两种类型的准入工具

**should_call_tool 判断规则**：
- 请求中包含具体项目名称（如"湿地修复项目"、"光伏项目"等） → True（先调用政策查询工具确定项目类型）
- 需要查询对公金融政策 → True（调用政策查询工具）
- 需要进行准入评估判断 → True（调用准入条件查询工具）
- 需要推荐对公金融产品或查询优惠政策 → True（调用政策查询工具获取相关信息）
- 已有完整信息，不需要进一步查询 → False（直接总结）

## 请求完成状态判断

**is_request_completed 判断规则**：
- 所有必要信息已获取，可以给出明确结论 → True（请求完成）
- 还需要更多信息或工具查询 → False（请求未完成）
- 政策查询后需要进一步准入判断 → False（还需要调用准入工具）
- 准入工具执行后且结果正常 → 根据是否还需要其他工具决定

## 输出要求

你必须输出结构化的决策结果，包含：
1. should_call_tool: True 或 False
2. is_request_completed: True 或 False
3. reasoning: 简要说明你的判断依据

## 决策示例

**示例1 - 需要先查询政策确定项目类型**：
用户："青岛国信发展(集团)有限责任公司的湿地修复项目，推荐最合适的产品，并列出相关优惠政策"
决策：should_call_tool=True, is_request_completed=False
理由：请求包含具体项目名称"湿地修复项目"，需要先调用政策查询工具确定项目是蓝色还是绿色类型

**示例2 - 需要政策查询**：
用户："查询绿色金融相关政策"
决策：should_call_tool=True, is_request_completed=False
理由：需要调用政策查询工具获取政策信息

**示例3 - 直接总结**：
用户："刚才的查询结果如何？"
决策：should_call_tool=False, is_request_completed=True
理由：已有完整查询结果，可以直接总结

**示例4 - 需要准入判断**：
用户："这个项目是否符合绿色金融准入标准？"
决策：should_call_tool=True, is_request_completed=False
理由：需要调用准入工具进行项目准入判断

## JSON输出要求如下
输出必须是合法的 JSON 对象，包含以下三个字段：
- "should_call_tool": 布尔值（true 或 false）
- "is_request_completed": 布尔值（true 或 false）
- "reasoning": 字符串，简要说明判断依据

例如：
{
  "should_call_tool": true,
  "is_request_completed": false,
  "reasoning": "请求包含具体项目名称\"湿地修复项目\"，需要先调用政策查询工具确定项目类型"
}
"""

    def _get_tool_system_prompt(self) -> str:
        """获取工具调用系统提示词 - 完整的工具使用说明"""
        return """你是一个专业的蓝绿准入评估工具调用助手。

## 使用场景
你专门处理对公金融项目的准入评估工具调用任务，包括：
- 政策库查询：绿色金融、蓝色金融相关政策文件、准入标准查询
- 准入判断：项目是否符合蓝色或绿色金融标准的综合判断
- 合规性检查：项目合规性评估的工具支持
- 项目评估：基于项目名称进行蓝绿准入评估

## 核心职责
- 分析用户请求，准确调用适当的蓝绿准入评估工具
- 确保工具参数正确且完整
- 处理工具调用过程中的错误和异常情况
- 提供准确可靠的工具执行结果
- 特别关注包含具体项目名称的请求，调用准入工具进行评估

## 核心能力
- 政策查询能力：精准调用政策库查询工具，获取相关政策信息
- 准入判断能力：执行绿色准入判断或蓝色准入判断，提供完整的评估支持
- 参数处理能力：正确解析和传递工具参数，确保工具调用成功
- 项目识别能力：识别请求中的具体项目名称，并调用准入工具

## 可用工具

1. **policy_query_tool** - 政策库查询工具
   - 参数：query (必需) - 政策查询内容
   - 用途：查询绿色金融、蓝色金融相关政策文件、准入标准、政策解读等

2. **access_query_tool_function** - 客户准入判断查询工具
   - 参数：
     - project_name (必需) - 项目名称
     - purpose (可选) - 资金用途，默认为"项目融资"
     - access_type (可选) - 准入类型，'green'表示绿色准入，'blue'表示蓝色准入，默认为'green'
   - 用途：执行绿色准入判断或蓝色准入判断，提供完整的蓝绿准入判断支持
   - **特别说明**：对于绿色准入判断，该工具会返回详细的绿色认定信息，包括：
     - 项目基础信息（项目名称、资金用途、业务类型、标准类型）
     - 非项目辅助识别接口项目认定响应
     - 非项目辅助识别接口接口资金用途信息（资金用途提示ID、资金用途描述、绿色代码、资金用途说明）
     - 根据资金用途提示获取分类信息接口绿色认定结果（绿色认定结果、最终绿色代码、响应代码、响应消息）
     - 综合评估信息（评估时间、认定流程完整性）

## 工具调用规则

1. 仔细分析用户请求，确定需要调用哪个工具
2. 确保工具参数正确且完整
3. 对于政策查询，提供清晰具体的查询内容
4. 对于准入判断，提供准确的项目名称和资金用途
5. 如果请求中包含具体项目名称（如"湿地修复项目"、"光伏项目"等），优先调用准入工具进行项目评估
6. 如果工具调用失败，分析错误原因并尝试解决
7. 只调用上述已提供的工具，不要尝试使用其他工具
8. 每次只调用一个工具，除非明确需要并行调用多个工具

## 绿色认定信息输出要求

当调用绿色准入判断工具时，必须确保输出完整的绿色认定信息，包括：

1. **基础项目信息**：
   - 项目名称
   - 资金用途
   - 业务类型
   - 标准类型

2. **API接口调用结果**：
   - 项目绿色认定接口：项目绿色认定响应
   - 非项目辅助识别接口：资金用途提示ID、资金用途描述、绿色代码、资金用途说明
   - 根据资金用途提示获取分类信息接口：绿色认定结果、最终绿色代码、响应代码、响应消息

3. **综合评估信息**：
   - 评估时间
   - 认定流程完整性

4. **绿色认定结论**：
   - 明确给出"认定成功"或"认定失败"的结论
   - 提供详细的认定依据和过程说明

## 错误处理

如果工具调用失败，请：
1. 分析错误消息，确定是否是参数问题
2. 如果是参数缺失，检查并补充必要参数
3. 如果是工具内部错误，向用户报告错误并提供建议
4. 如果无法解决，向用户报告错误并提供建议

## 调用示例

**示例1 - xxxx项目的归属蓝色还是绿色，还是蓝绿色属于**：
用户："xxxx项目的归属蓝色还是绿色，还是蓝绿色属于"
工具调用：policy_query_tool(query="xxxx项目的归属蓝色还是绿色，还是蓝绿色属于")

**示例2 - 绿色产业条目**：
用户："绿色产业条目"
工具调用：policy_query_tool(query="绿色产业条目")

**示例3 - 绿色项目评估（必须输出完整绿色认定信息）**：
用户："xxxx公司的xxxx项目是否属于绿色金融项目吗？"
工具调用：access_query_tool_function(project_name="湿地修复项目", purpose="项目融资", access_type="green")
**输出要求**：必须包含完整的绿色认定信息，包括项目基础信息、各API接口调用结果、绿色认定结论等

**示例4 - 绿色政策查询**：
用户："查询绿色金融相关政策"
工具调用：policy_query_tool(query="绿色金融相关政策")

**示例5 - 蓝色项目评估**：
用户："xxxx公司的xxxx项目是否属于蓝色金融项目吗？"
工具调用：access_query_tool_function(project_name="xxxx项目", purpose="项目融资", access_type="blue")

**示例6 - 蓝色政策查询**：
用户："查询蓝色金融相关政策"
工具调用：policy_query_tool(query="蓝色金融相关政策")

请专注于工具调用，确保绿色认定判断时输出完整的绿色认定信息。
"""

    def _get_summary_prompt(self, context_xml: str) -> str:
        """获取总结提示词 - 生成带RAG引用的评估报告

        Args:
            context_xml: XML格式的RAG检索分段
        """
        return f"""你是蓝绿色金融准入评估报告生成助手。

## RAG引用规则（强制要求）
你将收到一组与该问题相关的检索分段，每个检索分段都以 XML 标签包围：
- `<context id='x' source_id='原始ID'>内容</context>`
- `id` 是连续的整数编号（1, 2, 3...），用于在报告中引用
- `source_id` 是原始知识库分段的ID，用于追溯来源

⚠️ **重要：每个包含事实信息的句子都必须引用RAG分段！**

**强制引用规则**：
1. **必须引用的情况**：
   - 所有政策条文引用
   - 所有行业标准引用
   - 所有数值数据（金额、比例、时间等）
   - 所有判断结论（准入/不准入）
   - 所有风险提示和建议
   - 所有具体案例分析

2. **引用格式**：
   - 使用 `id` 属性的编号引用上下文，格式为 [x]
   - 如果一个句子来自多个上下文，请最多列出三个适用的引用，例如 [1][3][5]
   - 引用必须放在句子末尾，使用标点符号后
   - **来源传输**：来源信息通过send_citation_info函数传输到前端，前端会显示对应的来源描述

3. **引用示例**：
   - "该项目符合绿色金融标准[1]" ✅
   - "根据政策要求，绿色项目需满足环境效益指标[2][3]" ✅
   - "该项目不符合准入条件" ❌（缺少引用）
   - "该项目不符合准入条件[4]" ✅

4. **强制要求说明**：
   - **角标格式**：只使用[数字]格式
   - **来源传输**：来源信息通过send_citation_info函数传输，格式为：key是角标（如[1]），值是来源描述（如{{来源：政策文档库}}）

5. **严禁**：
   - 给出与问题无关的任何信息
   - 重复引用同一个分段
   - 虚构或推测任何信息
   - 使用没有RAG支撑的结论

6. **禁止添加元数据信息**：
   - ❌ 报告生成时间
   - ❌ 报告来源说明
   - ❌ 系统信息或版本信息
   - ❌ 任何与评估内容无关的装饰性文字

## 检索分段
{context_xml}

## 特别说明：API接口返回信息输出要求
**重要：绿色准入工具已成功调用API接口时，必须单独展示API接口返回的具体信息！**

### API接口信息与RAG分段的区别：
- **RAG分段**：来自知识库的静态政策信息，需要引用编号[1][2][3]...
- **API接口返回信息**：来自实时工具调用的动态数据，**也需要使用角标格式**，使用[s1]格式引用

### API接口信息输出规则：
1. **项目绿色认定接口项目认定响应**：
   - 必须展示项目绿色认定响应结果
   - 包括项目基本信息认定情况

2. **非项目辅助识别接口资金用途信息**：
   - 必须展示资金用途提示ID
   - 必须展示资金用途描述
   - 必须展示绿色代码
   - 必须展示资金用途说明

3. **根据资金用途提示获取分类信息接口绿色认定结果**：
   - 必须展示绿色认定结果（认定成功/认定失败）
   - 必须展示最终绿色代码
   - 必须展示响应代码
   - 必须展示响应消息

## 报告结构（必须引用RAG分段）
请基于对话历史、上述检索分段和工具返回的API接口数据，生成结构化的蓝绿准入评估报告，包含以下部分：

**重要说明**：
- 仅包含上述6个核心部分的内容
- 不添加任何前言、后记或元数据信息
- 报告以风险提示部分结束，无其他内容

1. **行业分类比对**：
   - 企业所属行业与国标分类的对应关系[引用RAG]
   - 行业分类依据和标准[引用RAG]

2. **政策标准匹配**：
   - 贷款投向与《蓝色金融产业认定标准》、《绿色产业指导目录》的符合度[引用RAG]
   - 具体政策条款和标准要求[引用RAG]
   - 项目类型识别（蓝色/绿色/蓝绿）[引用RAG]

3. **API接口认定信息**（当绿色准入工具已调用时）：
   - **非项目辅助识别接口项目认定响应**：[具体响应内容]
   - **非项目辅助识别接口资金用途信息**：[资金用途提示ID、资金用途描述、绿色代码、资金用途说明]
   - **根据资金用途提示获取分类信息接口绿色认定结果**：[绿色认定结果、最终绿色代码、响应代码、响应消息]
   - **说明**：以上信息来自实时API接口调用，使用[s1]角标格式

4. **环境风险排查**：
   - 近3年重大环保违规记录检查结果[引用RAG]
   - 50万元以上处罚触发否决的政策依据[引用RAG]
   - 环保合规性评估[引用RAG]

5. **准入决策判断**（必须明确）：
   - **明确的准入结论**：必须使用"准予准入"或"不予准入"的明确表述[引用RAG]
   - **具体政策依据**：引用支持该结论的政策条款和法规[引用RAG]
   - **API接口依据**：基于API接口返回的绿色认定结果进行判断
   - **准入条件分析**：逐条分析各项准入条件的满足情况[引用RAG]
   - **结论支撑**：确保每个准入结论都有充分的RAG政策依据和API接口数据支撑

6. **风险提示**：
   - 潜在风险点和改进建议[引用RAG]
   - 监管要求和后续跟踪要点[引用RAG]

## 输出要求（严格执行）
⚠️ **如果有RAG分段可用，以下要求必须严格执行**：

1. **强制引用**：
   - 每个包含事实信息的句子都必须引用RAG分段
   - 所有判断结论、政策依据、数据信息都必须有引用支撑
   - 严禁出现没有引用的事实性陈述

2. **API接口信息输出**：
   - 当工具已调用API接口时，必须输出具体的API接口返回信息
   - API接口信息需要使用[s1]角标格式引用
   - 确保非项目辅助识别、非项目辅助识别、根据资金用途提示获取分类信息接口的返回数据都得到展示

3. **禁止行为**：
   - ❌ 编造或推测任何信息
   - ❌ 使用"根据常识"、"一般来说"等非RAG支撑的表述
   - ❌ 给出没有引用的准入判断
   - ❌ 提供没有政策依据的建议
   - ❌ **隐藏或忽略API接口返回的重要信息**
   - ❌ **使用模糊的准入结论**（如"可能符合"、"倾向于"、"建议"等）
   - ❌ **避免明确判断**（如"需要进一步评估"、"暂无法确定"等）
   - ❌ **给出模棱两可的建议**（如"可以考虑"、"可能需要"等）

4. **格式要求**：
   - 引用格式：[数字编号]
   - 引用位置：句子末尾，标点符号之后
   - 引用数量：每个事实性句子至少1个引用

5. **准入判断要求（必须遵守）**：
   - **必须使用明确的二选一结论**：
     - "准予准入" ✅
     - "不予准入" ✅
     - "符合准入标准" ✅
     - "不符合准入标准" ✅

   - **禁止使用的模糊表述**：
     - "可能符合" ❌
     - "倾向于" ❌
     - "建议" ❌
     - "需要进一步评估" ❌
     - "暂无法确定" ❌
     - "可以考虑" ❌
     - "有待确认" ❌

   - **判断依据**：
     - 每个准入判断都必须基于RAG分段中的政策条款
     - 必须考虑API接口返回的绿色认定结果
     - 必须逐条分析准入条件的满足情况
     - 缺乏充分信息时，基于已有信息做出最佳判断，并明确说明依据

6. **质量检查**：
   - 在生成报告前，检查每个句子是否都有引用
   - 确保所有引用都来自提供的RAG分段
   - 确保报告中的每个结论都有政策或数据支撑
   - **特别检查**：确保准入结论使用了明确的"准予准入"或"不予准入"表述
   - **特别检查**：当工具已调用API接口时，确保API接口返回信息得到完整展示

7. **报告纯净性要求**：
   - 报告应直接从"行业分类比对"开始
   - 报告应在"风险提示"部分结束
   - 不包含任何形式的元数据、时间戳或来源说明
   - 专注于评估内容本身，避免任何装饰性或说明性文字

如果确实没有相关的RAG分段，请在报告开头明确说明："⚠️ 注意：当前缺乏相关RAG分段支撑，以下报告基于有限信息生成"。
"""

    def _build_access_graph(self):
        """构建准入评估LangGraph图结构 - 结构化决策模式

        流程：START → decision → router → 条件路由
                                         ↓
                                  ┌──────┴───────┐
                                  │              │
                               tools          summary
                                  │              │
                                  └──→ decision  END
        """
        logger.info("构建准入评估LangGraph图结构 - 结构化决策模式")

        # 构建图
        builder = StateGraph(UniState)

        # 添加节点
        builder.add_node("decision", self._decision_node)
        builder.add_node("router", self._router_node)
        builder.add_node("tool_node", self.tool_node)
        builder.add_node("summary", self._summary_node)

        # 设置执行流程：START → decision
        builder.add_edge(START, "decision")

        # decision → router
        builder.add_edge("decision", "router")

        # router 的条件路由
        builder.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "tools": "tool_node",
                "summary": "summary",
                "end": END,
            },
        )

        # 工具执行后回到决策节点
        builder.add_edge("tool_node", "decision")

        # 总结后结束
        builder.add_edge("summary", END)

        # 编译图
        return builder.compile(checkpointer=self.checkpointer)

    def _decision_node(self, state: UniState) -> Dict[str, Any]:
        """决策节点 - 使用结构化输出分析请求

        Args:
            state: 当前状态

        Returns:
            dict: 更新后的状态，包含决策结果
        """
        try:
            messages = state.get(StateFields.MESSAGES, [])
            messages_with_prompt = [
                SystemMessage(content=self._get_decision_system_prompt())
            ] + messages

            # 获取结构化决策
            logger.info(f"[blue_green_access_agent _decision_node] 获取结构化决策 LLM Start")
            decision: RouterDecision = self.decision_llm.invoke(messages_with_prompt)
            logger.info(f"[blue_green_access_agent _decision_node] 获取结构化决策 LLM End,{decision}")

            logger.info(
                f"[{self.name}] 决策结果: "
                f"should_call_tool={decision.should_call_tool}, "
                f"is_request_completed={decision.is_request_completed}, "
                f"reasoning={decision.reasoning}"
            )

            # 将决策存储到状态中（使用临时字段）
            return {StateFields.ROUTING_DECISION: decision}

        except Exception as e:
            logger.exception(f"[{self.name}] 决策节点失败")
            # 返回安全的默认决策
            default_decision = RouterDecision(
                should_call_tool=False,
                is_request_completed=False,
                reasoning=f"决策失败: {str(e)}",
            )
            return {StateFields.ROUTING_DECISION: default_decision}

    def _router_node(self, state: UniState, config: RunnableConfig) -> Dict[str, Any]:
        """Router 节点 - 根据决策调用工具

        Args:
            state: 当前状态
            config: 运行配置

        Returns:
            dict: 更新后的状态
        """
        try:
            messages = state.get(StateFields.MESSAGES, [])
            decision = state.get(StateFields.ROUTING_DECISION)

            if not decision:
                error_msg = "❌ 缺少路由决策"
                logger.error(f"[{self.name}] {error_msg}")
                return {StateFields.MESSAGES: [AIMessage(content=error_msg)]}

            # 如果决策是调用工具，使用 tool_llm
            if decision.should_call_tool:
                # 使用工具调用系统提示词
                messages_with_tool_prompt = [
                    SystemMessage(content=self._get_tool_system_prompt())
                ] + messages
                logger.info(f"[blue_green_access_agent tool_llm] 执行工具 LLM Start")
                response = self.tool_llm.invoke(messages_with_tool_prompt, config)
                logger.info(f"[blue_green_access_agent tool_llm] 执行工具 LLM End")

                logger.info(
                    f"[{self.name}] Router 调用工具: "
                    f"{[tc.get('name') for tc in response.tool_calls] if hasattr(response, 'tool_calls') and response.tool_calls else 'None'}"
                )

                return {StateFields.MESSAGES: [response]}
            else:
                # 如果不需要调用工具，直接返回（由条件路由决定下一步）
                return {}

        except Exception as e:
            logger.exception(f"[{self.name}] Router 节点失败")
            error_msg = f"❌ 处理请求失败: {str(e)}"
            return {StateFields.MESSAGES: [AIMessage(content=error_msg)]}

    def _summary_node(self, state: UniState, config: RunnableConfig) -> Dict[str, Any]:
        """总结节点 - 生成带RAG引用的准入评估报告

        Args:
            state: 当前状态
            config: 运行配置

        Returns:
            dict: 包含总结消息的状态更新
        """
        try:
            messages = state.get(StateFields.MESSAGES, [])

            # 1. 获取 rag_history（新结构）
            rag_history = state.get(StateFields.RAG_HISTORY, {})
            all_segments = rag_history.get("all_segments", [])
            agent_mapping = rag_history.get("agent_mapping", {})

            # 2. 获取当前 agent 使用的 segment id 列表
            agent_segment_ids = agent_mapping.get(self.name, [])

            # 3. 直接拼接 formatted 字段生成 context_xml（无需重新编号）
            context_xml = ""
            has_rag_segments = False
            if agent_segment_ids:
                has_rag_segments = True
                # 根据 id 获取对应的 segment 并拼接 formatted 字段
                for segment_id in agent_segment_ids:
                    # 从 all_segments 中找到对应的 segment
                    segment = next(
                        (seg for seg in all_segments if seg.get("id") == segment_id),
                        None,
                    )
                    if segment and "formatted" in segment:
                        context_xml += segment["formatted"] + "\n"

                logger.info(
                    f"[{self.name}] 使用 {len(agent_segment_ids)} 个 RAG 分段生成报告"
                )
            else:
                logger.info(f"[{self.name}] 没有RAG分段，将生成不含引用的报告")
                context_xml = "<context>无相关政策检索分段</context>\n"

            # 4. 构建总结提示词
            summary_prompt = self._get_summary_prompt(context_xml)

            # 5. 调用 LLM 生成报告
            summary_messages = [SystemMessage(content=summary_prompt)] + messages
            logger.info(f"[blue_green_access_agent summary_messages] 调用 LLM 生成报告 LLM Start")
            summary_response = self.llm.invoke(summary_messages, config)
            logger.info(f"[blue_green_access_agent summary_messages] 调用 LLM 生成报告 LLM End")

            logger.info(
                f"[{self.name}] 生成准入评估报告完成, 报告内容: {summary_response.content}"
            )

            return {StateFields.MESSAGES: [summary_response]}

        except Exception as e:
            logger.exception(f"[{self.name}] 总结节点失败")
            error_msg = f"❌ 生成执行报告失败: {str(e)}"
            return {StateFields.MESSAGES: [AIMessage(content=error_msg)]}

    def _route_decision(self, state: UniState) -> Literal["tools", "summary", "end"]:
        """基于结构化决策和实际情况决定路由目标

        判断逻辑：
        1. 如果 LLM 调用了工具 → 路由到 tools
        2. 如果决策显示请求已完成 → 路由到 summary
        3. 否则 → 结束

        Args:
            state: 当前状态

        Returns:
            str: 路由目标（tools、summary 或 end）
        """
        messages = state.get(StateFields.MESSAGES, [])
        decision = state.get(StateFields.ROUTING_DECISION)
        last_message = messages[-1] if messages else None

        # 1. 如果有工具调用，执行工具
        if (
            last_message
            and hasattr(last_message, "tool_calls")
            and last_message.tool_calls
        ):
            logger.info(f"[{self.name}] 检测到工具调用，路由到工具节点")
            return "tools"

        # 2. 基于结构化决策判断是否完成
        if decision:
            if decision.is_request_completed:
                logger.info(f"[{self.name}] 请求已完成，路由到总结节点")
                return "summary"

        # 3. 否则结束
        logger.info(f"[{self.name}] 完成处理，结束")
        return "end"
