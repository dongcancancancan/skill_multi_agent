"""
环保处罚详情解析器 - 服务ID: 400604
直接解析环保处罚详情XML并生成描述文字
"""

import xml.etree.ElementTree as ET
from typing import Dict

class EnvironmentalPenaltyDetailParser:
    """环保处罚详情解析器"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析环保处罚详情XML并生成描述文字"""
        description = "企业环保处罚详情查询结果：\n"
        
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
                            penalty_no = data_elem.findtext('penaltyNo', '').strip()
                            penalty_amount = data_elem.findtext('penaltyAmount', '').strip()
                            penalty_date = data_elem.findtext('penaltyDate', '').strip()
                            penalty_authority = data_elem.findtext('penaltyAuthority', '').strip()
                            penalty_reason = data_elem.findtext('penaltyReason', '').strip()
                            
                            description += f"\n处罚记录{penalty_count}：\n"
                            if penalty_no:
                                description += f"  处罚文号：{penalty_no}\n"
                            if penalty_amount:
                                description += f"  处罚金额：{penalty_amount}元\n"
                            if penalty_date:
                                description += f"  处罚日期：{penalty_date}\n"
                            if penalty_authority:
                                description += f"  处罚机关：{penalty_authority}\n"
                            if penalty_reason:
                                description += f"  处罚事由：{penalty_reason}\n"
                        
                        if penalty_count > 0:
                            description += f"\n总计处罚记录：{penalty_count}条\n"
                        else:
                            description += "未找到环保处罚记录\n"
            
            return description
            
        except Exception as e:
            return f"解析环保处罚信息时发生错误：{str(e)}"
    
    def get_field_mapping(self) -> Dict[str, str]:
        """返回环保处罚详情字段映射字典"""
        return {
            "penaltyNo": "处罚文号",
            "penaltyAmount": "处罚金额",
            "penaltyDate": "处罚日期",
            "penaltyAuthority": "处罚机关",
            "penaltyReason": "处罚事由",
            "verifyresult": "核查结果",
            "status": "状态码",
            "message": "消息",
            "respMsg": "查询状态"
        }
