"""
RAG History 格式转换工具

将 state.rag_history 转换为前端需要的 knowledge_base 格式
"""

from typing import Dict, Any
from app.utils.logger import logger


def format_rag_history_to_knowledge_base(
    rag_history: Dict[str, Any] | None,
) -> Dict[str, Any] | None:
    if not rag_history:
        logger.debug("[RAG Formatter] rag_history 为空，跳过转换")
        return None

    all_segments = rag_history.get("all_segments", [])
    if not all_segments:
        logger.debug("[RAG Formatter] all_segments 为空，跳过转换")
        return None

    # 从 all_segments 构造 documents
    documents = []
    for seg in all_segments:
        # 提取 segment 字段（参照 policy_query_tool.merge_rag_segments）
        global_id = seg.get("id")
        source_id = seg.get("source_id", "")
        content = seg.get("content", "")
        score = seg.get("score", 0.0)
        document_name = seg.get("document_name", "")

        # 数据完整性检查
        if not global_id or not content:
            logger.warning(
                f"[RAG Formatter] Segment 数据不完整，跳过: "
                f"global_id={global_id}, content_len={len(content)}"
            )
            continue

        # 构造显示名称
        name_parts = [f"知识库引用 #{global_id}"]
        if document_name:
            name_parts.append(f"文档: {document_name}")
        doc_name = " | ".join(name_parts)

        # 构造 document（每个 segment 作为独立 document）
        documents.append(
            {
                "document_id": source_id if source_id else f"rag_seg_{global_id}",
                "name": doc_name,
                "url": "",
                "download_url": "",
                "segments": [
                    {
                        "content": content,
                        "score": score,
                        "global_id": global_id,  # 用于匹配 <context id='X'>
                        "segment_id": source_id,  # 真实 segment id
                    }
                ],
            }
        )

    if not documents:
        logger.warning("[RAG Formatter] 没有有效的 segments，跳过转换")
        return None

    # 构造前端格式（与 parse_knowledge_base_info 输出一致）
    knowledge_base_data = {
        "type": "knowledge_base",
        "status": "success",
        "data": {
            "content": {
                "type": "knowledge_base",
                "status": "success",
                "original_data": {
                    "total_documents": len(documents),
                    "query": {"content": ""},
                    "documents": documents,
                },
            }
        },
    }

    logger.info(
        f"[RAG Formatter] 转换完成 | "
        f"总 Segments: {len(all_segments)} | "
        f"有效 Documents: {len(documents)}"
    )

    return knowledge_base_data


__all__ = ["format_rag_history_to_knowledge_base"]
