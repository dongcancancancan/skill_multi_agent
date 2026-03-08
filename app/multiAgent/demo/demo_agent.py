from typing import Annotated, Dict, Any
from langchain_core.messages import convert_to_messages
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.types import Command, interrupt
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.types import RunnableConfig
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langgraph.graph import END
from langgraph_supervisor import create_supervisor
import os
import uuid
from langgraph.checkpoint.memory import InMemorySaver

# 创建内存检查点器
checkpointer = InMemorySaver()

# LLM配置
llm = ChatOpenAI(
    temperature=0.6,
    model="deepseek-r1:32b",
    openai_api_key="sk-058d38c3d7d24749b7325",
    openai_api_base="http://10.1.84.77/v1-openai/",
)

os.environ["TAVILY_API_KEY"] = "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"
from langchain_tavily import TavilySearch

web_search = TavilySearch(max_results=3)

def create_handoff_tool(*, agent_name: str, description: str | None = None):
    name = f"transfer_to_{agent_name}"
    description = description or f"Ask {agent_name} for help."

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        tool_message = {
            "role": "tool",
            "content": f"Successfully transferred to {agent_name}",
            "name": name,
            "tool_call_id": tool_call_id,
        }
        return Command(
            goto=agent_name,
            update={**state, "messages": state["messages"] + [tool_message]},
            graph=Command.PARENT,
        )

    return handoff_tool

@tool
def add(a: float, b: float):
    """两个数字相加"""
    return a + b

@tool
def multiply(a: float, b: float):
    """两个数字相乘"""
    return a * b

@tool
def divide(a: float, b: float):
    """两个数字相除"""
    return a / b

@tool
def human_node(query: str) -> str:
    """
    用户审查节点，用于批准用户问题是否可以执行数学运算

    Args:
        query (str): 用户的输入问题
    """
    answer = interrupt("approve or reject?")
    print(f"获得答案: {answer}")
    return answer

# 数学代理
llm2 = ChatOpenAI(
    temperature=0.6,
    model="deepseek-r1:32b",
    openai_api_key="sk-058d38c3d7d24749b7325",
    openai_api_base="http://10.1.84.77/v1-openai/",
).bind_tools([add, multiply, divide, human_node])
math_tools = [add, multiply, divide, human_node]
math_tool_node = ToolNode(math_tools)

def call_math_llm(
    state: MessagesState,
    config: RunnableConfig,
):
    system_prompt = SystemMessage(
        "You are a math agent.\n\n"
        "INSTRUCTIONS:\n"
        "- You need to approve the user's question first\n"
        "- Assist ONLY with math-related tasks\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    )
    response = llm2.invoke([system_prompt] + state["messages"], config)
    return {"messages": [response]}

math_agent = (
    StateGraph(MessagesState)
    .add_node("call_math_llm", call_math_llm)
    .add_node("tools", math_tool_node)
    .add_edge(START, "call_math_llm")
    .add_edge("tools", "call_math_llm")
    .add_conditional_edges("call_math_llm", tools_condition)
    .compile(checkpointer=checkpointer)
)

# 研究代理
@tool
def joke_generation(topic: str):
    """生成关于给定主题的笑话"""
    return f"Here is a joke about {topic}: hhhhhhhhhhhhhhhhhhhhh"

llm3 = ChatOpenAI(
    temperature=0.6,
    model="deepseek-r1:32b",
    openai_api_key="sk-058d38c3d7d24749b7325",
    openai_api_base="http://10.1.84.77/v1-openai/",
).bind_tools([web_search, joke_generation])
research_tools = [web_search, joke_generation]
research_tool_node = ToolNode(research_tools)

def call_research_llm(
    state: MessagesState,
    config: RunnableConfig,
):
    system_prompt = SystemMessage(
        (
            "You are a research agent.\n\n"
            "INSTRUCTIONS:\n"
            "- Assist ONLY with research-related or joke generation tasks, DO NOT do any math\n"
            "- After you're done with your tasks, respond to the supervisor directly\n"
            "- Respond ONLY with the results of your work, do NOT include ANY other text."
        )
    )
    response = llm3.invoke([system_prompt] + state["messages"], config)
    return {"messages": [response]}

research_agent = (
    StateGraph(MessagesState)
    .add_node("call_research_llm", call_research_llm)
    .add_node("tools", research_tool_node)
    .add_edge(START, "call_research_llm")
    .add_conditional_edges("call_research_llm", tools_condition)
    .add_edge("tools", "call_research_llm")
    .compile(checkpointer=checkpointer)
)

# 交接工具
assign_to_research_agent = create_handoff_tool(
    agent_name="research_agent",
    description="将任务分配给研究代理。",
)

assign_to_math_agent = create_handoff_tool(
    agent_name="math_agent",
    description="将任务分配给数学代理。",
)

# 监督器代理
supervisor_agent = create_react_agent(
    model=llm,
    tools=[assign_to_research_agent, assign_to_math_agent],
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- a research agent. Assign research-related or joke generation tasks to this agent\n"
        "- a math agent. Assign math-related tasks to this agent\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),
    name="supervisor",
    checkpointer=checkpointer,
)

# 监督器图
supervisor = (
    StateGraph(MessagesState)
    .add_node(supervisor_agent, destinations=("research_agent", "math_agent", END))
    .add_node("research_agent", research_agent)
    .add_node("math_agent", math_agent)
    .add_edge(START, "supervisor")
    .add_edge("research_agent", "supervisor")
    .add_edge("math_agent", "supervisor")
    .compile(checkpointer=checkpointer)
)

def execute_demo_supervisor(request: Dict[str, Any]):
    """执行demo监督器"""
    session_id = request.get("session_id", str(uuid.uuid4()))
    user_input = request.get("input", "")
    
    config = {
        "configurable": {
            "thread_id": session_id,
        }
    }
    
    print(f"--config : {config}")
    messages = [{"role": "user", "content": user_input}]
    
    try:
        result = supervisor.invoke(
            {"messages": messages},
            config=config,
        )
        
        # 检查结果中是否包含中断信息
        if hasattr(result, '__interrupt__') and result.__interrupt__:
            return {
                "session_id": session_id,
                "status": "interrupted",
                "message": "需要人工干预",
                "interruption_type": "human_approval",
                "interrupt_data": result.__interrupt__
            }
        
        return {
            "session_id": session_id,
            "result": result,
            "status": "completed"
        }
    except Exception as e:
        if "interrupt" in str(e).lower():
            return {
                "session_id": session_id,
                "status": "interrupted",
                "message": "需要人工干预",
                "interruption_type": "human_approval"
            }
        else:
            raise e

def restore_demo_session(session_id: str, human_feedback: str):
    """恢复demo会话"""
    config = {
        "configurable": {
            "thread_id": session_id,
        }
    }
    
    try:
        # 使用Command恢复执行
        result = supervisor.invoke(
            Command(resume=human_feedback),
            config=config,
        )
        
        return {
            "session_id": session_id,
            "result": result,
            "status": "completed"
        }
    except Exception as e:
        raise e
