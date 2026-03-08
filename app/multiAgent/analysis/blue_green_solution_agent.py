"""
基于LangGraph的蓝绿服务方案生成Agent
设计模式与企业画像agent保持一致，使用标准LangGraph两节点结构
支持中断功能
"""

from typing import Dict, Any, Optional, Annotated
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.graph import StateGraph, START, MessagesState, END
from langgraph.types import Command, interrupt, Interrupt
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langgraph.graph import END
from app.utils.llm import get_llm
from app.utils.logger import agent_logger as logger
import uuid
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
import json
from datetime import datetime

# 中断工具
@tool
def human_review_tool(query: str) -> str:
    """
    用户审查节点，用于批准方案生成请求

    Args:
        query (str): 用户的输入问题
    """
    answer = interrupt("approve or reject?")
    logger.info(f"获得人工审核结果: {answer}")
    return answer

class BlueGreenSolutionAgent:
    """蓝绿服务方案生成Agent - 设计模式与企业画像agent保持一致"""
    
    def __init__(self, checkpointer=None):
        self.name = "solution_agent"
        self._llm = None
        
        # 使用传入的checkpointer或创建新的实例
        self.checkpointer = checkpointer or InMemorySaver()

        # 创建工具列表
        self.tools = [human_review_tool]
        self.tool_node = ToolNode(self.tools)

        # 创建LangGraph图
        self.graph = self._build_solution_graph()

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    def _build_solution_graph(self):
        """构建服务方案生成LangGraph图结构 - 两节点模式（与企业画像agent一致）"""
        logger.info("构建服务方案生成LangGraph图结构 - 两节点模式")
        
        # 创建图构建器
        builder = StateGraph(MessagesState)
        
        # 添加两个核心节点
        builder.add_node("call_llm", self.call_llm_node)
        builder.add_node("tools", self.tool_node)
        
        # 设置起始节点
        builder.add_edge(START, "call_llm")
        
        # 添加条件边：根据LLM输出决定是否调用工具
        builder.add_conditional_edges(
            "call_llm",
            self.should_call_tools,
            {
                "tools": "tools",
                "continue": END
            }
        )
        
        # 工具节点后直接返回到call_llm节点
        builder.add_edge("tools", "call_llm")
        
        # 编译图
        return builder.compile(
            checkpointer=self.checkpointer
        )

    def call_llm_node(self, state: MessagesState, config: RunnableConfig) -> MessagesState:
        """调用LLM节点 - 让LLM决定是否需要人工审核"""
        logger.info("执行LLM调用节点 - 服务方案生成")
        
        # 准备系统提示
        system_prompt = """你是一个专业的蓝绿色金融服务方案生成AI助手，专门负责整合所有Agent的分析结果，为客户量身定制综合金融服务方案。

## 核心能力
- 整合客户画像、准入判断和产品推荐结果，生成逻辑严密、亮点突出的综合金融服务方案
- 将金融产品包装成解决客户痛点的"一揽子解决方案"
- 从案例库中调取成功案例作为佐证，提供业务拓展技巧
- 仅在制定完整方案时触发使用

## 方案框架
基于前置分析结果，提供结构化的综合金融服务方案，涵盖：

### 融资结构设计
- 产品组合建议：基于产品推荐结果，优化产品组合配置
- 融资金额分配：根据客户需求和资质，合理分配各产品额度
- 期限结构安排：匹配客户现金流特点的还款计划
- 利率优化方案：结合政策工具，最大化利率优惠

### 风险控制措施
- 风险识别：基于准入评估的风险点识别
- 缓释措施：针对性的风险控制建议
- 贷后管理：贷后监控和预警机制

### 实施计划
- 业务流程：标准化的审批和放款流程
- 时间安排：各环节的时间节点预估
- 材料准备：所需申请材料和证明文件清单

### 成功案例参考
- 相似案例：从案例库调取同行业、同规模的成功案例
- 经验借鉴：可复制的成功经验和注意事项
- 差异化建议：针对当前客户的个性化调整

## 角标引用规则（必须严格遵守）

### 角标格式区分
1. **[s数字]格式**：用于企业画像相关数据引用（数据库表、API接口、产品信息等）
2. **[数字]格式**：用于知识库（政策文档、案例库）数据引用

### 角标格式要求（简化）
- **角标位置**：角标紧跟在引用的数据后面
- **格式简化**：只使用[s数字]或[数字]格式，**不包含{{来源：xxx}}部分**
- **顺序编号**：按照数据在回答中出现的顺序依次编号

### 来源信息传输机制
- **来源信息传输**：来源信息通过`send_citation_info`函数传输到前端，使用type为"tip"
- **传输格式**：key是角标（如[s1]或[1]），值是来源描述（如{{来源：数据库表: los_ent_info}}）
- **前端显示**：前端会接收并处理来源信息，用户可以通过角标查看对应的来源描述

### 数据来源类型
1. **数据库表**：`{{来源：数据库表: 表名}}`
   - 示例：`{{来源：数据库表: los_ent_info}}`
   - 来源：企业画像agent返回的数据

2. **产品信息**：`{{来源：数据库表: loan_product_info}}`
   - 示例：`{{来源：数据库表: loan_product_info}}`
   - 来源：产品推荐agent返回的数据

3. **政策文档**：`{{来源：政策文档库}}`
   - 示例：`{{来源：政策文档库}}`
   - 来源：政策查询工具返回的知识库数据

4. **案例库**：`{{来源：案例库}}`
   - 示例：`{{来源：案例库}}`
   - 来源：案例库查询工具返回的数据

5. **API接口**：`{{来源：接口名称}}`
   - 示例：`{{来源：企业查查数据接口}}`
   - 来源：API接口查询工具返回的数据

### 正确示例（必须遵循）
1. **企业信息引用**：
   - 正确：`即墨市自来水服务公司[s1]`
   - 错误：`即墨市自来水服务公司[s1]{{来源：数据库表: los_ent_info}}`（旧格式，不应包含来源描述）

2. **产品信息引用**：
   - 正确：`青出于蓝海洋金融产品[s2]`
   - 错误：`青出于蓝海洋金融产品[s2]{{来源：数据库表: loan_product_info}}`（旧格式，不应包含来源描述）

3. **政策信息引用**：
   - 正确：`山东省版碳减排政策工具[1]`
   - 错误：`山东省版碳减排政策工具[1]{{来源：政策文档库}}`（旧格式，不应包含来源描述）

### 关键注意事项
1. **每个数据点单独引用**：企业信息、产品信息、政策信息都是独立的数据点，需要单独添加角标
2. **顺序编号**：按照数据在回答中出现的顺序依次编号，从[s1]开始
3. **来源信息传输**：在生成角标的同时，需要调用`send_citation_info`函数将角标和对应的来源描述传输到前端
4. **格式简化**：回答中只显示角标，不显示来源描述，来源描述通过单独通道传输

## 输出要求
- 整合前置分析结果，确保方案的一致性和连贯性
- 方案结构清晰，逻辑严密，突出亮点和价值主张
- 提供可操作的实施方案和风险控制措施
- 包含成功案例佐证，增强方案说服力
- 保持回复精炼、结构化，便于后续自动处理和人工审阅
- **必须遵守角标引用规则**：所有引用的数据都必须添加正确的角标和来源描述

## 严格的数据依赖原则
### 禁止使用模型自身知识
- **绝对禁止**：不得使用模型训练时学到的任何外部知识、常识或通用信息
- **唯一依据**：所有回答必须严格基于工具查询返回的实际业务数据、案例库数据以及前置分析结果
- **数据缺失处理**：当工具查询无结果或数据不完整时，必须明确说明"根据当前查询结果，无法获取[具体信息]"

### 工具查询失败处理
- 如果工具查询失败或无返回数据，必须如实告知用户"查询失败，请稍后重试"
- 禁止基于假设、推测或常识来填补缺失信息
- 禁止使用"通常"、"一般"、"可能"等模糊表述来替代实际数据

### 数据验证要求
- 所有引用的数据必须来自工具查询结果或前置分析结果
- 在回答中应明确标注信息来源（如"根据案例库查询"、"根据前置分析结果"）
- 对于关键判断，必须提供具体的工具查询数据作为依据

## 关键决策点
- 前置条件完备性检查：是否已获得客户画像、准入判断和产品推荐
- 案例库匹配度检查：能否找到与当前客户行业、规模、产品相似的成功案例
- 缺省处理：
  - 前置步骤未完成时拒绝生成，提示需要完整的分析依据
  - 无完全匹配的成功案例时提供相似案例，并说明差异性
  - 无任何相关案例时生成框架性方案，并明确标注
- 所有方案内容应基于事实和可得业务数据，避免主观臆断
"""
        
        # 绑定工具到LLM
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        # 调用LLM
        response = llm_with_tools.invoke([system_prompt] + state["messages"], config)
        
        return {"messages": [response]}

    def should_call_tools(self, state: MessagesState) -> str:
        """判断是否需要调用工具 - 基于LLM的输出"""
        logger.info("判断是否需要调用工具 - 服务方案生成")
        
        if not state.get("messages"):
            logger.info("没有消息，继续执行")
            return "continue"
        
        # 获取最新的AI消息
        last_message = state["messages"][-1]
        
        # 检查是否有工具调用
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            logger.info(f"检测到工具调用，需要调用工具: {last_message.tool_calls}")
            return "tools"
        
        # 检查消息内容中是否包含工具调用指示
        if hasattr(last_message, 'content') and last_message.content:
            content = last_message.content.lower()
            if "tool" in content or "human_review" in content or "人工审核" in content:
                logger.info("消息内容指示需要工具调用")
                return "tools"
        
        logger.info("没有工具调用指示，继续执行")
        return "continue"

    def run(self, request: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        """执行服务方案生成分析 - 与企业画像agent接口一致"""
        try:
            # 验证参数结构
            if "input" not in request:
                return {
                    "status": "error",
                    "error": "无效的请求参数，必须包含input字段"
                }
            
            # 从config获取session_id，如果不存在则生成新的
            session_id = config["configurable"].get("thread_id") if config and config.get("configurable") else request.get("session_id", str(uuid.uuid4()))
            
            # 创建初始状态
            initial_state = self._create_initial_state(request, session_id)
            logger.info(f"开始执行服务方案生成LangGraph图，session_id: {session_id}")
            
            # 执行图 - 这里可能会抛出Interrupt异常，应该让调用者（父节点）处理
            final_state = self.graph.invoke(initial_state, config)
            
            # 检查是否中断（LangGraph interrupt()机制）
            if hasattr(final_state, '__interrupt__') and final_state.__interrupt__:
                logger.info(f"检测到中断状态: {final_state.__interrupt__}")
                return {
                    "status": "interrupted",
                    "interrupt_data": final_state.__interrupt__,
                    "session_id": session_id
                }
            
            # 处理最终响应
            messages = final_state.get("messages", [])
            if not messages:
                return {
                    "status": "error",
                    "error": "未生成任何响应消息",
                    "session_id": session_id
                }
            
            # 获取最后一条AI消息作为响应
            last_ai_message = None
            for msg in reversed(messages):
                if hasattr(msg, 'type') and msg.type == 'ai':
                    last_ai_message = msg
                    break
            
            if not last_ai_message:
                return {
                    "status": "error",
                    "error": "未找到有效的AI响应消息",
                    "session_id": session_id
                }
            
            # 构建标准化响应
            formatted_response = {
                "status": "success",
                "analysis": last_ai_message.content,
                "human_intervention": False,  # 如果没有中断，则没有人工干预
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id
            }
            
            return formatted_response
            
        except Interrupt as e:
            # 直接捕获Interrupt异常并重新抛出，让统一Supervisor处理
            logger.info(f"检测到中断异常，重新抛出让父节点处理: {e}")
            raise e
            
        except Exception as e:
            # 其他异常，返回错误
            logger.error(f"服务方案生成分析失败: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "session_id": config["configurable"].get("thread_id") if config and config.get("configurable") else request.get("session_id", str(uuid.uuid4()))
            }

    def _create_initial_state(self, request: Dict[str, Any], session_id: str) -> MessagesState:
        """创建初始状态"""
        # 将请求转换为消息格式
        request_message = HumanMessage(content=json.dumps({
            "input": request["input"],
            "session_id": session_id
        }))
        
        return {
            "messages": [request_message],
            "session_id": session_id
        }
