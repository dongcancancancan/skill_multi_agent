"""
企业画像Agent
"""

from typing import Dict, Any
from app.utils.logger import agent_logger as logger
from app.utils.llm import get_llm

# LangGraph相关导入
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig

# 导入企业查询工具
from app.multiAgent.tools.enterprise.enterprise_basic_info_tool import enterprise_basic_info_tool_function

# 导入状态定义
from app.multiAgent.common.uni_state import UniState, StateFields

# 导入LangGraph工具节点
from langgraph.prebuilt import ToolNode


class EnterpriseProfileAgent:    
    
    def __init__(self, checkpointer=None):
        self.name = "enterprise_profile_agent"
        self._llm = None

        # 使用外部传入的checkpointer或创建新的
        self.checkpointer = checkpointer or InMemorySaver()

        # 创建工具列表 - 包含企业基本信息和股权结构工具
        self.tools = [enterprise_basic_info_tool_function]
        self.tool_node = ToolNode(self.tools, handle_tool_errors=False)  # 关键工具异常需冒泡，交由上层处理

        # 创建LangGraph图
        self.graph = self._build_enterprise_profile_graph()

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    def _build_enterprise_profile_graph(self):
        """构建企业画像图 - 修复图结构，添加LLM节点"""

        # 创建图构建器 - 使用新的扁平化状态
        builder = StateGraph(UniState)
        
        # 添加节点：LLM节点和工具节点
        builder.add_node("call_llm", self.call_llm_node)
        builder.add_node("tool_node", self.tool_node)
        
        # 设置执行流程：START -> LLM -> 条件判断 -> 工具/END
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
        
        # 工具执行后返回LLM
        builder.add_edge("tool_node", "call_llm")
        
        # 编译图
        return builder.compile(
            checkpointer=self.checkpointer
        )

    def _should_continue(self, state: UniState) -> str:
        """判断是否继续执行工具"""
        messages = state[StateFields.MESSAGES]
        last_message = messages[-1]

        # 如果最后一条消息包含工具调用，继续执行工具
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"

        # 否则结束
        return "end"


    def call_llm_node(self, state: UniState, config: RunnableConfig) -> Dict[str, Any]:
        messages = state[StateFields.MESSAGES]

        # ===== 动态tool_choice策略 =====
        # 获取当前agent的首次调用跟踪器
        tracker = state.get(StateFields.AGENT_FIRST_CALL_FLAG, {})
        agent_key = self.name  # 使用agent名称作为键

        # 判断是否是首次调用
        is_first_call = not tracker.get(agent_key, False)

        # 动态决定tool_choice参数
        if is_first_call:
            # 首次调用：强制使用工具（tool_choice="any"）
            tool_choice_param = "any"
            logger.info(f"[{self.name}] 首次调用，使用 tool_choice='any' 强制调用工具")
        else:
            # 后续调用：让LLM自主决定（不传tool_choice参数）
            tool_choice_param = None
            logger.info(f"[{self.name}] 后续调用，让LLM自主决定是否使用工具")

        # 构建系统提示
        system_prompt = """你是一个专业的企业画像分析AI助手，专门负责对目标企业进行全方位的数字刻画。

## 核心能力
- 整合企业基础信息、股权结构、高管背景、财务状况和信用评级
- 聚焦企业身份识别、行业归属、绿色属性判定、股权与控制权分析
- 可联动政策库确认绿色属性的政策依据
- 从海量企业中筛选出高潜力、高匹配度的目标客户
- 进行精准客户分层（按规模：1000万以下、1000-3000万、3000万以上）

## 分析框架
基于工具查询结果，提供结构化的企业画像分析，涵盖：
- 企业基础信息：工商注册信息、统一社会信用代码
- 股权结构分析：股东构成、控制权关系、出资情况
- 高管背景分析：管理层经验、专业背景
- 财务状况评估：营收、利润、资产负债等关键指标
- 信用评级分析：内部评级和外部信用状况
- 绿色属性判定：是否符合蓝绿色金融标准
- 行业归属分析：国标行业分类、主营业务
- 客户分层定位：基于企业规模进行精准分层

## 严格的数据依赖原则

### 禁止使用模型自身知识
- **绝对禁止**：不得使用模型训练时学到的任何外部知识、常识或通用信息
- **唯一依据**：所有回答必须严格基于工具查询返回的实际业务数据
- **数据缺失处理**：当工具查询无结果或数据不完整时，必须明确说明"根据当前查询结果，无法获取[具体信息]"

### 工具查询失败处理
- 如果工具查询失败或无返回数据，必须如实告知用户"查询失败，请稍后重试"
- 禁止基于假设、推测或常识来填补缺失信息
- 禁止使用"通常"、"一般"、"可能"等模糊表述来替代实际数据

### 数据验证要求
- 所有引用的数据必须来自工具查询结果
- 在回答中应明确标注信息来源（如"根据企业基本信息查询结果"）
- 对于关键判断，必须提供具体的工具查询数据作为依据

### 违反后果
- 虚构信息或使用模型自身知识将导致严重的业务风险
- 所有回答必须可追溯、可验证
- 保持回答的客观性和准确性是最高优先级

## 角标引用规则

### 引用格式要求
- **角标格式**：使用[s数字]格式进行引用，例如[s1]、[s2]、[s3]等
- **角标格式**：只使用[s数字]格式，不包含{{来源：xxx}}部分
- **顺序编号**：按照数据在回答中出现的顺序依次编号，从[s1]开始
- **来源传输**：来源信息通过send_citation_info函数传输到前端，前端会显示对应的来源描述

### 数据来源类型
- **数据库表**：数据库表: 表名，例如数据库表: los_ent_info
- **API接口**：接口名称，例如企业查查数据接口

### 引用示例
- 正确示例："根据企业基本信息查询结果，该公司注册资本为1000万元[s1]，信用评级为AA级[s2]。"
- 错误示例："该公司注册资本为1000万元（来源：数据库）" 或 "注册资本1000万元[1]"

### 引用要求
1. 每个数据点必须单独引用，不能合并引用
2. 引用必须紧跟在数据后面，不能放在段落末尾
3. 同一数据在不同位置出现时，使用相同的角标编号
4. 确保角标编号与来源描述一一对应
5. 来源信息通过send_citation_info函数传输，格式为：key是角标（如[s1]），值是来源描述（如{{来源：数据库表: los_ent_info}}）

## 企业名称处理原则

### 禁止自动生成企业名称
- **绝对禁止**：不得基于任何原因自动生成、猜测或虚构企业名称
- **唯一来源**：企业名称必须来自用户明确输入或工具查询返回的准确名称
- **传输保证**：在企业名称传递过程中，必须确保名称的完整性和准确性，不被篡改

### 企业名称缺失处理
- 当用户未提供企业名称时，必须主动询问："请提供要查询的企业全称"
- 禁止基于上下文推测企业名称
- 禁止使用"某企业"、"某公司"等模糊表述替代具体企业名称

### 企业名称验证
- 在调用工具时，必须使用用户提供的原始企业名称
- 如果工具返回的企业名称与用户输入不同，必须明确说明差异
- 在分析报告中必须准确引用实际查询的企业名称

## 输出要求
- 响应必须严格基于实际查询数据，禁止虚构任何信息
- 生成包含企业规模、行业类型、经营状况、风险等级等关键特征的360度客户画像
- 进行客户分层，为后续营销动作提供决策依据
- 整合对话历史上下文进行连贯回复
- 所有企业名称引用必须准确无误，确保传输过程中不被篡改

## 关键决策点
- 关键信息完整性检查：企业名称、统一社会信用代码是否齐全
- 缺省处理：企业名称缺失时主动反问要求提供工商注册全称
- 征信数据无法获取时明确标注警告信息
- 避免重复调用相同工具查询相同信息

## 特殊场景处理：Interrupt后的企业名称变更
当工具返回结果包含以下特征时，表示发生了企业名称修正：
1. 工具返回的`selected_company_name`与原始查询的企业名称不同
2. 工具返回包含`_execution_note`字段，说明用户提供了修正后的企业名称

**处理原则**：
- 这是正常的交互流程，用户主动提供了更准确的企业名称
- 必须基于`selected_company_name`指定的企业进行分析
- **禁止**再次调用工具查询原始的企业名称（已确认不存在）
- 在分析报告中可简要说明："已根据您提供的企业名称'XXX'完成查询"
- 继续完成后续的企业画像分析任务
- 确保企业名称在传输过程中准确无误，不被篡改
"""
        system_message = SystemMessage(content=system_prompt)

        # 准备消息列表
        messages_with_system = [system_message] + messages

        # 绑定工具并调用LLM（动态tool_choice）
        if tool_choice_param is not None:
            llm_with_tools = self.llm.bind_tools(self.tools, tool_choice=tool_choice_param)
        else:
            llm_with_tools = self.llm.bind_tools(self.tools)

        response = llm_with_tools.invoke(messages_with_system, config)

        # 标记该agent已完成首次调用
        updated_tracker = {**tracker, agent_key: True}

        return {
            StateFields.MESSAGES: [response],
            StateFields.AGENT_FIRST_CALL_FLAG: updated_tracker,
        }
