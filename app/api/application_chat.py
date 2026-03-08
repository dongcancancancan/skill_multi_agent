"""
对话历史相关API路由
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Query, Header
from app.utils.logger import logger
from app.utils.postgresql_client import get_postgresql_client
from app.api.auth import verify_token
from app.utils.local_storage import get_local_storage

router = APIRouter(prefix="/api/applicationChat", tags=["ApplicationChat"])


@router.get("/getFlowHistory")
async def get_flow_history(
    applicationConfigId: str = Query(None, description="应用配置ID"),
    userName: str = Query(None, description="用户名"),
    windowNo: str = Query(None, description="窗口编号，用于按窗口号分组查询"),
    authorization: str = Header(None, description="Authorization header, e.g. 'Bearer <token>'"),
):
    """
    获取对话历史记录，按时间分组
    
    Args:
        applicationConfigId: 应用配置ID（作为session_id使用，可选）
        userName: 用户名（可选）
    
    Returns:
        Dict: 按时间分组的对话历史记录
    """
    try:
        # 如果前端传来了 token，则解析出 user_id；否则尝试用 applicationConfigId / userName 做备用匹配
        user_id = None
        # 支持从 Authorization header 解析 token（格式: 'Bearer <token>'）
        token = None
        if authorization:
            try:
                if authorization.lower().startswith('bearer '):
                    token = authorization.split(' ', 1)[1].strip()
                else:
                    token = authorization.strip()
            except Exception:
                token = authorization

        if token:
            try:
                user_info = verify_token(token)
                if user_info:
                    user_id = getattr(user_info, "userid", None)
                else:
                    logger.warning("提供的 token 无效或已过期")
            except Exception as e:
                logger.warning(f"解析 token 失败: {e}")

        # 如果没有通过 token 获取到 user_id，优先使用 userName 参数
        if not user_id and userName:
            user_id = userName

        # 如果仍没有 user_id，也可以尝试使用 applicationConfigId 作为 session 标识，但此接口主要按 user_id 查询
        if not user_id and not applicationConfigId:
            logger.info("未提供 token 或 userName，无法按用户查询 session_history，返回空结果")
            return {"data": {"today": {}, "yestoday": {}, "last30": {}}, "message": "未提供用户信息", "status": "success"}
        # 从数据库查询 session_history，按 create_time 降序
        client = get_postgresql_client()
        try:
            # 构建查询条件和参数
            sql_conditions = ["del_flag = 0"]
            sql_params = []
            
            # 如果提供了 windowNo，则按 windowNo 过滤
            if windowNo:
                sql_conditions.append("windows_no = %s")
                sql_params.append(windowNo)
            else:
                # 如果没有提供 windowNo，则按 user_id 查询
                sql_conditions.append("user_id = %s")
                sql_params.append(user_id)
            
            # 过滤掉 query 为 1-10、approve、reject 的记录
            sql_conditions.append("(query IS NULL OR query NOT IN ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'approve', 'reject'))")
            
            # 构建完整的 SQL 查询
            sql = (
                "SELECT id, user_id, create_time, query, answer, windows_no, think_content FROM session_history "
                f"WHERE {' AND '.join(sql_conditions)} ORDER BY create_time DESC"
            )
            rows = client.execute_query(sql, tuple(sql_params))
        except Exception as e:
            logger.error(f"从 session_history 查询失败: {e}")
            raise HTTPException(status_code=500, detail="查询 session_history 失败")

        # 返回扁平化的历史记录列表（按 create_time 降序），每条记录包含 windows_no
        records = []
        for r in rows:
            try:
                ct = r.get("create_time")
                if not ct:
                    continue
                # create_time 可能是字符串或 datetime
                if isinstance(ct, str):
                    create_dt = datetime.fromisoformat(ct.replace('Z', '+00:00'))
                else:
                    create_dt = ct

                # 统一格式化 create_time 为 年-月-日 时:分:秒
                try:
                    formatted_time = create_dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    formatted_time = str(r.get("create_time")) if r.get("create_time") is not None else ""

                query_value = r.get("query")
                # 如果 query 的值为 1-10、'approve'、'reject'，则转换为空字符串
                if query_value in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'approve', 'reject']:
                    query_value = ""
                
                records.append({
                    "id": r.get("id"),
                    "query": query_value,
                    "answer": r.get("answer"),
                    "create_time": formatted_time,
                    "windows_no": r.get("windows_no"),
                    "think_content": r.get("think_content"),
                })
            except Exception as e:
                logger.warning(f"处理session_history记录失败: {e}")
                continue

        logger.info(f"获取对话历史成功 - user_id: {user_id}, count: {len(records)}")
        # 如果存在 windows_no 字段，则按 windows_no 分组返回数据，方便前端按会话窗口聚合展示
        try:
            has_windows = any(r.get("windows_no") for r in records)
        except Exception:
            has_windows = False

        if has_windows:
            grouped = {}
            for r in records:
                key = r.get("windows_no") or "_no_windows_no"
                grouped.setdefault(key, []).append(r)

            # 将分组转换为列表返回，按 create_time 对每组内记录排序（正序）
            grouped_list = []
            for k, v in grouped.items():
                try:
                    v_sorted = sorted(v, key=lambda x: x.get("create_time") or "")
                except Exception:
                    v_sorted = v
                grouped_list.append({
                    "windows_no": k,
                    "records": v_sorted,
                    "count": len(v_sorted)
                })

            return {"data": grouped_list, "message": "获取对话历史成功（按 windows_no 分组）", "status": "success"}

        return {"data": records, "message": "获取对话历史成功", "status": "success"}
        
    except Exception as e:
        logger.error(f"获取对话历史失败 - 应用ID: {applicationConfigId or '未指定'}, 用户: {userName or '未指定'}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")


@router.get("/pageFlowQa")
async def page_flow_qa(
    flowId: str = Query(..., description="会话ID"),
    current: int = Query(1, description="当前页码"),
    size: int = Query(200, description="每页大小"),
    windowsNo: str = Query(None, description="窗口编号，优先按 windows_no 表/字段查询")
):
    """
    分页获取会话中的问答记录
    
    Args:
        flowId: 会话ID
        current: 当前页码
        size: 每页大小
    
    Returns:
        Dict: 分页的问答记录
    """
    try:
        # 增加可选参数 windowsNo：若传入则优先按 windows_no 从数据库（先尝试 windows_no 表，再回退到 session_history）查询对话记录
        # 若未提供 windowsNo，则保持原有从 local_storage 加载会话消息的行为
        # 注意：前端会将 /api/applicationChat/getFlowHistory 中分组的 windows_no 传入本接口以获取对应会话的问答明细
        windows_no = None
        # 如果 flowId 实际上携带 windowsNo（兼容旧调用），保持兼容性；但优先使用显式参数（前端应传 windowsNo）
        # 这里不改动 flowId 的必需性，仅在有 windowsNo 时切换数据源

        # try to read windowsNo from query parameters if provided via flowId-like usage
        # (前端应以独立参数 windowsNo 调用，本段仅做防御性保留)
        # 如果需要严格变更为可选 flowId，可进一步修改函数签名

        # 获取数据库客户端用于按 windows_no 查询（若提供）
        client = get_postgresql_client()

        records = []
        # 如果前端传入 windowsNo，则优先按该编号从数据库查询对话数据
        if windowsNo:
            try:
                # 先尝试查询名为 windows_no 的表（按需求）；若表不存在或无数据，再回退到 session_history 表
                rows = []
                if not rows:
                    # 回退：按 session_history 表中的 windows_no 字段查询
                    sql_fallback = (
                        "SELECT id, user_id, create_time, query, answer, windows_no,think_content,interrupt_data FROM session_history "
                        "WHERE del_flag = 0 AND windows_no = %s ORDER BY create_time ASC"
                    )
                    rows = client.execute_query(sql_fallback, (windowsNo,))

                for r in rows:
                    query_value = r.get("query")
                    # 如果 query 的值为 1-10、'approve'、'reject'，则转换为空字符串
                    if query_value in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'approve', 'reject']:
                        query_value = ""
                    
                    records.append({
                        "id": r.get("id"),
                        "query": query_value,
                        "answer": r.get("answer"),
                        "create_time": r.get("create_time"),
                        "windows_no": r.get("windows_no"),
                        "think_content": r.get("think_content"),
                        "interrupt_data": r.get("interrupt_data"),
                    })
            except Exception as e:
                logger.error(f"按 windowsNo 查询对话失败: {e}")
                raise HTTPException(status_code=500, detail="按 windowsNo 查询对话失败")
        else:
            # 浏览器/本地存储回退逻辑：保持原有从 local_storage 加载消息并成对组成问答记录的行为
            local_storage = get_local_storage()
            
            # 加载会话中的所有消息
            messages = local_storage.load_messages(flowId)
            
            # 转换为前端需要的格式
            for i, message in enumerate(messages):
                # 根据消息类型确定是问题还是回答
                role = message.get("role", "")
                content = message.get("content", "")
                
                if role == "human":
                    # 这是用户的问题
                    if i < len(messages) - 1 and messages[i+1].get("role") == "ai":
                        # 下一个消息是AI的回答
                        ai_message = messages[i+1]
                        records.append({
                            "query": content,
                            "answer": ai_message.get("content", ""),
                            "think_content": ai_message.get("think_content", ""),
                            "timestamp": message.get("timestamp", "")
                        })
        # 如果前端把 windowsNo 当作 flowId 传入（兼容）或未来增加参数，这里尝试从 query params 中读取
        # 实际的前端请直接传入 windowsNo 参数到本接口
        # 从 request 查询参数中获取 windowsNo（FastAPI 会自动把 Query 参数注入到函数，暂时不修改签名）

        # 如果请求的 flowId 看起来像 windows_no（例如全数字或包含特殊前缀），我们不会盲目解析；优先检查 query params via imported FastAPI Request would be needed.
        # 为保持实现简单：如果调用者在 URL 中以 flowId 传入 windowsNo，请改用新的参数调用，当前实现基于新增 windowsNo 参数优先处理。

        # try windows_no via environment if present in function locals (no change), but actual param addition handled below
        
        # NOTE: page_flow_qa 现在支持 windowsNo 参数，请在前端以 ?windowsNo=... 调用以触发 DB 查询逻辑
        
        # 本函数会在下方按 windowsNo 分支填充 records；如果 windowsNo 没提供，则回退到原有 local_storage 逻辑

        # 回退点：暂无 windowsNo，使用 local_storage（旧行为）
        
        # 如果没有 windowsNo，我们再执行原有 local_storage 加载逻辑
        
        # (保留下面的 local_storage 加载逻辑在函数末尾)
        
        # 计算分页
        total = len(records)
        start_index = (current - 1) * size
        end_index = start_index + size
        paged_records = records[start_index:end_index]
        
        logger.info(f"获取会话问答记录成功 - 会话ID: {flowId}, 记录数: {len(paged_records)}")
        return {
            "data": {
                "records": paged_records,
                "total": total,
                "size": size,
                "current": current,
                "pages": (total + size - 1) // size
            },
            "message": "获取问答记录成功",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"获取会话问答记录失败 - 会话ID: {flowId}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取问答记录失败: {str(e)}")


@router.delete("/deleteFlow")
async def delete_flow(flowId: str = Query(..., description="会话ID")):
    """
    删除会话记录 - 逻辑删除
    
    Args:
        flowId: 会话ID
    
    Returns:
        Dict: 删除结果
    """
    try:
        # 获取数据库客户端
        client = get_postgresql_client()
        
        # 执行逻辑删除，将 del_flag 设置为 1
        sql = "UPDATE session_history SET del_flag = 1, update_time = CURRENT_TIMESTAMP WHERE id = %s"
        row_count = client.execute_dml(sql, (flowId,))
        
        if row_count > 0:
            logger.info(f"逻辑删除会话成功 - 会话ID: {flowId}")
            return {
                "data": None,
                "message": "删除成功",
                "status": "success"
            }
        else:
            logger.warning(f"逻辑删除会话失败 - 会话ID: {flowId} 可能不存在")
            return {
                "data": None,
                "message": "删除失败，会话可能不存在",
                "status": "error"
            }
        
    except Exception as e:
        logger.error(f"逻辑删除会话失败 - 会话ID: {flowId}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.delete("/deleteFlowByWindowNo")
async def delete_flow_by_window_no(windowNo: str = Query(..., description="窗口编号")):
    """
    根据窗口编号逻辑删除会话记录
    
    Args:
        windowNo: 窗口编号
    
    Returns:
        Dict: 删除结果
    """
    try:
        # 获取数据库客户端
        client = get_postgresql_client()
        
        # 执行逻辑删除，将 del_flag 设置为 1
        sql = "UPDATE session_history SET del_flag = 1, update_time = CURRENT_TIMESTAMP WHERE windows_no = %s"
        row_count = client.execute_dml(sql, (windowNo,))
        
        if row_count > 0:
            logger.info(f"根据窗口编号逻辑删除会话成功 - 窗口编号: {windowNo}, 删除记录数: {row_count}")
            return {
                "data": {
                    "deleted_count": row_count
                },
                "message": f"删除成功，共删除 {row_count} 条记录",
                "status": "success"
            }
        else:
            logger.warning(f"根据窗口编号逻辑删除会话失败 - 窗口编号: {windowNo} 可能不存在")
            return {
                "data": None,
                "message": "删除失败，该窗口编号可能不存在",
                "status": "error"
            }
        
    except Exception as e:
        logger.error(f"根据窗口编号逻辑删除会话失败 - 窗口编号: {windowNo}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")


@router.delete("/deleteSessionByWindowsNo")
async def delete_session_by_windows_no(windowsNo: str = Query(..., description="窗口编号")):
    """
    根据窗口编号逻辑删除session_history内的数据
    
    Args:
        windowsNo: 窗口编号
    
    Returns:
        Dict: 删除结果，包含删除的记录数量
    """
    try:
        # 获取数据库客户端
        client = get_postgresql_client()
        
        # 执行逻辑删除，将 del_flag 设置为 1
        sql = "UPDATE session_history SET del_flag = 1, update_time = CURRENT_TIMESTAMP WHERE windows_no = %s"
        row_count = client.execute_dml(sql, (windowsNo,))
        
        if row_count > 0:
            logger.info(f"根据窗口编号逻辑删除session_history数据成功 - 窗口编号: {windowsNo}, 删除记录数: {row_count}")
            return {
                "data": {
                    "deleted_count": row_count
                },
                "message": f"删除成功，共删除 {row_count} 条记录",
                "status": "success"
            }
        else:
            logger.warning(f"根据窗口编号逻辑删除session_history数据失败 - 窗口编号: {windowsNo} 可能不存在")
            return {
                "data": None,
                "message": "删除失败，该窗口编号可能不存在",
                "status": "error"
            }
        
    except Exception as e:
        logger.error(f"根据窗口编号逻辑删除session_history数据失败 - 窗口编号: {windowsNo}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除session_history数据失败: {str(e)}")


@router.post("/addFlow")
async def add_flow():
    """
    创建新会话（占位符接口，实际由start接口处理）
    """
    return {
        "data": str(uuid.uuid4()),
        "message": "创建会话成功",
        "status": "success"
    }


@router.post("/addFlowQa")
async def add_flow_qa():
    """
    添加问答记录（占位符接口，实际由消息存储处理）
    """
    return {
        "data": None,
        "message": "添加问答记录成功",
        "status": "success"
    }


@router.post("/qaPromptAndDocs")
async def qa_prompt_and_docs():
    """
    获取Prompt和知识检索结果（占位符接口）
    """
    return {
        "data": {
            "prompt": "placeholder_prompt",
            "docs": []
        },
        "message": "获取Prompt和知识检索结果成功",
        "status": "success"
    }


@router.post("/qa")
async def qa():
    """
    问答接口（占位符接口，实际由agents接口处理）
    """
    return {
        "data": "placeholder_answer",
        "message": "问答成功",
        "status": "success"
    }
