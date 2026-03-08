"""
ToolBox Agent - 简单工具集合的 React Agent

设计目标：
- 支持多轮工具调用（ReAct 循环）
- 自动判断是否需要继续查询
- 整合多个查询结果生成综合回复

参考实现：enterprise_profile_agent.py
"""

from typing import Dict, Any
from app.utils.logger import agent_logger as logger
from app.utils.llm import get_llm

# LangGraph相关导入
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig

# 导入简单工具
from app.multiAgent.tools.enterprise.enterprise_basic_info_tool import enterprise_basic_info_tool_function
from app.multiAgent.tools.policy.policy_query_tool import policy_query_tool
from app.multiAgent.tools.case import case_query_tool
from app.multiAgent.tools.product.product_query_tool import product_query_tool
from app.multiAgent.tools.product.product_policy_query_tool import product_policy_query_tool
from app.multiAgent.tools.customer_manager.customer_manager_profile_tool import call_customer_manager_info_tool
from app.multiAgent.tools.industry.industry_query_tool import industry_query_tool
from app.multiAgent.tools.counterparty.counterparty_query_tool import counterparty_query_tool
from app.multiAgent.tools.credit.credit_query_tool import credit_query_tool
from app.multiAgent.tools.supply_chain import supply_chain_query_tool
from app.multiAgent.tools.blue_green_access.access_query_tool import access_query_tool_function

# 导入状态定义
from app.multiAgent.common.uni_state import UniState, StateFields

# 导入LangGraph工具节点
from langgraph.prebuilt import ToolNode


class ToolBoxAgent:
    """简单工具集合的 React Agent"""

    # 最大循环次数限制（防止死循环）
    MAX_ITERATIONS = 10

    def __init__(self, checkpointer=None):
        self.name = "toolbox_agent"
        self._llm = None

        # 使用外部传入的checkpointer或创建新的
        self.checkpointer = checkpointer or InMemorySaver()

        # 创建工具列表 - 11个简单查询工具
        self.tools = [
            enterprise_basic_info_tool_function,    # 企业基本信息
            policy_query_tool,                       # 政策查询
            # case_query_tool,                         # 案例查询
            product_query_tool,                      # 产品查询
            product_policy_query_tool,               # 产品政策查询
            # call_customer_manager_info_tool,         # 客户经理信息
            # industry_query_tool,                     # 行业查询
            # counterparty_query_tool,                 # 交易对手查询
            # credit_query_tool,                       # 征信查询
            # supply_chain_query_tool,                 # 供应链查询
            access_query_tool_function,              # 准入条件查询
        ]
        self.tool_node = ToolNode(self.tools, handle_tool_errors=False)

        # 创建LangGraph图
        self.graph = self._build_graph()

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm(disable_streaming=False)
        return self._llm

    def _build_graph(self):
        """构建 React 图：START → call_llm → [条件边] → tool_node/END"""

        # 创建图构建器
        builder = StateGraph(UniState)

        # 添加节点：LLM节点和工具节点
        builder.add_node("call_llm", self.call_llm_node)
        builder.add_node("tool_node", self.tool_node)

        # 设置执行流程：START → LLM → 条件判断 → 工具/END
        builder.add_edge(START, "call_llm")

        # 条件边：根据LLM响应决定下一步
        builder.add_conditional_edges(
            "call_llm",
            self._should_continue,
            {
                "continue": "tool_node",
                "end": END
            }
        )

        # 工具执行后返回LLM（React循环）
        builder.add_edge("tool_node", "call_llm")

        # 编译图
        return builder.compile(checkpointer=self.checkpointer)

    def _should_continue(self, state: UniState) -> str:
        """判断是否继续执行工具（包含循环次数保护和空结果检测）"""
        messages = state[StateFields.MESSAGES]
        last_message = messages[-1]

        # 防护：检查循环次数
        tool_call_count = sum(
            1 for msg in messages
            if hasattr(msg, 'tool_calls') and getattr(msg, 'tool_calls', None)
        )

        if tool_call_count >= self.MAX_ITERATIONS:
            logger.warning(f"[ToolBox] 达到最大循环次数 {self.MAX_ITERATIONS}，强制结束")
            return "end"

        # 检查最近的工具调用是否返回空结果
        if tool_call_count > 0:
            # 查找最近的工具调用结果
            for i in range(len(messages) - 1, -1, -1):
                msg = messages[i]
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # 检查工具调用后的消息是否包含空结果提示
                    if i + 1 < len(messages):
                        next_msg = messages[i + 1]
                        if hasattr(next_msg, 'content'):
                            content = next_msg.content
                            # 检测空结果模式
                            if any(pattern in content.lower() for pattern in 
                                   ['没有找到', '未找到', '空结果', '0个结果', 'total_count: 0']):
                                logger.info(f"[ToolBox] 检测到空结果，停止循环")
                                return "end"

        # 如果最后一条消息包含工具调用，继续执行工具
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"

        # 否则结束
        return "end"

    def call_llm_node(self, state: UniState, config: RunnableConfig) -> Dict[str, Any]:
        """LLM 节点：决策调用哪些工具或生成最终回复"""
        messages = state[StateFields.MESSAGES]

        # 构建系统提示
        system_prompt = """你是一个智能工具调用助手，专门处理数据查询和信息检索任务。

## 核心能力
- 根据用户需求选择合适的工具进行数据查询
- 支持多次工具调用以获取完整信息
- 整合多个查询结果提供综合分析和回复

## 可用工具

1. **enterprise_basic_info_tool_function** - 企业基本信息查询
   - 企业工商信息（名称、注册号、法人、注册资本等）
   - 债券发行主体信用评级
   - 企查查身份识别、司法风险、经营异常、年报信息
   - 环保信用评价、行政处罚、股权冻结、失信详情

2. **policy_query_tool** - 政策文档查询
   - 对公金融政策、环保政策文档
   - 调用时必须传递 agent='toolbox_agent' 参数

3. **case_query_tool** - 案例库查询
   - 成功案例、项目参考

4. **product_query_tool** - 产品查询
   - 产品分类、产品详情、优惠政策

5. **product_policy_query_tool** - 产品政策查询
   - 产品政策工具、支持领域

6. **call_customer_manager_info_tool** - 客户经理信息查询
   - 客户经理联系方式、负责区域

7. **industry_query_tool** - 行业查询
   - 行业分类、行业属性

8. **counterparty_query_tool** - 交易对手查询
   - 交易对手风险评估

9. **credit_query_tool** - 征信查询
   - 企业征信、信用评级、违约概率

10. **supply_chain_query_tool** - 供应链查询
    - 供应链关系、业务联系

11. **access_query_tool_function** - 准入条件查询
    - 绿色准入判断、蓝色准入判断
    
## 执行策略

1. **分析需求**：仔细分析用户需求，确定需要哪些工具
2. **按需调用**：根据需求调用相应工具（可以多次）
3. **评估信息**：评估已获取信息是否充分回答用户问题
4. **补充查询**：如果信息不足，继续调用其他相关工具
5. **综合回复**：信息充分后，生成基于实际数据的综合回复

## 关键原则

- ✅ 避免重复调用相同工具查询相同信息
- ✅ 工具返回空结果时，说明可能不存在该信息，告知用户
- ✅ 最终回复基于实际查询数据，不虚构信息
- ✅ 对于对比类需求，确保查询所有对比对象
- ✅ 整合历史对话上下文，提供连贯回复

## 角标引用规则

### 角标格式区分
系统使用两种不同的角标格式来区分数据来源类型：

1. **[s数字]格式**：用于企业画像相关数据引用
   - 企业基本信息、债券评级、API接口查询结果等
   - 示例：[s1]、[s2]、[s3]

2. **[数字]格式**：用于知识库（政策文档）数据引用
   - 政策查询、案例库等知识库检索结果
   - 示例：[1]、[2]、[3]

### 引用格式要求
- **角标位置**：角标紧跟在引用的数据后面
- **角标格式**：只使用[s数字]或[数字]格式，不包含{{来源：xxx}}部分
- **顺序编号**：按照数据在回答中出现的顺序依次编号，企业数据从[s1]开始，知识库数据从[1]开始
- **来源传输**：来源信息通过send_citation_info函数传输到前端，前端会显示对应的来源描述

### 数据来源类型
- **数据库表**：数据库表: 表名，例如数据库表: los_ent_info
- **API接口**：接口名称，例如企业查查数据接口
- **政策文档**：政策文档库，例如政策文档库
- **产品信息**：产品数据库，例如产品数据库
- **准入条件**：准入条件数据库，例如准入条件数据库

### 引用示例
- **企业信息示例**："根据企业基本信息查询结果，该公司注册资本为1000万元[s1]，信用评级为AA级[s2]。"
- **API接口示例**："根据企查查查询结果，该企业无司法风险记录[s3]。"
- **政策信息示例**："根据政策查询结果，该企业符合绿色金融支持政策[1]。"
- **产品信息示例**："根据产品查询结果，该企业可申请绿色信贷产品[s4]。"

### 引用要求
1. 每个数据点必须单独引用，不能合并引用
2. 引用必须紧跟在数据后面，不能放在段落末尾
3. 同一数据在不同位置出现时，使用相同的角标编号
4. 确保角标编号与来源描述一一对应
5. 企业查询工具返回的数据已包含_source字段，请根据该字段确定具体来源
6. 政策查询工具返回的是知识库数据，使用[数字]格式角标
7. 来源信息通过send_citation_info函数传输，格式为：key是角标（如[s1]或[1]），值是来源描述（如{{来源：数据库表: loan_product_info}}）

## 输出要求

- 响应专业、准确、简洁
- 突出关键信息和重点发现
- 提供有价值的分析和建议
- 在生成列表时，每个新的大类或章节下的子点必须从1开始重新编号，确保层级清晰
- **必须遵守角标引用规则**，所有引用数据都要标注来源
"""
        system_message = SystemMessage(content=system_prompt)

        # 准备消息列表
        messages_with_system = [system_message] + messages

        # 绑定工具并调用LLM
        llm_with_tools = self.llm.bind_tools(self.tools)
        response = llm_with_tools.invoke(messages_with_system, config)

        # 如果即将结束（没有 tool_calls），发送完整 RAG 溯源信息到前端
        if not (hasattr(response, 'tool_calls') and response.tool_calls):
            try:
                from langgraph.config import get_stream_writer
                from app.multiAgent.tools.rag_history_formatter import (
                    format_rag_history_to_knowledge_base,
                )

                rag_history = state.get(StateFields.RAG_HISTORY)
                if rag_history:
                    knowledge_base_data = format_rag_history_to_knowledge_base(
                        rag_history
                    )
                    if knowledge_base_data:
                        stream_writer = get_stream_writer()
                        if stream_writer:
                            # 直接发送转换后的数据
                            stream_writer(knowledge_base_data)
                            logger.info("[ToolBox] 已发送完整 RAG 溯源信息到前端")
            except Exception as e:
                logger.warning(f"[ToolBox] RAG 溯源发送失败，但不影响主流程: {e}")

        # 防御性处理：确保响应对象可以被正确处理
        # 如果是流式响应对象，需要特殊处理
        if hasattr(response, 'model_dump'):
            # 标准 Pydantic 模型对象
            processed_response = response
        else:
            # 流式响应或其他类型对象，直接使用
            processed_response = response

        return {StateFields.MESSAGES: [processed_response]}
