import asyncio
import json
import time
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# 导入生产环境的请求模型
from app.api.models import MainGraphRequest, GraphStreamResult
from langgraph.checkpoint.memory import InMemorySaver

# 导入测试框架的核心组件
from tests.test_framework.test_supervisor import TestSupervisor
from app.utils.llm import get_llm
from tests.test_framework.test_agents import MathAgent, ResearchAgent


# ===================================================================
# Global Supervisor Instance Initialization
# ===================================================================

# 模块级初始化，确保所有启动方式都能复用同一个检查点存储器
checkpointer = InMemorySaver()
non_stream_llm = get_llm(disable_streaming=True)
stream_llm = get_llm(disable_streaming=False)

# 初始化 Agent 实例
math_agent = MathAgent(checkpointer=checkpointer, llm=non_stream_llm)
research_agent = ResearchAgent(checkpointer=checkpointer, llm=non_stream_llm)

# 初始化 TestSupervisor 实例
supervisor_instance = TestSupervisor(
    llm=stream_llm,
    agent_runnables={
        "math_agent": math_agent._create_graph(),
        "research_agent": research_agent._create_graph(),
    },
    checkpointer=checkpointer,
)

# ===================================================================
# App Lifespan Management
# ===================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器"""
    # 启动时执行
    print("E2E Test Server initialized with shared checkpointer")
    print(
        f"Supervisor instance checkpointer ID: {id(supervisor_instance.checkpointer)}"
    )
    yield
    # 关闭时执行（如果需要清理资源）
    print("E2E Test Server shutting down")


# ===================================================================
# App and Middleware Setup
# ===================================================================

app = FastAPI(
    title="E2E Test Server (Dynamic Assembly)",
    description="A server that dynamically assembles and runs a supervisor graph in the controller.",
    version="4.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================================================================
# FastAPI Endpoint with Dynamic Supervisor Assembly
# ===================================================================


def format_sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/v1/e2e_test_flow")
async def e2e_test_flow_endpoint(request: MainGraphRequest):
    """
    使用预初始化的 TestSupervisor 实例处理请求：
    1. 复用全局的 checkpointer，确保同一 session_id 下的历史消息得以保留
    2. 支持 resume 功能，可以恢复被中断的对话
    3. 流式返回处理结果
    """
    print(f"--- [API] Using shared supervisor instance for request: {request} ---")
    print(f"--- [API] Checkpointer ID: {id(supervisor_instance.checkpointer)} ---")

    # 使用预初始化的 supervisor_instance，确保所有请求共享同一个 checkpointer
    async def event_generator():
        stream_iter = supervisor_instance.astream(request)
        # ... (The rest of the SSE generator logic is identical to previous versions) ...
        tasks = set()
        try:
            data_task = asyncio.create_task(stream_iter.__anext__())
            tasks.add(data_task)
            heartbeat_task = asyncio.create_task(asyncio.sleep(15))
            tasks.add(heartbeat_task)
            while tasks:
                done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    if task == heartbeat_task:
                        yield format_sse_event(
                            event="heartbeat", data={"timestamp": time.time()}
                        )
                        heartbeat_task = asyncio.create_task(asyncio.sleep(15))
                        tasks.add(heartbeat_task)
                    elif task == data_task:
                        try:
                            result: GraphStreamResult = task.result()
                            if (
                                result.status == "success"
                                and result.data
                                and hasattr(result.data, "content")
                            ):
                                yield format_sse_event(
                                    event="message",
                                    data={"content": result.data.content},
                                )
                            elif result.status == "interrupted":
                                yield format_sse_event(
                                    event="interrupt",
                                    data={"interrupt_data": result.interrupt_data},
                                )
                            elif result.status == "error":
                                yield format_sse_event(
                                    event="error",
                                    data={"message": result.error_message},
                                )
                            # You can add handling for other statuses like 'interrupted' or 'error' here if needed
                            data_task = asyncio.create_task(stream_iter.__anext__())
                            tasks.add(data_task)
                        except StopAsyncIteration:
                            tasks.remove(data_task)
                            data_task = None  # Mark as done
                            # Cancel the heartbeat task as the main stream is finished
                            if heartbeat_task in tasks:
                                heartbeat_task.cancel()
                                tasks.remove(heartbeat_task)
                        except Exception as e:
                            yield format_sse_event(
                                event="error", data={"message": f"Stream error: {e}"}
                            )
                            return
                    if task in tasks:
                        tasks.remove(task)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            yield format_sse_event(event="end", data={})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ===================================================================
# Entrypoint to run this test server
# ===================================================================

if __name__ == "__main__":
    print("Starting E2E Test Server (v4.0 - Dynamic Assembly)")
    print("Access at http://127.0.0.1:8001")
    print("Test endpoint: POST http://127.0.0.1:8001/api/v1/e2e_test_flow")
    print(f"Using shared checkpointer: {id(checkpointer)}")
    uvicorn.run(app, host="127.0.0.1", port=8001)
