from langgraph.graph import StateGraph, END, MessagesState
from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.tools import tool, InjectedToolCallId
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langgraph.graph import START
from langchain_core.messages import SystemMessage
from langgraph.types import RunnableConfig
from langgraph.types import interrupt
import os
from app.utils.logger import agent_logger as logger


def create_placeholder_agent(name: str, checkpointer: BaseCheckpointSaver = None):
    """
    A factory function to create simple, placeholder agent graphs.
    These agents just print a message and add it to the state, then terminate.
    You can replace these with your actual test agents.
    """

    def agent_node(state: MessagesState):
        print(f"--- Executing Placeholder Agent: {name} ---")
        return {"messages": [AIMessage(content=f"Response from {name}")]}

    builder = StateGraph(MessagesState)
    builder.add_node(name, agent_node)
    builder.add_edge(name, END)

    return builder.compile(checkpointer=checkpointer)


class MathAgent:
    def __init__(
        self, checkpointer: BaseCheckpointSaver = None, llm: ChatOpenAI = None
    ):
        self.checkpointer = checkpointer
        self.llm = llm

    # Define the node that calls the model

    def call_math_llm(
        self,
        state: MessagesState,
        config: RunnableConfig,
    ):
        # this is similar to customizing the create_react_agent with 'prompt' parameter, but is more flexible
        system_prompt = SystemMessage(
            "You are a math agent.\n\n"
            "INSTRUCTIONS:\n"
            "- You must use human_node tool to approve the user's question first\n"
            "- Assist ONLY with math-related tasks\n"
            "- After you're done with your tasks, respond to the supervisor directly\n"
            "- as possible as you can, use the tool to get the result\n"
            "- Respond ONLY with the results of your work, do NOT include ANY other text."
        )

        # sw = get_stream_writer()
        # for chunk in llm2.stream([system_prompt] + state["messages"]):
        #     sw(chunk)
        tools = [self.add, self.multiply, self.divide, self.human_node]
        response = self.llm.bind_tools(tools).invoke(
            [system_prompt] + state["messages"]
        )
        # logger.info(f"MathAgent response: {response}")
        # logger.info("*" * 100)
        # We return a list, because this will get added to the existing list
        # print("*" * 100)
        # print(response)
        # print("*" * 100)
        return {"messages": [response]}

    def _create_graph(self):
        tools = [self.add, self.multiply, self.divide, self.human_node]
        tool_node = ToolNode(tools)

        return (
            StateGraph(MessagesState)
            .add_node("call_math_llm", self.call_math_llm)
            .add_node("tools", tool_node)
            .add_edge(START, "call_math_llm")
            .add_edge("tools", "call_math_llm")
            .add_conditional_edges("call_math_llm", tools_condition)
            .compile(checkpointer=self.checkpointer)
        )

    @tool
    def add(a: float, b: float):
        """Add two numbers."""
        return a + b

    @tool
    def multiply(a: float, b: float):
        """Multiply two numbers."""
        return a * b

    @tool
    def divide(a: float, b: float):
        """Divide two numbers."""
        return a / b

    @tool
    def human_node(query: str) -> str:
        """
        用户审查节点，用于批准用户问题是否可以执行数学运算

        Args:
            query (str): 用户的输入问题
        """
        answer = interrupt("approve or reject?")
        print(f"Got an answer of {answer}")
        return answer


class ResearchAgent:
    def __init__(
        self, checkpointer: BaseCheckpointSaver = None, llm: ChatOpenAI = None
    ):
        self.checkpointer = checkpointer
        self.llm = llm

    @tool
    def joke_generation(self, topic: str):
        """Generate a joke about the given topic."""
        result = self.llm.invoke(f"Generate a joke about {topic}")
        return f"Here is a joke about {topic}: {result.content}"

    def call_research_llm(
        self,
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
        response = self.llm.invoke([system_prompt] + state["messages"])
        return {"messages": [response]}

    def _create_graph(self):
        os.environ["TAVILY_API_KEY"] = "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"
        from langchain_tavily import TavilySearch

        web_search = TavilySearch(max_results=3)
        tools = [self.joke_generation, web_search]
        tool_node = ToolNode(tools)

        return (
            StateGraph(MessagesState)
            .add_node("call_research_llm", self.call_research_llm)
            .add_node("tools", tool_node)
            .add_edge(START, "call_research_llm")
            .add_conditional_edges("call_research_llm", tools_condition)
            .add_edge("tools", "call_research_llm")
            .compile(checkpointer=self.checkpointer)
        )
