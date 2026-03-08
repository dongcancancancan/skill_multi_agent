"""
工具模块公共功能
提供统一的进度信息输出功能
"""

from langgraph.config import get_stream_writer
from app.utils.logger import agent_logger as logger


def send_progress_info(data: str, status: str = "success", type: str = "progress") -> None:
    """发送进度信息到流式输出
    
    Args:
        data: 进度信息内容
        status: 状态，默认为"success"
        type: 信息类型，默认为"progress"
    """
    progress_info = {
        "type": type,
        "status": status,
        "data": data,
    }
    stream_writer = get_stream_writer()
    if stream_writer:
        stream_writer(progress_info)
        logger.info(f"已通过custom流模式输出progress信息: {progress_info}")


def send_citation_info(citation_key: str, source_description: str, status: str = "success") -> None:
    """发送角标和来源信息到流式输出
    
    Args:
        citation_key: 角标key，如[s1]或[1]
        source_description: 来源描述，如{{来源：数据库表: loan_product_info}}
        status: 状态，默认为"success"
    """
    citation_info = {
        "type": "tip",
        "status": status,
        "data": {
            "citation_key": citation_key,
            "source_description": source_description
        }
    }
    stream_writer = get_stream_writer()
    if stream_writer:
        stream_writer(citation_info)
        logger.info(f"已通过custom流模式输出角标信息: {citation_info}")
