"""
环保处罚核查解析器
服务ID: 400637 - 环保处罚核查
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any

class EnvPenaltyParser:
    """环保处罚核查解析器"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析环保处罚核查XML并生成描述文字
        
        Args:
            root: XML根元素
            
        Returns:
            生成的描述文字
        """
        description = "企业环保处罚核查结果：\n"
        
        try:
            # 解析响应头信息
            svc_hdr = root.find('svcHdr')
            if svc_hdr is not None:
                resp_msg = svc_hdr.findtext('respMsg', '').strip()
                if resp_msg:
                    description += f"查询状态：{resp_msg}\n"
            
            # 解析应用体中的环保处罚信息
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
                    
                    # 解析环保处罚信息
                    result = data.find('result')
                    if result is not None:
                        verify_result = result.findtext('verifyresult', '').strip()
                        if verify_result:
                            description += f"核查结果：{'存在环保处罚记录' if verify_result == '1' else '无环保处罚记录'}\n"
                        
                        # 解析环保处罚数据列表
                        penalty_count = 0
                        for data_elem in result.findall('data'):
                            penalty_count += 1
                            case_no = data_elem.findtext('caseNo', '').strip()
                            punish_date = data_elem.findtext('punishDate', '').strip()
                            punish_gov = data_elem.findtext('punishGov', '').strip()
                            illegal_type = data_elem.findtext('illegalType', '').strip()
                            
                            description += f"\n处罚记录{penalty_count}：\n"
                            if case_no:
                                description += f"  案件文号：{case_no}\n"
                            if punish_date:
                                description += f"  处罚日期：{punish_date}\n"
                            if punish_gov:
                                description += f"  处罚机关：{punish_gov}\n"
                            if illegal_type:
                                description += f"  违法类型：{illegal_type}\n"
                        
                        if penalty_count > 0:
                            description += f"\n总计处罚记录：{penalty_count}条\n"
                        else:
                            description += "未找到环保处罚记录\n"
            
            return description
            
        except Exception as e:
            return f"解析环保处罚信息时发生错误：{str(e)}"
    
    def get_field_mapping(self) -> Dict[str, str]:
        """返回环保处罚核查字段映射字典"""
        return {
            # 基础字段
            "caseNo": "案件文号",
            "punishDate": "处罚日期",
            "punishGov": "处罚机关",
            "illegalType": "违法类型",
            
            # 状态字段
            "verifyresult": "核查结果",
            "status": "状态码",
            "message": "消息",
            
            # 响应头字段
            "respMsg": "查询状态"
        }
