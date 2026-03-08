"""
企查查环保信用评价解析器
服务ID: 401058
"""

import xml.etree.ElementTree as ET
from typing import Dict

class EnvCreditParser:
    """环保信用评价解析器"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析环保信用评价XML并生成描述文字
        
        Args:
            root: XML根元素
            
        Returns:
            生成的描述文字
        """
        description = "企业环保信用评价查询结果：\n"
        
        try:
            # 解析响应头信息
            svc_hdr = root.find('svcHdr')
            if svc_hdr is not None:
                resp_msg = svc_hdr.findtext('respMsg', '').strip()
                if resp_msg:
                    description += f"查询状态：{resp_msg}\n"
            
            # 解析应用头信息
            app_hdr = root.find('appHdr')
            if app_hdr is not None:
                app_resp_msg = app_hdr.findtext('respMsg', '').strip()
                if app_resp_msg:
                    description += f"应用状态：{app_resp_msg}\n"
            
            # 解析应用体中的环保信用信息
            app_body = root.find('appBody')
            if app_body is not None:
                data = app_body.find('data')
                if data is not None:
                    # 解析状态信息
                    status = data.findtext('status', '').strip()
                    message = data.findtext('message', '').strip()
                    if status:
                        description += f"状态码：{status}\n"
                    if message:
                        description += f"消息：{message}\n"
                    
                    # 解析分页信息
                    paging = data.find('paging')
                    if paging is not None:
                        total_records = paging.findtext('totalRecords', '').strip()
                        if total_records:
                            description += f"总记录数：{total_records}\n"
                    
                    # 解析环保信用评价详细信息
                    results = data.findall('result')
                    if results:
                        description += "\n环保信用评价详细信息：\n"
                        for i, result in enumerate(results, 1):
                            change_date = result.findtext('changeDate', '').strip()
                            pre_level = result.findtext('preLevel', '').strip()
                            after_level = result.findtext('afterLevel', '').strip()
                            pj_org = result.findtext('pjOrg', '').strip()
                            
                            description += f"记录 {i}:\n"
                            if change_date:
                                description += f"  变更日期：{change_date}\n"
                            if pre_level:
                                description += f"  变更前等级：{pre_level}\n"
                            if after_level:
                                description += f"  变更后等级：{after_level}\n"
                            if pj_org:
                                description += f"  评价单位：{pj_org}\n"
                            description += "\n"
                    else:
                        description += "未找到环保信用评价记录\n"
            
            return description
            
        except Exception as e:
            return f"解析环保信用评价时发生错误：{str(e)}"
    
    def get_field_mapping(self) -> Dict[str, str]:
        """返回环保信用评价字段映射字典
        
        Returns:
            字段映射字典，英文字段名 -> 中文描述
        """
        return {
            "changeDate": "变更日期",
            "preLevel": "变更前等级",
            "afterLevel": "变更后等级",
            "pjOrg": "评价单位",
            "status": "状态码",
            "message": "消息",
            "respMsg": "响应消息",
            "totalRecords": "总记录数"
        }
