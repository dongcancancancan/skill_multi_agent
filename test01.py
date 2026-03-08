from typing import Annotated
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

# 使用 `pretty_print_messages` 辅助函数来美化流式代理输出的显示 

llm = ChatOpenAI(
    temperature=0.6,
    model="deepseek-r1:32b",
    openai_api_key="sk-058d38c3d7d24749b7325",
    openai_api_base="http://10.1.84.77/v1-openai/",
)
checkpointer = InMemorySaver()
os.environ["TAVILY_API_KEY"] = "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"
from langchain_tavily import TavilySearch

web_search = TavilySearch(max_results=3)


def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return

    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    print(indented)


def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        # 跳过父图的更新显示
        if len(ns) == 0:
            return

        graph_id = ns[-1].split(":")[0]
        print(f"来自子图 {graph_id} 的更新:")
        print("\n")
        is_subgraph = True

    for node_name, node_update in update.items():
        update_label = f"来自节点 {node_name} 的更新:"
        if is_subgraph:
            update_label = "\t" + update_label

        print(update_label)
        print("\n")

        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]

        for m in messages:
            pretty_print_message(m, indent=is_subgraph)
        print("\n")


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


# # 简单的代理工具
# @tool
# def web_search(query: str):
#     """搜索网络信息"""
#     return f"Successfully searched the web for {query}."


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


# 定义代理
# flight_assistant = create_react_agent(
#     model="anthropic:claude-3-5-sonnet-latest",
#     tools=[book_flight, transfer_to_hotel_assistant],
#     prompt="You are a flight booking assistant",
#     name="flight_assistant",
# )

llm2 = ChatOpenAI(
    temperature=0.6,
    model="deepseek-r1:32b",
    openai_api_key="sk-058d38c3d7d24749b7325",
    openai_api_base="http://10.1.84.77/v1-openai/",
).bind_tools([add, multiply, divide, human_node])
tools = [add, multiply, divide, human_node]
tool_node = ToolNode(tools)


# 定义调用模型的节点
def call_math_llm(
    state: MessagesState,
    config: RunnableConfig,
):
    # 这类似于使用 'prompt' 参数自定义 create_react_agent，但更灵活
    system_prompt = SystemMessage(
        "You are a math agent.\n\n"
        "INSTRUCTIONS:\n"
        "- You need to approve the user's question first\n"
        "- Assist ONLY with math-related tasks\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    )
    response = llm2.invoke([system_prompt] + state["messages"], config)
    # 我们返回一个列表，因为它将被添加到现有列表中
    return {"messages": [response]}


math_agent = (
    StateGraph(MessagesState)
    .add_node("call_math_llm", call_math_llm)
    .add_node("tools", tool_node)
    .add_edge(START, "call_math_llm")
    .add_edge("tools", "call_math_llm")
    .add_conditional_edges("call_math_llm", tools_condition)
    .compile(checkpointer=checkpointer)
)


# hotel_assistant = create_react_agent(
#     model="anthropic:claude-3-5-sonnet-latest",
#     tools=[book_hotel, transfer_to_flight_assistant],
#     prompt="You are a hotel booking assistant",
#     name="hotel_assistant",
# )


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
tools = [
    web_search,
    joke_generation,
]
tool_node = ToolNode(tools)


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
    .add_node("tools", tool_node)
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


supervisor = (
    StateGraph(MessagesState)
    # 注意：`destinations` 仅用于可视化，不影响运行时行为
    .add_node(supervisor_agent, destinations=("research_agent", "math_agent", END))
    .add_node("research_agent", research_agent)
    .add_node("math_agent", math_agent)
    .add_edge(START, "supervisor")
    # 总是返回到监督器
    .add_edge("research_agent", "supervisor")
    .add_edge("math_agent", "supervisor")
    .compile(checkpointer=checkpointer)
)


config = {
    "configurable": {
        "thread_id": uuid.uuid4(),
    }
}

for chunk in supervisor.stream(
    {
        "messages": [
            {
                "role": "user",
                # "content": "find US and New York state GDP in 2024. what % of US GDP was New York state?",
                "content": "1+1 = ?",
            }
        ]
    },
    subgraphs=True,
    config=config,
    # stream_mode=["messages"],
):
    # pretty_print_messages(chunk, last_message=True)
    # print("************************ ************************")
    print(chunk)
    print("####################")


print("--- 恢复执行 ---")

for chunk in supervisor.stream(
    Command(resume="approve"), subgraphs=True, config=config
):
    print(chunk)


print("####################=======================")
print(chunk)
final_message_history = chunk[1]["supervisor"]["messages"]
for message in final_message_history:
    message.pretty_print()

# for token, metadata in supervisor.stream(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": "为我写一个笑话,要求是要好笑",
#             }
#         ]
#     },
#     stream_mode="messages",
# ):
#     # print(token)
#     # print("************************ ************************")
#     # print(metadata)
#     print("####################")
#     print(token.content, sep="&&", end="\n", flush=True)

# print("=====================================")
