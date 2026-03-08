"""
经营异常核查解析器 - 直接解析XML并生成描述文字
服务ID: 400687
"""

import xml.etree.ElementTree as ET
from typing import Dict

class OperationAbnormalParser:
    """经营异常核查解析器"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析经营异常核查XML并生成描述文字"""
        description = "企业经营异常核查结果：\n"
        
        try:
            # 解析响应头信息
            svc_hdr = root.find('svcHdr')
            if svc_hdr is not None:
                resp_msg = svc_hdr.findtext('respMsg', '').strip()
                if resp_msg:
                    description += f"查询状态：{resp_msg}\n"
            
            # 解析应用体中的经营异常信息
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
                    
                    # 解析经营异常信息
                    result = data.find('result')
                    if result is not None:
                        verify_result = result.findtext('verifyresult', '').strip()
                        if verify_result:
                            description += f"核查结果：{'存在经营异常记录' if verify_result == '1' else '无经营异常记录'}\n"
                        
                        # 解析具体的经营异常数据
                        abnormal_data = result.find('data')
                        if abnormal_data is not None:
                            add_reason = abnormal_data.findtext('addReason', '').strip()
                            add_date = abnormal_data.findtext('addDate', '').strip()
                            remove_reason = abnormal_data.findtext('romoveReason', '').strip()
                            remove_date = abnormal_data.findtext('removeDate', '').strip()
                            decision_office = abnormal_data.findtext('decisionOffice', '').strip()
                            remove_decision_office = abnormal_data.findtext('removeDecisionOffice', '').strip()
                            
                            if add_reason:
                                description += f"列入原因：{add_reason}\n"
                            if add_date:
                                description += f"列入日期：{add_date}\n"
                            if decision_office:
                                description += f"决定机关：{decision_office}\n"
                            
                            if remove_reason:
                                description += f"移出原因：{remove_reason}\n"
                            if remove_date:
                                description += f"移出日期：{remove_date}\n"
                            if remove_decision_office:
                                description += f"移出决定机关：{remove_decision_office}\n"
            
            return description
            
        except Exception as e:
            return f"解析经营异常信息时发生错误：{str(e)}"
    
    def get_field_mapping(self) -> Dict[str, str]:
        """返回字段映射字典"""
        return {
            # 基础字段
            "respMsg": "响应消息",
            "status": "状态码",
            "message": "消息",
            "verifyresult": "核查结果",
            
            # 经营异常特定字段
            "addReason": "列入原因",
            "addDate": "列入日期",
            "romoveReason": "移出原因",
            "removeDate": "移出日期",
            "decisionOffice": "决定机关",
            "removeDecisionOffice": "移出决定机关"
        }
