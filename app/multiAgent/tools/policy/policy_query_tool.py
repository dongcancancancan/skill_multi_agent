"""
政策库查询工具 - 知识库查询入口
提供政策信息查询功能，支持某某银行内部政策知识库查询
"""

import json
from typing import Dict, Any, Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langgraph.types import Command, interrupt

from app.multiAgent.tools.query_knowledge_base import query_knowledge_base
from app.multiAgent.common.tool_decorator import with_error_handling
from app.multiAgent.common.uni_state import UniState, StateFields
import asyncio
from app.utils.logger import logger
from app.utils.config import get_config
from app.multiAgent.tools.common import send_progress_info


# 从配置文件读取政策知识库ID
# 环境配置通过config/[sit|uat].yaml管理
DATASET_ID = get_config("knowledge.policy_dataset_id")

if not DATASET_ID:
    raise ValueError(
        "政策知识库ID未配置！请在config文件中设置knowledge.policy_dataset_id"
    )


def merge_rag_segments(
    current_rag_history: Dict[str, Any],
    new_segments: list[Dict],
    agent_name: str,
) -> Dict[str, Any]:
    """
    合并 RAG segments 到全局 rag_history，在合并时即完成标签化和 id 分配

    Args:
        current_rag_history: 当前的 rag_history（包含 all_segments 和 agent_mapping）
        new_segments: 新查询到的 segments（来自知识库 records）
        agent_name: 当前调用的 agent 名称

    Returns:
        更新后的 rag_history，结构为：
        {
            "all_segments": [
                {
                    "id": 1,  # 全局唯一自增id
                    "source_id": "原始segment.id",
                    "content": "...",
                    "formatted": "<context id='1' source_id='原始id'>内容</context>"
                },
                ...
            ],
            "agent_mapping": {
                "agent_name": [1, 2, 5],  # 该agent使用的全局id列表
                ...
            }
        }
    """
    # 1. 初始化 rag_history 结构
    all_segments = current_rag_history.get("all_segments", [])
    agent_mapping = current_rag_history.get("agent_mapping", {})

    # 2. 构建 source_id 到全局 id 的映射（用于去重）
    source_id_to_global_id = {}
    for seg in all_segments:
        if isinstance(seg, dict) and "source_id" in seg:
            source_id_to_global_id[seg["source_id"]] = seg["id"]

    # 3. 计算当前最大 id
    max_id = max([seg.get("id", 0) for seg in all_segments], default=0)

    # 4. 当前 agent 使用的 segment id 列表
    agent_segment_ids = agent_mapping.get(agent_name, [])

    # 5. 遍历新 segments，去重并分配 id
    for seg_data in new_segments:
        if not isinstance(seg_data, dict) or "segment" not in seg_data:
            continue

        segment = seg_data["segment"]
        source_id = segment.get("id")
        content = segment.get("content", "")
        # 安全获取 document_name 和 score
        document_name = segment.get("document", {}).get("name", "未知文档")
        score = seg_data.get("score", 0)

        if not source_id:
            logger.warning(f"Segment 缺少 id 字段，跳过: {segment}")
            continue

        # 检查是否已存在（基于 source_id 去重）
        if source_id in source_id_to_global_id:
            # 已存在，获取全局 id
            global_id = source_id_to_global_id[source_id]
            logger.debug(f"Segment {source_id} 已存在，全局 id={global_id}")
        else:
            # 不存在，分配新的全局 id
            max_id += 1
            global_id = max_id

            # 生成 formatted 字段
            formatted = (
                f"<context id='{global_id}' source_id='{source_id}'>{content}</context>"
            )

            # 添加到 all_segments
            new_segment = {
                "id": global_id,
                "source_id": source_id,
                "content": content,
                "formatted": formatted,
                "score": score,
                "document_name": document_name,
            }
            all_segments.append(new_segment)
            source_id_to_global_id[source_id] = global_id

            logger.debug(
                f"新增 Segment: source_id={source_id}, global_id={global_id}, "
                f"document={document_name}, score={score:.6f}"
            )

        # 记录当前 agent 使用的 segment id（避免重复）
        if global_id not in agent_segment_ids:
            agent_segment_ids.append(global_id)

    # 6. 更新 agent_mapping
    agent_mapping[agent_name] = agent_segment_ids

    # 7. 返回更新后的 rag_history
    updated_rag_history = {
        "all_segments": all_segments,
        "agent_mapping": agent_mapping,
    }

    logger.info(
        f"RAG History 更新 | Agent: {agent_name} | "
        f"全局 Segments 总数: {len(all_segments)} | "
        f"当前 Agent 使用 Segments: {len(agent_segment_ids)} | "
        f"新增 Segments: {max_id - (max([seg.get('id', 0) for seg in current_rag_history.get('all_segments', [])], default=0))}"
    )

    return updated_rag_history


@tool("policy_query_tool")
@with_error_handling
def policy_query_tool(
    query: str,
    agent: str = "overall",
    state: Annotated[UniState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """政策库查询工具

    查询绿色金融和蓝色金融相关政策文件，支持政策解读和准入标准查询。
    查询结果会自动缓存到 state.rag_history 中，按 agent 名称分组并自动去重。

    Args:
        query: 查询内容，描述需要查询的政策信息
            示例：'查询绿色金融相关政策'、'蓝色金融准入标准'
        agent: 调用来源的 agent 标识，用于追踪和日志记录
            - 具体子 agent 传入对应名称，如 'blue_green_access_agent'
            - 不在具体子 agent 时传入 'overall'

    Returns:
        Command: 包含更新后的 state 和工具执行结果

    功能：
        - 绿色金融政策查询：获取绿色金融相关的政策文件
        - 蓝色金融政策查询：获取蓝色金融相关的政策文件
        - 准入标准查询：查询绿色/蓝色金融的准入标准
        - 政策解读：提供政策文件的解读和分析

    示例：
        >>> policy_query_tool('查询绿色金融相关政策', agent='blue_green_access_agent')
        >>> policy_query_tool('蓝色金融准入标准', agent='overall')
    """
    try:
        logger.info(f"政策库查询 | Agent: {agent} | Query: {query}")
        if not query:
            interrupt("请提供详细的政策信息，如对公金融政策、环保政策等")

        # 输出进度信息（agent 名称汉化）
        from app.multiAgent.common.agent_name_mapper import get_agent_display_name

        agent_display_name = get_agent_display_name(agent)
        progress_data = f"📜 政策库查询 | 执行方: {agent_display_name} | 查询：{query}"
        send_progress_info(progress_data)

        # 尝试从LangGraph上下文中获取config
        config = None
        try:
            from langgraph.config import get_config as get_langgraph_config

            config = get_langgraph_config()
        except Exception as e:
            logger.warning(f"无法从LangGraph上下文获取config: {e}")

        # 查询知识库获取政策信息（使用异步调用）
        knowledge_result = asyncio.run(
            query_knowledge_base(
                query=query,
                dataset_id=DATASET_ID,
                config=config,  # 传递config参数以启用流式输出
            )
        )
        logger.info(f"政策库查询结果：{knowledge_result}")

        # 获取当前查询的 records (segments)
        current_records = knowledge_result.get("records", [])

        # 从 state 中获取现有的 rag_history
        rag_history = state.get(StateFields.RAG_HISTORY) or {}

        # 使用新的 merge_rag_segments 函数合并并去重 segments
        updated_rag_history = merge_rag_segments(
            current_rag_history=rag_history,
            new_segments=current_records,
            agent_name=agent,
        )

        # 构造返回结果
        result_payload = {
            "status": "success",
            "query": query,
            "agent": agent,
            "dataset_id": DATASET_ID,
            "result": {
                "content": current_records if current_records else "未找到相关政策",
            },
        }

        # 创建 ToolMessage
        tool_message = ToolMessage(
            content=json.dumps(result_payload, ensure_ascii=False, indent=2),
            name="policy_query_tool",
            tool_call_id=tool_call_id,
        )

        # 获取当前消息列表
        current_messages = list(state.get(StateFields.MESSAGES, []))

        # 返回 Command 更新 state
        return Command(
            update={
                StateFields.MESSAGES: current_messages + [tool_message],
                StateFields.RAG_HISTORY: updated_rag_history,
            }
        )

    except Exception as exc:
        logger.error(f"政策库查询工具错误: {exc}", exc_info=True)
        error_payload = {
            "status": "error",
            "query": query,
            "agent": agent,
            "error": str(exc),
        }
        error_message = ToolMessage(
            content=json.dumps(error_payload, ensure_ascii=False),
            name="policy_query_tool",
            tool_call_id=tool_call_id,
        )
        current_messages = list(state.get(StateFields.MESSAGES, []))
        return Command(
            update={StateFields.MESSAGES: current_messages + [error_message]}
        )


# 导出工具实例
policy_tool = policy_query_tool
