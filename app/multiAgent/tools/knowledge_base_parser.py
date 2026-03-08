"""
知识库信息解析工具
负责解析知识库API返回的信息，提取document_id并获取文档名称
"""

import asyncio
from typing import Dict, List, Set, Any
import requests
from app.utils.logger import logger


class KnowledgeBaseParser:
    """知识库信息解析器"""
    
    def __init__(self, base_url: str = "http://localhost:5001/v1"):
        self.base_url = base_url.rstrip('/')
    
    def extract_unique_document_ids(self, knowledge_base_response: Dict[str, Any]) -> Set[str]:
        """从知识库API响应中提取所有唯一的document_id
        
        Args:
            knowledge_base_response: 知识库API返回的完整响应数据
            
        Returns:
            Set[str]: 去重后的document_id集合
        """
        unique_ids = set()
        
        try:
            # 解析知识库API返回的数据结构
            if isinstance(knowledge_base_response, dict):
                # 检查records字段（根据测试输出，数据在records中）
                records = knowledge_base_response.get('records', [])
                if isinstance(records, list):
                    for record in records:
                        # 检查segment字段中的document_id
                        segment = record.get('segment', {})
                        if isinstance(segment, dict):
                            document_id = segment.get('document_id')
                            if document_id:
                                unique_ids.add(document_id)
                        
                        # 检查segment.document字段中的id
                        document_info = segment.get('document', {})
                        if isinstance(document_info, dict):
                            doc_id = document_info.get('id')
                            if doc_id:
                                unique_ids.add(doc_id)
                
                # 检查其他可能包含document_id的字段
                for key, value in knowledge_base_response.items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                # 检查segment字段
                                segment = item.get('segment', {})
                                if isinstance(segment, dict):
                                    doc_id = segment.get('document_id')
                                    if doc_id:
                                        unique_ids.add(doc_id)
                                
                                # 检查document字段
                                doc_info = item.get('document', {})
                                if isinstance(doc_info, dict):
                                    doc_id = doc_info.get('id')
                                    if doc_id:
                                        unique_ids.add(doc_id)
            
            logger.info(f"从知识库响应中提取到 {len(unique_ids)} 个唯一的document_id: {list(unique_ids)}")
            return unique_ids
            
        except Exception as e:
            logger.error(f"提取document_id时出错: {e}")
            return set()
    
    async def get_document_details(self, dataset_id: str, document_id: str, 
                                 headers: Dict[str, str]) -> Dict[str, Any]:
        """获取单个文档的详细信息
        
        Args:
            dataset_id: 数据集ID
            document_id: 文档ID
            headers: API请求头，包含认证信息
            
        Returns:
            Dict[str, Any]: 文档详细信息
        """
        try:
            url = f"{self.base_url}/datasets/{dataset_id}/documents/{document_id}"
            logger.debug(f"请求文档详情: {url}")
            
            # 使用异步方式调用API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(url, headers=headers, timeout=30)
            )
            
            if response.status_code == 200:
                document_data = response.json()
                logger.debug(f"成功获取文档 {document_id} 的详细信息")
                return document_data
            else:
                logger.warning(f"获取文档 {document_id} 详情失败: {response.status_code}")
                return {"error": f"HTTP {response.status_code}", "document_id": document_id}
                
        except Exception as e:
            logger.error(f"获取文档 {document_id} 详情时出错: {e}")
            return {"error": str(e), "document_id": document_id}
    
    async def get_upload_file_info(self, dataset_id: str, document_id: str,
                                 headers: Dict[str, str]) -> Dict[str, Any]:
        """获取上传文件信息，包括url和download_url
        
        Args:
            dataset_id: 数据集ID
            document_id: 文档ID
            headers: API请求头，包含认证信息
            
        Returns:
            Dict[str, Any]: 上传文件信息
        """
        try:
            url = f"{self.base_url}/datasets/{dataset_id}/documents/{document_id}/upload-file"
            logger.debug(f"请求上传文件信息: {url}")
            
            # 使用异步方式调用API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=headers, timeout=30)
            )
            
            if response.status_code == 200:
                file_data = response.json()
                logger.debug(f"成功获取文档 {document_id} 的上传文件信息")
                return file_data
            else:
                logger.warning(f"获取文档 {document_id} 上传文件信息失败: {response.status_code}")
                return {"error": f"HTTP {response.status_code}", "document_id": document_id}
                
        except Exception as e:
            logger.error(f"获取文档 {document_id} 上传文件信息时出错: {e}")
            return {"error": str(e), "document_id": document_id}
    
    async def parse_knowledge_base_response(self, 
                                          knowledge_base_response: Dict[str, Any],
                                          dataset_id: str,
                                          headers: Dict[str, str]) -> Dict[str, Any]:
        """解析知识库响应，获取所有文档的详细信息
        
        Args:
            knowledge_base_response: 知识库API返回的完整响应数据
            dataset_id: 数据集ID
            headers: API请求头，包含认证信息
            
        Returns:
            Dict[str, Any]: 解析后的知识库信息，包含文档列表和元数据
        """
        try:
            # 提取唯一的document_id
            document_ids = self.extract_unique_document_ids(knowledge_base_response)
            
            if not document_ids:
                logger.warning("知识库响应中没有找到任何document_id")
                return {
                    "type": "knowledge_base",
                    "status": "empty",
                    "message": "知识库响应中没有找到相关文档",
                    "documents": []
                }
            
            # 并发获取所有文档的详细信息
            tasks = []
            for doc_id in document_ids:
                task = self.get_document_details(dataset_id, doc_id, headers)
                tasks.append(task)
            
            # 等待所有文档详情请求完成
            document_details = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果，过滤掉异常
            valid_documents = []
            for i, detail in enumerate(document_details):
                doc_id = list(document_ids)[i]
                if isinstance(detail, Exception):
                    logger.error(f"获取文档 {doc_id} 详情时出现异常: {detail}")
                    valid_documents.append({
                        "document_id": doc_id,
                        "error": str(detail),
                        "name": f"未知文档-{doc_id[:8]}"
                    })
                elif isinstance(detail, dict):
                    # 提取文档名称和其他元数据
                    document_name = detail.get('name', f"文档-{doc_id[:8]}")
                    valid_documents.append({
                        "document_id": doc_id,
                        "name": document_name,
                        "metadata": detail.get('metadata', {}),
                        "content_preview": detail.get('content', '')[:200] + '...' if detail.get('content') else '',
                        "full_data": detail
                    })
            
            # 构建最终的解析结果
            parsed_result = {
                "type": "knowledge_base",
                "status": "success",
                "total_documents": len(valid_documents),
                "query": knowledge_base_response.get('query', ''),
                "documents": valid_documents,
                "original_response_keys": list(knowledge_base_response.keys())
            }
            
            logger.info(f"成功解析知识库响应，共处理 {len(valid_documents)} 个文档")
            return parsed_result
            
        except Exception as e:
            logger.error(f"解析知识库响应时出错: {e}")
            return {
                "type": "knowledge_base",
                "status": "error",
                "error": str(e),
                "documents": []
            }


# 创建全局解析器实例
_knowledge_base_parser = KnowledgeBaseParser()


async def parse_knowledge_base_info(knowledge_base_response: Dict[str, Any],
                                  dataset_id: str,
                                  headers: Dict[str, str]) -> Dict[str, Any]:
    """解析知识库信息的异步函数
    
    Args:
        knowledge_base_response: 知识库API返回的完整响应数据
        dataset_id: 数据集ID
        headers: API请求头，包含认证信息
        
    Returns:
        Dict[str, Any]: 精简格式的解析结果，包含segment、url和download_url字段
    """
    # 先获取完整的解析结果
    parsed_result = await _knowledge_base_parser.parse_knowledge_base_response(
        knowledge_base_response, dataset_id, headers
    )
    
    # 构建精简格式的返回数据
    documents = parsed_result.get('documents', [])
    
    # 并发获取所有文档的上传文件信息
    upload_file_tasks = []
    for doc in documents:
        doc_id = doc.get('document_id')
        if doc_id:
            task = _knowledge_base_parser.get_upload_file_info(dataset_id, doc_id, headers)
            upload_file_tasks.append(task)
    
    # 等待所有上传文件信息请求完成
    upload_file_results = await asyncio.gather(*upload_file_tasks, return_exceptions=True)
    
    # 处理文档列表，添加segment、url和download_url字段
    processed_documents = []
    for i, doc in enumerate(documents):
        doc_id = doc.get('document_id', '')
        
        # 从原始知识库响应中提取命中的文档块内容
        segments = []
        
        # 从knowledge_base_response中查找匹配的文档块
        records = knowledge_base_response.get('records', [])
        for record in records:
            segment_data = record.get('segment', {})
            if isinstance(segment_data, dict):
                segment_doc_id = segment_data.get('document_id')
                if segment_doc_id == doc_id:
                    # 提取文档块内容和score
                    content = segment_data.get('content', '')
                    score = record.get('score', 0.0)  # 获取匹配分数
                    
                    if content:
                        segments.append({
                            "content": content,
                            "score": score
                        })
        
        # 获取上传文件信息
        upload_file_info = {}
        if i < len(upload_file_results):
            file_result = upload_file_results[i]
            if isinstance(file_result, dict) and "error" not in file_result:
                upload_file_info = {
                    "url": file_result.get('url', ''),
                    "download_url": file_result.get('download_url', '')
                }
        
        # 构建处理后的文档信息
        processed_doc = {
            "document_id": doc_id,
            "name": doc.get('name', '未知文档'),
            "url": upload_file_info.get('url', ''),
            "download_url": upload_file_info.get('download_url', ''),
            "segments": segments  # 所有匹配的文档块，包含content和score
        }
        processed_documents.append(processed_doc)
    
    # 构建精简格式的返回结果
    return {
        "content": {
            "type": "knowledge_base",
            "status": parsed_result.get('status', 'unknown'),
            "original_data": {
                "total_documents": len(processed_documents),
                "query": {
                    "content": parsed_result.get('query', '')
                },
                "documents": processed_documents
            }
        }
    }
