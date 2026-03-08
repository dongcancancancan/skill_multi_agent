"""
股权冻结核查解析器
服务ID: 400640, 400639
"""

import xml.etree.ElementTree as ET
from typing import Dict

class EquityFreezeParser:
    """股权冻结核查解析器"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析股权冻结核查XML并生成描述文字"""
        description = "企业股权冻结核查结果：\n"
        
        try:
            # 解析响应头信息
            svc_hdr = root.find('svcHdr')
            if svc_hdr is not None:
                resp_msg = svc_hdr.findtext('respMsg', '').strip()
                if resp_msg:
                    description += f"查询状态：{resp_msg}\n"
            
            # 解析应用体中的股权冻结信息
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
                    
                    # 解析股权冻结信息
                    result = data.find('result')
                    if result is not None:
                        verify_result = result.findtext('verifyresult', '').strip()
                        if verify_result:
                            description += f"核查结果：{'存在股权冻结记录' if verify_result == '1' else '无股权冻结记录'}\n"
                        
                        # 解析股权冻结数据列表
                        freeze_count = 0
                        for data_elem in result.findall('data'):
                            freeze_count += 1
                            execute_name = data_elem.findtext('executeName', '').strip()
                            execute_court = data_elem.findtext('executeCourt', '').strip()
                            equity_amount = data_elem.findtext('equityAmount', '').strip()
                            execution_notice_num = data_elem.findtext('executionNoticeNum', '').strip()
                            freeze_start_date = data_elem.findtext('freezeStartDate', '').strip()
                            freeze_end_date = data_elem.findtext('freezeEndDate', '').strip()
                            type_or_status = data_elem.findtext('typeOrStatus', '').strip()
                            
                            description += f"\n冻结记录{freeze_count}：\n"
                            if execute_name:
                                description += f"  被执行人：{execute_name}\n"
                            if execute_court:
                                description += f"  执行法院：{execute_court}\n"
                            if equity_amount:
                                description += f"  股权金额：{equity_amount}\n"
                            if execution_notice_num:
                                description += f"  执行通知书号：{execution_notice_num}\n"
                            if freeze_start_date:
                                description += f"  冻结开始日期：{freeze_start_date}\n"
                            if freeze_end_date:
                                description += f"  冻结结束日期：{freeze_end_date}\n"
                            if type_or_status:
                                description += f"  冻结类型/状态：{type_or_status}\n"
                        
                        if freeze_count > 0:
                            description += f"\n总计冻结记录：{freeze_count}条\n"
                        else:
                            description += "未找到股权冻结记录\n"
            
            return description
            
        except Exception as e:
            return f"解析股权冻结信息时发生错误：{str(e)}"
    
    def get_field_mapping(self) -> Dict[str, str]:
        """返回股权冻结字段映射字典"""
        return {
            "executeName": "被执行人",
            "executeCourt": "执行法院",
            "equityAmount": "股权金额",
            "executionNoticeNum": "执行通知书号",
            "freezeStartDate": "冻结开始日期",
            "freezeEndDate": "冻结结束日期",
            "typeOrStatus": "冻结类型/状态",
            "verifyresult": "核查结果",
            "status": "状态码",
            "message": "消息"
        }
