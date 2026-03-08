from typing import Dict, Any, List

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool, Tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from app.api.models import MainGraphRequest, GraphStreamResult
from app.utils.llm import get_llm
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langgraph.graph import START, MessagesState
from langgraph.types import RunnableConfig
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from typing import Annotated
from langgraph.types import Interrupt
from langchain_openai import ChatOpenAI
from app.utils.logger import agent_logger as logger
from langchain_core.messages import AIMessage, AIMessageChunk


class TestSupervisor:
    """
    A factory class that generates a supervisor graph.
    It is initialized with a dictionary of agent runnables, allowing for dynamic assembly.
    This structure mirrors the principles of `UnifiedSupervisor`.
    """

    def __init__(
        self,
        llm: ChatOpenAI,
        agent_runnables: Dict[str, CompiledStateGraph],
        checkpointer: BaseCheckpointSaver = None,
    ):
        self.agent_runnables = agent_runnables
        self.checkpointer = checkpointer
        self.llm = llm
        self.supervisor_graph = self._create_graph()

    def create_handoff_tool(self, *, agent_name: str, description: str | None = None):
        name = f"transfer_to_{agent_name}"
        description = description or f"Ask {agent_name} for help."

        @tool(name, description=description)
        def handoff_tool(
            state: Annotated[MessagesState, InjectedState],
            tool_call_id: Annotated[str, InjectedToolCallId],
        ) -> Command:
            logger.info(f"Successfully transferred to {agent_name}")
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

    def _create_graph(self):
        """Dynamically builds the graph based on the provided agent runnables."""
        handoff_tools = []
        for agent_name in self.agent_runnables.keys():
            handoff_tools.append(
                self.create_handoff_tool(
                    agent_name=agent_name,
                    description=f"将任务分配给{agent_name}进行处理",
                )
            )

        supervisor_agent = create_react_agent(
            model=self.llm,
            tools=handoff_tools,
            prompt=(
                "Important Instructions :\n"
                "You are a supervisor managing two agents:\n"
                "- a research agent. Assign research-related or joke generation tasks to this agent, \n"
                "- a math agent. Assign math-related tasks to this agent\n"
                "- when you get the subagent respone, if your answer is similar to the subagent response, exit the loop directly, do not generate duplicate response.\n"
                "Assign work to one agent at a time, do not call agents in parallel.\n"
                "Do not do any work yourself."
            ),
            name="supervisor",
            checkpointer=self.checkpointer,
        )

        # 3. Build the StateGraph
        builder = StateGraph(MessagesState)
        builder.add_node("supervisor", supervisor_agent)

        # 4. Add agent nodes and edges dynamically
        for name, agent_runnable in self.agent_runnables.items():
            builder.add_node(name, agent_runnable)
            builder.add_edge(name, "supervisor")

        builder.set_entry_point("supervisor")
        return builder.compile(checkpointer=self.checkpointer)

    async def astream(self, request: MainGraphRequest):
        """
        The main streaming method to execute the graph.
        """
        config = {"configurable": {"thread_id": request.session_id}}

        if request.is_resume:
            # state_history = list(self.supervisor_graph.get_state_history(config))
            # print(state_history)
            # print("*" * 100)
            async for graph, stream_mode, chunk in self.supervisor_graph.astream(
                Command(resume=request.input),
                config,
                stream_mode=["messages", "updates"],
                subgraphs=True,
            ):
                if stream_mode == "messages":
                    if isinstance(chunk[0], AIMessage) or isinstance(
                        chunk[0], AIMessageChunk
                    ):
                        yield GraphStreamResult(
                            status="success",
                            stream_mode=stream_mode,
                            data=chunk[0],
                        )
                elif stream_mode == "updates":
                    # 只返回最后一个interrupt信息
                    if (
                        isinstance(chunk, dict)
                        and "__interrupt__" in chunk
                        and isinstance(chunk["__interrupt__"][0], Interrupt)
                        and len(graph) == 0
                    ):
                        yield GraphStreamResult(
                            status="interrupted",
                            stream_mode=stream_mode,
                            data=chunk,
                            interrupt_data=chunk["__interrupt__"][0].value,
                        )
        else:
            initial_state = {"messages": [HumanMessage(content=request.input)]}
            async for graph, stream_mode, chunk in self.supervisor_graph.astream(
                initial_state,
                config,
                stream_mode=["messages", "updates"],
                subgraphs=True,
            ):
                if stream_mode == "messages":
                    if isinstance(chunk[0], AIMessage) or isinstance(
                        chunk[0], AIMessageChunk
                    ):
                        yield GraphStreamResult(
                            status="success",
                            stream_mode=stream_mode,
                            data=chunk[0],
                        )
                elif stream_mode == "updates":
                    # 只返回最后一个interrupt信息
                    if (
                        isinstance(chunk, dict)
                        and "__interrupt__" in chunk
                        and isinstance(chunk["__interrupt__"][0], Interrupt)
                        and len(graph) == 0
                    ):
                        yield GraphStreamResult(
                            status="interrupted",
                            stream_mode=stream_mode,
                            data=chunk,
                            interrupt_data=chunk["__interrupt__"][0].value,
                        )
