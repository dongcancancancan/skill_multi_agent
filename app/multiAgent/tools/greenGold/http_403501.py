"""非项目辅助识别工具 (端口8082)"""

import json
import requests
from typing import Dict
from app.utils.logger import agent_logger as logger
from app.utils.config import get_config

class NonProjectAssistTool:
    """非项目辅助识别工具类"""
    
    def __init__(self, host: str = "10.1.93.208", port: int = 8090):
        self.url = f"http://{get_config("edss_api.host") or host}:{get_config("edss_api.port") or port}/services/403501"
        self.headers = {'Content-Type': 'application/xml'}

    def execute(self, business_type: str, industry_atgreen_code: str, purpose: str, standard_type: str, current_page: int, page_size: int) -> Dict:
        """执行非项目辅助识别查询
        
        Args:
            business_type: 业务类型 (00-项目贷、01-非项目)
            industry_atgreen_code: 行业投向
            purpose: 资金用途
            standard_type: 分类标准类型 (PBOCGL-人行、CBIRCGC-银保监)
            current_page: 当前页
            page_size: 每页显示记录数
            
        Returns:
            API响应结果
        """
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <!-- "Service URL": "http://[host:port]/services/403501", "Service Name": "非项目辅助识别", "Transaction Code": "GFM0002", "Transaction Type": "null" -->
        <reqt>
            <svcHdr>                                                                    <!-- -->
                <corrId></corrId>                                                       <!-- Correlation Id 可选项 元素类型:A 长度: 精度:  备注:服务关联Id-->
                <svcId>403501</svcId>                                                   <!-- Service Id 可选项 元素类型:A 长度: 精度:  备注:服务Id-->
                <verNbr>105</verNbr>                                                    <!-- Version Number 可选项 元素类型:A 长度: 精度:  备注:服务版本号-->
                <csmrId>37500</csmrId>                                                 <!-- Consumer Id 可选项 元素类型:A 长度: 精度:  备注:服务请求方Id-->
                <csmrSerNbr>100010001000</csmrSerNbr>                                   <!-- Consumer Serial Number 可选项 元素类型:A 长度: 精度:  备注:服务请求方交易流水号-->
                <tmStamp>2011.12.29-15.00.00-218</tmStamp>                              <!-- Time stamp 可选项 元素类型:A 长度: 精度:  备注:服务访问/响应时间戳，由服务请求方/提供方填写。-->
                <reqtIp>10.1.80.185</reqtIp>                                            <!-- Request IP 可选项 元素类型:A 长度: 精度:  备注:1. 接入系统填. ( 对于维修资金,填柜员所在终端的IP)-->
            </svcHdr>
            <campHdr> <!-- -->
                <custNbr></custNbr>                                                     <!-- 备注:客户CIF号; 必输项; 类型:String 长度:19-->
                <drivTrd></drivTrd>                                                     <!-- 备注:场景识别代码; 必输项; 类型:String 长度:10-->
                <srcChlNbr></srcChlNbr>                                                 <!-- 备注:来源渠道编号; 必输项; 类型:String 长度:6-->
                <maxAmt></maxAmt>                                                       <!-- 备注:最大营销推送量; 可选项; 类型:String 长度:2-->
                <custLoc></custLoc>                                                     <!-- 备注:客戶位置信息; 可选项; 类型:String 长度:10-->
                <stepFlag>E</stepFlag>                                                  <!-- 备注:原子交易识别代码；目前固定值; 必输项; 类型:String 长度:2-->
                <custType></custType>                                                   <!-- 备注:信息类别; 必输项; 类型:String 长度:2-->
                <custUniqInfo></custUniqInfo>                                           <!-- 备注:客户识别信息; 必输项; 类型:String 长度:256-->
                <attr1></attr1>                                                         <!-- 备注:预留字段1; 必输项; 类型:String 长度:256-->
                <attr2></attr2>                                                         <!-- 备注:预留字段2; 必输项; 类型:String 长度:256-->
                <attr3></attr3>                                                         <!-- 备注:预留字段3; 必输项; 类型:String 长度:256-->
                <attr4></attr4>                                                         <!-- 备注:预留字段4; 必输项; 类型:String 长度:256-->
                <attr5></attr5>                                                         <!-- 备注:预留字段5; 必输项; 类型:String 长度:256-->
            </campHdr>
            <appHdr>
                <bsnCde>403501</bsnCde>
                <chl>AIJ</chl>
                <reqDt>20250715</reqDt>
                <reqTm>182306</reqTm>
            </appHdr>
            <appBody>
                <businessType>{business_type}</businessType>
                <industryAtgreenCode>B0620</industryAtgreenCode>
                <purpose>{purpose}</purpose>
                <standardType>{standard_type}</standardType>
                <currentPage>{current_page}</currentPage>
                <pageSize>{page_size}</pageSize>
                <res1></res1>
                <res2></res2>
                <res3></res3>
            </appBody>
        </reqt>'''
        
        response = requests.post(self.url, data=xml_data, headers=self.headers)
        response.raise_for_status()
        
        # 检查响应内容类型
        content_type = response.headers.get('content-type', '').lower()
        
        # 如果是XML响应，返回原始文本
        if 'xml' in content_type:
            logger.info("API返回XML格式响应")
            return {"raw_xml_response": response.text}
        
        # 尝试解析JSON
        return response.json()
        
   
