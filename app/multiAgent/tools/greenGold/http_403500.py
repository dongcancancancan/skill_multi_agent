"""Project Green Certification Tool (Port 8082)"""

import json
import requests
from typing import Dict
from app.utils.logger import agent_logger as logger
from app.utils.config import get_config

class ProjectGreenCertificationTool:
    """Project Green Certification Tool Class"""
    
    def __init__(self, host: str = "10.1.93.208", port: int = 8090):
        self.url = f"http://{get_config("edss_api.host") or host}:{get_config("edss_api.port") or port}/services/403500"
        self.headers = {'Content-Type': 'application/xml'}

    def execute(self, business_type: str, project_name: str, project_industry_code: str, context: str, standard_type: str) -> Dict:
        """Execute project green certification query
        
        Args:
            business_type: Business type (00-project loan, 01-non-project)
            project_name: Project name
            project_industry_code: Project industry direction
            context: Construction content and scale
            standard_type: Classification standard type (PBOCGL-PBOC, CBIRCGC-CBIRC)
            
        Returns:
            API response result
        """
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <!-- "Service URL": "http://[host:port]/services/403500", "Service Name": "项目绿色认定", "Transaction Code": "GFM0001", "Transaction Type": "null" -->
        <reqt>
            <svcHdr>                                                                    <!-- -->
                <corrId></corrId>                                                       <!-- Correlation Id 可选项 元素类型:A 长度: 精度:  备注:服务关联Id-->
                <svcId>403500</svcId>                                                   <!-- Service Id 可选项 元素类型:A 长度: 精度:  备注:服务Id-->
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
            <appHdr>                                                                    <!-- -->
                <bsnCde></bsnCde>                                                       <!-- 交易代码 必输项 元素类型:string 长度:6.0 精度:0  备注:交易代码;上送：ED1001-->
                <chl></chl>                                                             <!-- 渠道标识 必输项 元素类型:string 长度:3 精度:0  备注:渠道标识 ;9:ESB-->
                <reqDt></reqDt>                                                         <!-- 渠道日期 可选项 元素类型:string 长度:8.0 精度:0  备注:渠道日期-->
                <reqTm></reqTm>                                                         <!-- 渠道时间 可选项 元素类型:string 长度:6.0 精度:0  备注:渠道时间-->
            </appHdr>
            <appBody>
                <businessType>{business_type}</businessType>
                <projectName>{project_name}</projectName>
                <projectIndustryCode>{project_industry_code}</projectIndustryCode>
                <context>{context}</context>
                <standardType>{standard_type}</standardType>
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
        return response.json()
        
            
        
