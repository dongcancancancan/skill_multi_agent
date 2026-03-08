"""
行政处罚核查解析器
服务ID: 400682
"""

import xml.etree.ElementTree as ET
from typing import Dict

class AdminPenaltyParser:
    """行政处罚核查解析器"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析行政处罚核查XML并生成描述文字
        
        Args:
            root: XML根元素
            
        Returns:
            行政处罚核查的描述文字
        """
        description = "企业行政处罚核查结果：\n"
        
        try:
            # 解析响应头信息
            svc_hdr = root.find('svcHdr')
            if svc_hdr is not None:
                resp_msg = svc_hdr.findtext('respMsg', '').strip()
                if resp_msg:
                    description += f"查询状态：{resp_msg}\n"
            
            # 解析应用体中的行政处罚信息
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
                    
                    # 解析行政处罚信息
                    result = data.find('result')
                    if result is not None:
                        verify_result = result.findtext('verifyresult', '').strip()
                        if verify_result:
                            description += f"核查结果：{'存在行政处罚记录' if verify_result == '1' else '无行政处罚记录'}\n"
                        
                        # 解析行政处罚数据列表 - 根据实际XML结构调整
                        penalty_count = 0
                        for data_elem in result.findall('data'):
                            penalty_count += 1
                            doc_no = data_elem.findtext('docNo', '').strip()
                            punish_reason = data_elem.findtext('punishReason', '').strip()
                            punish_result = data_elem.findtext('punishResult', '').strip()
                            punish_office = data_elem.findtext('punishOffice', '').strip()
                            punish_date = data_elem.findtext('punishDate', '').strip()
                            punish_amt = data_elem.findtext('punishAmt', '').strip()
                            data_src = data_elem.findtext('dataSrc', '').strip()
                            
                            description += f"\n处罚记录{penalty_count}：\n"
                            if doc_no:
                                description += f"  决定文书号：{doc_no}\n"
                            if punish_reason:
                                description += f"  处罚事由：{punish_reason}\n"
                            if punish_result:
                                description += f"  处罚结果：{punish_result}\n"
                            if punish_office:
                                description += f"  处罚单位：{punish_office}\n"
                            if punish_date:
                                description += f"  处罚日期：{punish_date}\n"
                            if punish_amt:
                                description += f"  处罚金额：{punish_amt}元\n"
                            if data_src:
                                description += f"  数据来源：{data_src}\n"
                        
                        if penalty_count > 0:
                            description += f"\n总计行政处罚记录：{penalty_count}条\n"
                        else:
                            description += "未找到行政处罚记录\n"
            
            return description
            
        except Exception as e:
            return f"解析行政处罚信息时发生错误：{str(e)}"
    
    def get_field_mapping(self) -> Dict[str, str]:
        """获取行政处罚核查字段映射字典
        
        Returns:
            字段映射字典，英文字段名 -> 中文描述
        """
        return {
            # 基础字段 - 根据实际XML结构调整
            "docNo": "决定文书号",
            "punishReason": "处罚事由",
            "punishResult": "处罚结果",
            "punishOffice": "处罚单位",
            "punishDate": "处罚日期",
            "punishAmt": "处罚金额",
            "dataSrc": "数据来源",
            
            # 状态字段
            "verifyresult": "核查结果",
            "status": "状态码",
            "message": "消息",
            "respMsg": "响应消息"
        }
