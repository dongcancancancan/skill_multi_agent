import json
import uuid
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
from langchain_core.messages.ai import AIMessageChunk
from app.api.models import MainGraphRequest
from langchain_core.messages import HumanMessage
from app.multiAgent.analysis.blue_green_policy_agent import BlueGreenPolicyAgent
from app.multiAgent.analysis.blue_green_access_agent import BlueGreenAccessAgent
from app.multiAgent.analysis.blue_green_product_agent import BlueGreenProductAgent
from app.multiAgent.analysis.blue_green_solution_agent import BlueGreenSolutionAgent
from app.multiAgent.agents.enterprise_profile_agent import EnterpriseProfileAgent
from app.multiAgent.dispatch.unified_supervisor import (
    stream_with_unified_supervisor,
)
from app.utils.logger import logger as logger
from app.api.auth import verify_token
from app.utils.state_manager import (
    load_session_state,
    restore_session as restore_session_state,
    with_state_persistence,
)
from app.utils.local_storage import get_local_storage
from langgraph.types import Interrupt
from app.multiAgent.demo.demo_agent import execute_demo_supervisor, restore_demo_session
import time
from app.multiAgent.demo.demo_agent_new import execute_demo_agent, restore_demo_agent
from app.utils.snowflake import SnowflakeGenerator
from app.utils.postgresql_client import get_postgresql_client

generator = SnowflakeGenerator(machine_id=0)

router = APIRouter(prefix="/api/agents", tags=["Agents"])


# @router.post("/enterprise_profile_agent")
# def enterprise_profile_agent(request: Dict[str, Any]):
#     logger.info(f"企业画像分析agent请求参数: {str(request)}")
#     try:
#         # 创建EnterpriseProfileAgent实例并直接调用run方法
#         agent = EnterpriseProfileAgent()
#         final_result = agent.run(request)
#         logger.info(f"企业画像分析agent返回结果:{final_result}")

#         # 检查是否需要人工干预
#         if isinstance(final_result, dict) and final_result.get("awaiting_human_input", False):
#             # 返回202状态码和人工干预请求详情
#             return {
#                 "status": "awaiting_human_input",
#                 "message": "需要人工补充信息才能继续执行",
#                 "intervention_request": final_result.get("intervention_request", {}),
#                 "session_id": final_result.get("session_id", ""),
#                 "company": final_result.get("company", "")
#             }

#         return final_result  # 直接返回字符串结果
#     except Exception as e:
#         logger.error(f"企业画像分析agent执行异常: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

from app.api.models import GraphStreamResult


def format_sse_event(event: str, data: dict) -> str:
    """格式化SSE事件"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def parse_token(token_value: str) -> str:
    """解析token，返回用户ID"""
    # 尝试从token中解析用户信息
    user_id = None
    try:
        if token_value:
            user_info = verify_token(token_value)
            logger.info(f"verify_token 返回: {user_info}")
            if user_info:
                # 兼容 pydantic 对象和 dict
                if hasattr(user_info, "userid"):
                    user_id = getattr(user_info, "userid", None)
                elif isinstance(user_info, dict):
                    user_id = (
                        user_info.get("userid")
                        or user_info.get("user_id")
                        or user_info.get("username")
                    )
                else:
                    user_id = str(user_info)
                logger.info(f"从 token 解析到 user_id: {user_id}")
            else:
                logger.info("提供的 token 无效或已过期")
    except Exception as e:
        logger.warning(
            f"解析 token 时发生异常: {e}, user_info={locals().get('user_info', None)}"
        )
    return user_id


@with_state_persistence(agent_type="main_graph")
def _save_main_graph_result(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    包装函数，用于保存main_graph的执行结果
    """
    # 调用原有的执行函数
    result = execute_with_unified_supervisor(request)
    return result


async def save_interrupt_to_database(request, interrupt_state, collected_content, think_content_save):
    """保存中断数据到数据库"""
    try:
        # 特殊处理中断情况：如果遇到中断，保存中断信息而不是常规回答
        final_content_to_save = collected_content

        if interrupt_state["has_interrupt"] and interrupt_state["interrupt_data"]:
            # 对于中断情况，构建一个包含中断信息的回答
            interrupt_message = f"需要用户选择：{interrupt_state['interrupt_data'].get('message', '请从以下选项中选择')}"
            final_content_to_save = interrupt_message
            logger.info(f"🎯 检测到中断，保存中断信息: {interrupt_message}")

        # 确保 interrupt_data_to_save 有值
        interrupt_data_to_save = interrupt_state.get("interrupt_data_to_save")
        logger.info(f"🎯 最终中断数据保存状态: {interrupt_data_to_save is not None}")

        if final_content_to_save:
            from datetime import datetime

            # 保存用户问题
            user_message = {
                "role": "human",
                "content": request.input,
                "timestamp": datetime.now().isoformat(),
            }

            # 保存AI回答
            ai_message = {
                "role": "ai",
                "content": final_content_to_save,
                "timestamp": datetime.now().isoformat(),
            }

            # 使用本地存储保存消息
            local_storage = get_local_storage()
            session_id = request.session_id or str(uuid.uuid4())

            logger.info(f"🎯 开始保存中断消息 - 会话ID: {session_id}")
            success1 = local_storage.save_message(session_id, user_message)
            success2 = local_storage.save_message(session_id, ai_message)
            if success1 and success2:
                logger.info(
                    f"🎯 中断对话记录保存成功 - 会话ID: {session_id}, 用户问题: {request.input[:50]}..., AI回答长度: {len(final_content_to_save)}"
                )
            else:
                logger.error(
                    f"🎯 中断对话记录保存失败 - 会话ID: {session_id}, 用户问题保存: {success1}, AI回答保存: {success2}"
                )

        else:
            logger.warning("🎯 final_content_to_save为空，跳过保存")

        # 尝试从请求中的 session_id（或 metadata 中的 token）解析用户信息
        token_value = request.token or None
        user_id = parse_token(token_value)
        # 保存进数据库（示例：记录 windowNo 与生成的 id）
        windowNo = None
        if request.metadata:
            # 支持两种命名风格 windowNo 与 window_No
            windowNo = request.metadata.get("windowNo") or request.metadata.get("window_No")
        id = generator.next_id()

        logger.info(f"🎯 准备保存中断会话元信息: id={id}, windowNo={windowNo}")

        # 插入 session_history 表
        client = get_postgresql_client()
        sid = str(id)
        user_id_val = user_id if user_id else None

        # 不再尝试将 windowNo 转为 int，保持字符串格式由数据库处理（数字字符串可被隐式转换）
        windows_no_val = windowNo

        q_text = (request.input or "")[:1024]
        a_text = (final_content_to_save or "")

        # 处理思考内容，确保能够正确存储到数据库
        think_content_db = think_content_save  # 直接使用累积的思考内容字符串
        if think_content_db and len(think_content_db) > 4000:
            # 如果思考内容过长，进行截断
            think_content_db = think_content_db[:4000] + "...(截断)"

        # 修改数据库插入语句，添加 interrupt_data 字段
        insert_sql = (
            "INSERT INTO session_history "
            "(id, user_id, create_by, create_time, update_by, update_time, remark, query, answer, windows_no, del_flag, think_content, interrupt_data) "
            "VALUES (%s, %s, %s, NOW(), %s, NOW(), %s, %s, %s, %s, 0, %s, %s)"
        )

        create_by = user_id_val
        update_by = user_id_val
        remark = None

        # 详细的调试信息
        logger.info("🎯 === 中断数据库插入调试信息 ===")
        logger.info(f"🎯 中断数据最终值: {interrupt_data_to_save}")
        logger.info(f"🎯 中断数据类型: {type(interrupt_data_to_save)}")

        time.sleep(1)  # 确保时间戳不冲突

        # 执行数据库插入
        result = client.execute_dml(
            insert_sql,
            (
                sid,
                user_id_val,
                create_by,
                update_by,
                remark,
                q_text,
                a_text,
                windows_no_val,
                think_content_db,
                interrupt_data_to_save  # 保存中断数据到数据库
            ),
        )

        logger.info(f"🎯 中断数据库插入结果: {result}")
        logger.info(f"🎯 中断session_history插入成功: id={sid}, 思考内容长度: {len(think_content_db) if think_content_db else 0}, 中断数据: {interrupt_data_to_save is not None}")

    except Exception as e:
        logger.error("🎯 插入中断session_history失败: %s", str(e), exc_info=True)


async def save_normal_to_database(request, collected_content, think_content_save):
    """保存正常流程数据到数据库"""
    try:
        final_content_to_save = collected_content

        if final_content_to_save:
            from datetime import datetime

            # 保存用户问题
            user_message = {
                "role": "human",
                "content": request.input,
                "timestamp": datetime.now().isoformat(),
            }

            # 保存AI回答
            ai_message = {
                "role": "ai",
                "content": final_content_to_save,
                "timestamp": datetime.now().isoformat(),
            }

            # 使用本地存储保存消息
            local_storage = get_local_storage()
            session_id = request.session_id or str(uuid.uuid4())

            logger.info(f"开始保存正常消息 - 会话ID: {session_id}")
            success1 = local_storage.save_message(session_id, user_message)
            success2 = local_storage.save_message(session_id, ai_message)
            if success1 and success2:
                logger.info(
                    f"正常对话记录保存成功 - 会话ID: {session_id}, 用户问题: {request.input[:50]}..., AI回答长度: {len(final_content_to_save)}"
                )
            else:
                logger.error(
                    f"正常对话记录保存失败 - 会话ID: {session_id}, 用户问题保存: {success1}, AI回答保存: {success2}"
                )

        else:
            logger.warning("final_content_to_save为空，跳过保存")

        # 尝试从请求中的 session_id（或 metadata 中的 token）解析用户信息
        token_value = request.token or None
        user_id = parse_token(token_value)
        # 保存进数据库（示例：记录 windowNo 与生成的 id）
        windowNo = None
        if request.metadata:
            # 支持两种命名风格 windowNo 与 window_No
            windowNo = request.metadata.get("windowNo") or request.metadata.get("window_No")
        id = generator.next_id()

        logger.info(f"准备保存正常会话元信息: id={id}, windowNo={windowNo}")

        # 插入 session_history 表
        client = get_postgresql_client()
        sid = str(id)
        user_id_val = user_id if user_id else None

        windows_no_val = windowNo

        q_text = (request.input or "")[:1024]
        a_text = (final_content_to_save or "")[:1024]

        # 处理思考内容，确保能够正确存储到数据库
        think_content_db = think_content_save
        if think_content_db and len(think_content_db) > 4000:
            think_content_db = think_content_db[:4000] + "...(截断)"

        insert_sql = (
            "INSERT INTO session_history "
            "(id, user_id, create_by, create_time, update_by, update_time, remark, query, answer, windows_no, del_flag, think_content, interrupt_data) "
            "VALUES (%s, %s, %s, NOW(), %s, NOW(), %s, %s, %s, %s, 0, %s, %s)"
        )

        create_by = user_id_val
        update_by = user_id_val
        remark = None

        time.sleep(1)

        # 执行数据库插入
        result = client.execute_dml(
            insert_sql,
            (
                sid,
                user_id_val,
                create_by,
                update_by,
                remark,
                q_text,
                a_text,
                windows_no_val,
                think_content_db,
                None  # 正常流程没有中断数据
            ),
        )

        logger.info(f"正常数据库插入结果: {result}")
        logger.info(f"正常session_history插入成功: id={sid}, 思考内容长度: {len(think_content_db) if think_content_db else 0}")

    except Exception as e:
        logger.error(f"插入正常session_history失败: {e}", exc_info=True)


@router.post("/main_graph")
async def main_graph_agent(request: MainGraphRequest):
    """
    使用统一Supervisor架构处理多Agent系统请求 - SSE流式接口
    """
    logger.info(f"多Agent系统调度[SSE]请求参数: {request}")

    async def event_generator():
        """事件生成器，用于流式返回处理过程，具有健壮的任务管理和异常处理。"""
        stream_iter = stream_with_unified_supervisor(request)
        think_content_save = ""
        # 收集流式消息用于后续保存
        collected_messages = []
        collected_content = ""

        # 使用字典来确保状态一致性
        interrupt_state = {
            "has_interrupt": False,
            "interrupt_data": None,
            "interrupt_data_to_save": None,
            "handled_interrupt": False  # 新增字段，标记中断是否已处理
        }

        # 标记是否已经保存了中断数据
        interrupt_saved = False

        tasks = set()
        try:
            # 初始化第一个数据获取任务
            data_task = asyncio.create_task(stream_iter.__anext__())
            tasks.add(data_task)

            # 初始化心跳任务
            heartbeat_interval = 15
            heartbeat_task = asyncio.create_task(asyncio.sleep(heartbeat_interval))
            tasks.add(heartbeat_task)

            while tasks:
                done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                for task in done:
                    if task == heartbeat_task:
                        # 心跳任务完成
                        yield format_sse_event(
                            event="heartbeat", data={"timestamp": time.time()}
                        )
                        # 创建新的心跳任务
                        heartbeat_task = asyncio.create_task(
                            asyncio.sleep(heartbeat_interval)
                        )
                        tasks.add(heartbeat_task)

                    elif task == data_task:
                        # 数据任务完成
                        try:
                            chunk: GraphStreamResult = task.result()

                            # 根据状态生成不同类型的SSE事件
                            if chunk.status == "error":
                                yield format_sse_event(
                                    event="error", data={"message": chunk.error_message}
                                )
                                return  # 出错则终止
                            elif chunk.status == "interrupted" and not interrupt_state["handled_interrupt"]:
                                # 处理中断情况 - 保存完整的中断数据到状态字典
                                interrupt_state["has_interrupt"] = True
                                interrupt_state["interrupt_data"] = chunk.interrupt_data
                                interrupt_state["handled_interrupt"] = True  # 标记为已处理
                                logger.info("🎯 ===== 检测到中断! =====")

                                # 序列化中断数据
                                try:
                                    interrupt_state["interrupt_data_to_save"] = json.dumps(
                                        chunk.interrupt_data, ensure_ascii=False, default=str
                                    )
                                    logger.debug(f"中断数据序列化成功")
                                except Exception as e:
                                    logger.error(f"中断数据序列化失败: {e}")
                                    interrupt_state["interrupt_data_to_save"] = None

                                # 保存数据到数据库
                                if not interrupt_saved:
                                    await save_interrupt_to_database(request, interrupt_state, collected_content, think_content_save)
                                    interrupt_saved = True
                                    logger.debug("中断数据已保存到数据库")

                                yield format_sse_event(
                                    event="interrupt",
                                    data={"interrupt_data": chunk.interrupt_data},
                                )

                                # 中断后不再继续处理
                                for t in tasks:
                                    t.cancel()
                                break

                            elif chunk.status == "success":
                                # 处理流式数据，支持多种数据类型
                                content = ""
                                if hasattr(chunk.data, "content"):
                                    # 如果chunk.data是对象且有content属性
                                    content = chunk.data.content
                                elif (
                                    isinstance(chunk.data, dict)
                                    and "content" in chunk.data
                                ):
                                    # 如果chunk.data是字典且包含content字段
                                    content = chunk.data["content"]
                                elif isinstance(chunk.data, str):
                                    # 如果chunk.data是字符串
                                    content = chunk.data

                                # 收集流式内容用于保存 - 这里确保所有message事件内容都被收集
                                if content:
                                    collected_content += content
                                    # 同时记录消息事件用于调试
                                    collected_messages.append({
                                        "type": "message",
                                        "content": content,
                                        "timestamp": time.time()
                                    })

                                # 处理溯源信息：优先检查chunk.data是否为knowledge_base类型
                                trace_info_content = None
                                if (
                                    isinstance(chunk.data, dict)
                                    and chunk.data.get("type") == "knowledge_base"
                                ):
                                    # 如果chunk.data是knowledge_base类型，将其作为trace_info发送
                                    trace_info_content = chunk.data
                                    logger.info(
                                        f"检测到knowledge_base类型数据，作为trace_info发送: {trace_info_content}"
                                    )
                                elif chunk.trace_info:
                                    # 否则，使用原有的trace_info字段
                                    trace_info_content = chunk.trace_info
                                    logger.info(
                                        f"使用原有trace_info字段: {trace_info_content}"
                                    )

                                # 确保溯源信息正确发送到前端
                                if trace_info_content:
                                    logger.info(
                                        f"发送溯源信息到前端: {type(trace_info_content)}"
                                    )
                                    yield format_sse_event(
                                        event="trace_info",
                                        data={"content": trace_info_content},
                                    )

                                # 发送消息内容事件
                                if content:
                                    yield format_sse_event(
                                        event="message",
                                        data={"content": content},
                                    )

                            # 处理进度信息：检查chunk.data是否为progress类型
                            progress_content = None
                            if (
                                isinstance(chunk.data, dict)
                                and chunk.data.get("type") == "progress"
                            ):
                                progress_content = chunk.data
                                logger.debug(
                                    f"检测到progress类型数据，作为progress信息发送: {progress_content}"
                                )
                                yield format_sse_event(
                                    event="progress",
                                    data={"content": progress_content},
                                )

                            # 处理角标信息：检查chunk.data是否为tip类型
                            tip_content = None
                            if (
                                isinstance(chunk.data, dict)
                                and chunk.data.get("type") == "tip"
                            ):
                                tip_content = chunk.data
                                logger.info(
                                    f"检测到tip类型数据，作为tip信息发送: {tip_content}"
                                )
                                yield format_sse_event(
                                    event="tip",
                                    data={"content": tip_content},
                                )

                            # 处理思考信息：检查chunk.data是否为thinking类型（在所有状态下都需要处理）
                            thinking_content = None
                            if (
                                isinstance(chunk.data, dict)
                                and chunk.data.get("type") == "thinking"
                            ):
                                # 如果chunk.data是thinking类型，将其作为thinking信息发送
                                thinking_content = chunk.data
                                logger.debug(
                                    f"检测到thinking类型数据，作为thinking信息发送: {thinking_content}"
                                )
                                # 累积思考内容，而不是覆盖
                                thinking_data = thinking_content.get("data", "")
                                if thinking_data:
                                    if think_content_save:
                                        # 如果已有思考内容，追加新的思考内容
                                        think_content_save += "\n" + thinking_data
                                    else:
                                        # 第一次接收到思考内容
                                        think_content_save = thinking_data

                                # 确保思考信息正确发送到前端
                                logger.debug(
                                    f"发送思考信息到前端: {type(thinking_content)}"
                                )

                                # 统一处理thinking信息格式，确保符合前端要求：{"content": {"type": "thinking", "status": "success", "data": ""}}
                                standard_thinking_format = {
                                    "type": "thinking",
                                    "status": "success",
                                    "data": thinking_data,
                                }

                                # 确保最终格式符合前端要求：{"content": {"type": "thinking", "status": "success", "data": ""}}
                                final_thinking_data = {
                                    "content": standard_thinking_format
                                }

                                yield format_sse_event(
                                    event="thinking",
                                    data=final_thinking_data,
                                )

                            # 创建下一个数据获取任务（除非遇到中断）
                            if not interrupt_state["has_interrupt"]:
                                data_task = asyncio.create_task(stream_iter.__anext__())
                                tasks.add(data_task)
                            else:
                                # 如果遇到中断，不再创建新的数据任务
                                tasks.remove(data_task)
                                data_task = None

                        except StopAsyncIteration:
                            tasks.remove(data_task)
                            data_task = None  # Mark as done
                            # Cancel the heartbeat task as the main stream is finished
                            if heartbeat_task in tasks:
                                heartbeat_task.cancel()
                                tasks.remove(heartbeat_task)
                        except Exception as e:
                            error_message = str(e)
                            # 使用 exception() 自动捕获完整堆栈信息
                            logger.exception(f"Stream error: {error_message}")
                            yield format_sse_event(
                                event="error",
                                data={"message": f"Stream error: {error_message}"},
                            )
                            return

                    # 从任务集合中移除已完成的任务
                    if task in tasks:
                        tasks.remove(task)

        except asyncio.CancelledError:
            # 客户端断开连接，日志记录
            logger.info("SSE连接被客户端取消")
            # 此处不应再有 yield
        except Exception as e:
            # 生成器顶层异常
            logger.exception(f"agent执行异常: {str(e)}")
            yield format_sse_event(
                event="error", data={"message": f"agent执行异常: {str(e)}"}
            )
        finally:
            # 清理所有仍在运行的任务
            for task in tasks:
                task.cancel()
            # 等待任务被真正取消
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("SSE event_generator 清理完成")

            # 🎯 关键修改：只有在没有立即保存中断数据的情况下，才在finally块中保存
            if interrupt_state["has_interrupt"] and not interrupt_saved:
                logger.info("🎯 在finally块中保存中断数据")
                await save_interrupt_to_database(request, interrupt_state, collected_content, think_content_save)
            elif not interrupt_state["has_interrupt"]:
                # 正常流程的保存
                await save_normal_to_database(request, collected_content, think_content_save)

            # 发送结束事件
            yield format_sse_event(event="end", data={})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{session_id}/history")
def get_conversation_history(session_id: str):
    """获取会话历史记录接口

    Args:
        session_id: 会话标识符

    Returns:
        List[Dict]: 按时间顺序排序的对话消息列表
    """
    try:
        local_storage = get_local_storage()
        messages = local_storage.load_messages(session_id)

        return {
            "session_id": session_id,
            "messages": messages,
            "message_count": len(messages),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"获取会话历史记录失败 - session_id: {session_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话历史记录失败: {str(e)}")


@router.get("/sessions/list")
def get_all_sessions():
    """获取所有会话列表接口 - 供前端展示历史会话

    Returns:
        List[Dict]: 所有会话的基本信息列表
    """
    try:
        local_storage = get_local_storage()
        sessions_info = local_storage.get_all_sessions()

        # 转换为前端友好的格式
        sessions_list = []
        for session_id, info in sessions_info.items():
            sessions_list.append(
                {
                    "session_id": session_id,
                    "last_updated": info.get("last_updated"),
                    "message_count": info.get("file_count", 0),
                    "total_size": info.get("total_size", 0),
                    "first_message": info.get(
                        "first_message"
                    ),  # 新增字段，包含会话的第一个消息内容
                }
            )

        # 按最后更新时间排序，最新的在前
        sessions_list.sort(key=lambda x: x.get("last_updated", ""), reverse=True)

        return {
            "sessions": sessions_list,
            "total_count": len(sessions_list),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")
