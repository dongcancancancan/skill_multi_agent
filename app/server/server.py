"""
FastAPI服务端接口，基于server/docs下的XML请求报文和返回报文生成
端口：8082
返回挡板真实数据
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from app.utils.logger import agent_logger as logger
import xml.etree.ElementTree as ET
from typing import Dict, Any
import os
from pathlib import Path

app = FastAPI(title="金融服务接口", description="基于XML报文的服务端接口", version="1.0.0")

# 服务映射表：服务ID -> 服务名称（包含目录路径）
SERVICE_MAPPING = {
    "400640": "股权冻结核查",
    "400604": "环保处罚详情", 
    "400631": "汇法司法风险企业画像换签版",
    "400687": "经营异常核查",
    "403501": "绿金/非项目辅助识别",
    "403502": "绿金/根据资金用途提示获取分类信息",
    "403500": "绿金/项目绿色认定",
    "401058": "企查查环保信用评价",
    "401008": "企查查客户身份识别",
    "400690": "企业年报信息",
    "400601": "失信详情",
    "400682": "行政处罚核查",
    "400639": "核查/股权冻结核查",
    "400637": "核查/环保处罚核查",
    "401049": "核查/企查查失信核查",
    "401015": "企查查股东信息工商登记",
    "401029": "企查查历史高管核查"
}

def load_response_xml(service_id: str, search_key: str = None) -> str:
    """加载对应服务的响应XML文件，支持根据公司名称查找特定响应文件"""
    service_name = SERVICE_MAPPING.get(service_id)
    if not service_name:
        raise ValueError(f"未知的服务ID: {service_id}")
    
    # 构建响应文件路径
    base_dir = Path(__file__).parent / "docs"
    service_dir = base_dir / service_name
    
    # 如果提供了搜索关键词，尝试查找包含公司名称的响应文件
    if search_key:
        # 尝试查找包含公司名称的响应文件
        company_files = list(service_dir.glob(f"*{search_key}*res*.xml"))
        if company_files:
            # 读取公司特定的响应文件
            with open(company_files[0], 'r', encoding='utf-8') as f:
                return f.read()
    
    # 查找默认的响应文件（不包含公司名称）
    resp_files = list(service_dir.glob(f"*{service_id}*res*.xml"))
    if not resp_files:
        raise FileNotFoundError(f"未找到服务 {service_id} 的响应文件")
    
    # 读取默认响应文件内容
    with open(resp_files[0], 'r', encoding='utf-8') as f:
        return f.read()


def process_403501_response(xml_content: str) -> str:
    """处理403501服务的响应XML，对特定fundsTipId进行records过滤
    
    Args:
        xml_content: 原始XML响应内容
        
    Returns:
        处理后的XML响应内容
    """
    try:
        # 解析XML
        root = ET.fromstring(xml_content)
        
        # 查找所有records元素
        records_elems = root.findall('.//records')
        
        # 如果没有records或只有一个record，直接返回
        if len(records_elems) <= 1:
            return xml_content
        
        # 检查是否存在特定的fundsTipId
        special_funds_tip_ids = ["SM_FUNDS_PBOCGL_25V1_NO0013", "SM_FUNDS_PBOCGL_25V1_NO0015"]
        has_special_funds_tip_id = False
        
        for record in records_elems:
            funds_tip_id_elem = record.find('fundsTipId')
            if funds_tip_id_elem is not None and funds_tip_id_elem.text:
                funds_tip_id = funds_tip_id_elem.text.strip()
                if funds_tip_id in special_funds_tip_ids:
                    has_special_funds_tip_id = True
                    logger.info(f"检测到特殊fundsTipId: {funds_tip_id}，进行records过滤处理")
                    break
        
        # 如果存在特定的fundsTipId且records数量大于1，则只保留第一个record
        if has_special_funds_tip_id and len(records_elems) > 1:
            # 找到records的父元素
            parent_elem = None
            for record in records_elems:
                parent_elem = record.getparent()
                if parent_elem is not None:
                    break
            
            if parent_elem is not None:
                # 移除除第一个record之外的所有records
                for i in range(len(records_elems) - 1, 0, -1):
                    parent_elem.remove(records_elems[i])
                
                logger.info(f"已过滤records，保留第一个record，原始records数量: {len(records_elems)}")
                
                # 返回处理后的XML
                return ET.tostring(root, encoding='utf-8').decode('utf-8')
        
        return xml_content
        
    except ET.ParseError as e:
        logger.error(f"XML解析失败: {e}")
        return xml_content
    except Exception as e:
        logger.error(f"处理403501响应时发生错误: {e}")
        return xml_content

def parse_search_key_from_request(xml_content: str) -> str:
    """从请求XML中解析searchKey字段"""
    try:
        root = ET.fromstring(xml_content)
        # 查找searchKey元素
        search_key_elem = root.find(".//searchKey")
        if search_key_elem is not None and search_key_elem.text:
            return search_key_elem.text.strip()
        return None
    except ET.ParseError:
        return None

@app.post("/services/{service_id}")
async def handle_service_request(service_id: str, request: Request):
    """处理服务请求，返回对应的响应XML"""
    try:
        # 检查服务ID是否有效
        if service_id not in SERVICE_MAPPING:
            raise HTTPException(status_code=404, detail=f"服务ID {service_id} 不存在")
        
        # 读取请求体
        request_body = await request.body()
        request_xml = request_body.decode('utf-8')
        
        # 解析请求XML中的searchKey
        search_key = parse_search_key_from_request(request_xml)
        logger.info(f"收到服务 {service_id} 请求，搜索关键词: {search_key}")
        logger.info(f"收到服务 request_xml:{request_xml}")
        
        # 加载对应的响应XML
        response_xml = load_response_xml(service_id, search_key)
        
        # 如果是403501服务，处理响应XML
        if service_id == "403501":
            response_xml = process_403501_response(response_xml)
            logger.info("已对403501响应进行特殊处理")
        
        logger.info(f"返回服务 response_xml:{response_xml} 的响应数据")
        
        # 返回XML响应
        return Response(content=response_xml, media_type="application/xml")
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")

@app.get("/services")
async def list_services():
    """列出所有可用的服务"""
    return {
        "services": [
            {"service_id": sid, "service_name": name, "endpoint": f"/services/{sid}"}
            for sid, name in SERVICE_MAPPING.items()
        ]
    }

@app.get("/")
async def root():
    """根端点，返回服务信息"""
    return {
        "message": "金融服务接口服务器",
        "version": "1.0.0",
        "port": 8082,
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
