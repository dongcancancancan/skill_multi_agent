"""知识库查询工具"""

import os
import requests
from typing import Dict, Optional
from app.utils.logger import agent_logger as logger
from app.utils.config import get_config
from app.multiAgent.tools.knowledge_base_parser import parse_knowledge_base_info


async def query_knowledge_base(
    query: str,
    dataset_id: str = "eec4cb44-0b0e-4342-8891-560388fdd495",
    top_k: int = 10,
    enable_streaming: bool = True,
    config: Optional[Dict] = None,
) -> Dict:
    """查询知识库API

    Args:
        query: 查询文本
        dataset_id: 知识库数据集ID
        top_k: 返回结果数量
        enable_streaming: 是否启用流式输出
        config: LangGraph配置对象，用于流式写入

    Returns:
        知识库查询结果

    Raises:
        ValueError: 当API配置不完整时
        requests.exceptions.RequestException: 当请求失败时
    """
    # 从配置文件读取知识库配置
    knowledge_api_base = get_config("knowledge.api_base")
    knowledge_api_key = get_config("knowledge.api_key")

    if not knowledge_api_base or not knowledge_api_key:
        raise ValueError(
            "知识库API配置不完整！请配置config/default.yaml中的knowledge.api_base和api_key配置项"
        )

    url = f"{knowledge_api_base}{dataset_id}/retrieve"
    headers = {
        "Authorization": f"Bearer {knowledge_api_key}",
        "Content-Type": "application/json",
    }
    # data = {"query": query, "top_k": top_k}
    data = {
        "query": query,
        "retrieval_model": {
            "search_method": "keyword_search",
            "reranking_enable": False,
            "top_k": top_k,
            "score_threshold_enabled": False
        }
    }

    # 打印请求详细信息
    logger.info(f"========== 知识库查询请求 ==========")
    logger.info(f"请求URL: {url}")
    logger.info(f"数据集ID: {dataset_id}")
    logger.info(f"请求头: {{'Authorization': 'Bearer ***', 'Content-Type': '{headers.get('Content-Type')}'}}")
    logger.info(f"请求体: {data}")
    logger.info(f"查询文本: {query}")
    logger.info(f"返回数量(top_k): {top_k}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        # 打印响应基本信息
        logger.info(f"========== 知识库查询响应 ==========")
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应头: {dict(response.headers)}")
        
        # 如果响应不是2xx，打印详细错误信息
        if not response.ok:
            try:
                error_detail = response.json()
                logger.error(f"知识库API返回错误详情: {error_detail}")
            except Exception as json_error:
                # 如果无法解析JSON，打印原始文本（限制长度）
                error_text = response.text[:1000] if hasattr(response, 'text') else str(response.content[:1000])
                logger.error(f"知识库API返回错误（非JSON格式）: {error_text}")
                logger.error(f"响应内容类型: {response.headers.get('Content-Type', 'unknown')}")
        
        response.raise_for_status()
        
        # 成功响应，解析并打印结果摘要
        knowledge_data = response.json()
        logger.info(f"知识库查询成功")
        if isinstance(knowledge_data, dict):
            # 打印结果摘要
            if 'data' in knowledge_data:
                result_count = len(knowledge_data.get('data', []))
                logger.info(f"返回结果数量: {result_count}")
            else:
                logger.info(f"返回数据结构: {list(knowledge_data.keys())}")
        logger.info(f"=====================================")

        # 禁用实时溯源发送，RAG 信息将由 reporter/toolbox 统一发送
        # RAG 信息已通过 policy_query_tool 中的 merge_rag_segments 写入 state.rag_history
        # if enable_streaming and config:
        #     try:
        #         # 导入langgraph.config用于流式写入
        #         from langgraph.config import get_stream_writer
        #
        #         # 解析知识库信息
        #         parsed_info = await parse_knowledge_base_info(
        #             knowledge_data, dataset_id, headers
        #         )
        #
        #         # 通过custom流模式输出解析后的信息
        #         stream_writer = get_stream_writer()
        #         if stream_writer:
        #             # 修复：传递符合自定义流模式格式的字典
        #             custom_stream_data = {
        #                 "type": "knowledge_base",
        #                 "status": "success",
        #                 "data": parsed_info,
        #             }
        #             stream_writer(custom_stream_data)
        #             logger.info("已通过custom流模式输出知识库解析信息")
        #
        #     except Exception as e:
        #         logger.warning(f"知识库流式输出失败，但不影响主流程: {e}")

        return knowledge_data

    except requests.exceptions.HTTPError as e:
        # 对于HTTP错误，尝试获取响应体详细信息
        logger.error(f"========== 知识库查询HTTP错误 ==========")
        # HTTPError 总是有 response 属性
        status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else 'unknown'
        logger.error(f"HTTP状态码: {status_code}")
        logger.error(f"错误URL: {url}")
        
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                logger.error(f"错误详情(JSON): {error_detail}")
                # 特别处理 Weaviate 连接错误
                if isinstance(error_detail, dict) and 'message' in error_detail:
                    message = error_detail.get('message', '')
                    if 'Weaviate' in message or 'weaviate' in message.lower():
                        logger.error(f"⚠️  检测到 Weaviate 向量数据库连接失败！")
                        logger.error(f"   这通常是 Dify 服务器端配置问题，请检查：")
                        logger.error(f"   1. Weaviate 服务是否正在运行")
                        logger.error(f"   2. Dify 的 Weaviate 连接配置是否正确")
                        logger.error(f"   3. 网络连接是否正常")
            except Exception:
                # 如果无法解析JSON，打印原始文本
                error_text = e.response.text[:1000] if hasattr(e.response, 'text') else str(e.response.content[:1000])
                logger.error(f"错误详情(文本): {error_text}")
                logger.error(f"响应内容类型: {e.response.headers.get('Content-Type', 'unknown')}")
        else:
            logger.error(f"错误信息: {str(e)}")
        logger.error(f"=========================================")
        raise
        
    except requests.exceptions.RequestException as e:
        logger.error(f"========== 知识库查询请求异常 ==========")
        logger.error(f"异常类型: {type(e).__name__}")
        logger.error(f"异常信息: {str(e)}")
        logger.error(f"请求URL: {url}")
        logger.error(f"=========================================")
        raise


# 导出函数
__all__ = ["query_knowledge_base"]
