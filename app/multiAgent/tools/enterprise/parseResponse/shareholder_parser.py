"""
股东信息工商登记解析器 - 服务ID: 401015
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any


class ShareholderInfoParser:
    """股东信息工商登记解析器"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析股东信息XML并生成描述文字"""
        description = "企业股东信息查询结果：\n"
        
        try:
            # 解析响应头信息
            svc_hdr = root.find('svcHdr')
            if svc_hdr is not None:
                resp_msg = svc_hdr.findtext('respMsg', '').strip()
                if resp_msg:
                    description += f"查询状态：{resp_msg}\n"
            
            # 解析应用体中的股东信息
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
                    
                    # 解析股东信息
                    result = data.find('result')
                    if result is not None:
                        verify_result = result.findtext('verifyresult', '').strip()
                        if verify_result:
                            description += f"核查结果：{'存在股东信息' if verify_result == '1' else '无股东信息'}\n"
                        
                        # 解析股东列表
                        regstock_info = result.find('data/regstockInfo')
                        if regstock_info is not None:
                            shareholder_count = 0
                            for regstock_list in regstock_info.findall('regstockList'):
                                shareholder_count += 1
                                inves_prsn_nm = regstock_list.findtext('invesPrsnNm', '').strip()
                                should_capi = regstock_list.findtext('shouldCapi', '').strip()
                                inves_prsn_typ = regstock_list.findtext('invesPrsnTyp', '').strip()
                                stock_percent = regstock_list.findtext('stockpercent', '').strip()
                                shoud_date = regstock_list.findtext('shouddate', '').strip()
                                
                                description += f"\n股东{shareholder_count}：\n"
                                if inves_prsn_nm:
                                    description += f"  股东姓名：{inves_prsn_nm}\n"
                                if should_capi:
                                    description += f"  认缴出资额：{should_capi}万元\n"
                                if stock_percent:
                                    description += f"  持股比例：{stock_percent}\n"
                                if inves_prsn_typ:
                                    description += f"  股东类型：{inves_prsn_typ}\n"
                                if shoud_date:
                                    description += f"  认缴日期：{shoud_date}\n"
                            
                            if shareholder_count > 0:
                                description += f"\n总计股东数量：{shareholder_count}位\n"
                            else:
                                description += "未找到股东信息\n"
            
            return description
            
        except Exception as e:
            return f"解析股东信息时发生错误：{str(e)}"
    
    def get_field_mapping(self) -> Dict[str, str]:
        """获取字段映射字典"""
        return {
            # 基础字段
            "invesPrsnNm": "股东姓名",
            "shouldCapi": "认缴出资额",
            "invesPrsnTyp": "股东类型", 
            "stockpercent": "持股比例",
            "shouddate": "认缴日期",
            
            # 响应字段
            "respMsg": "查询状态",
            "status": "状态码",
            "message": "消息",
            "verifyresult": "核查结果"
        }
