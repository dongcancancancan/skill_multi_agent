"""
XML API调用工具封装 - 处理XML响应并解析为结构化数据
基于提供的XML响应样例进行映射解析
使用新的解析器架构直接从XML生成描述文字
"""

import requests
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from app.utils.logger import agent_logger as logger
from app.utils.config import get_config

# 导入新的解析器模块
from .parseResponse import ParserFactory


class XMLAPITool:
    """XML API调用工具类，专门处理XML响应"""
    
    def __init__(self, host: str = "10.1.93.208", port: int = 8090):
        self.base_url = f"http://{get_config('edss_api.host') or host}:{get_config('edss_api.port') or port}/services"
        self.headers = {'Content-Type': 'application/xml'}
    
    def call_api(self, service_id: str, xml_payload: str) -> Dict[str, Any]:
        """调用XML API并解析响应
        
        Args:
            service_id: 服务ID，如"400640"
            xml_payload: XML请求负载
            
        Returns:
            包含原始数据和接口解析的结构化数据
        """
        url = f"{self.base_url}/{service_id}"
        
        # 发送XML请求
        response = requests.post(url, data=xml_payload, headers=self.headers)
        
        # 使用新的解析器架构直接解析XML响应并生成描述文字
        interpretation = ParserFactory.parse_xml_directly(service_id, response.text)
        
        # 返回统一格式
        return {
            "raw_data": response.text,  # 保留原始XML响应
            "interpretation": interpretation
        }
    
    def parse_xml_directly(self, service_id: str, xml_response: str) -> str:
        """直接解析XML响应并生成描述文字，跳过字典转换步骤
        
        Args:
            service_id: 服务ID
            xml_response: XML响应字符串
            
        Returns:
            直接生成的描述文字
        """
        return ParserFactory.parse_xml_directly(service_id, xml_response)
    
    def get_supported_services(self) -> list:
        """获取支持的服务ID列表"""
        return ParserFactory.get_supported_services()


# 全局实例
xml_api_tool = XMLAPITool()
