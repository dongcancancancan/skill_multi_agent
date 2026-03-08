"""
企查查客户身份识别解析器
服务ID: 401008
"""

import xml.etree.ElementTree as ET
from typing import Dict

class IdentityCheckParser:
    """企查查客户身份识别解析器"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析客户身份识别XML并生成描述文字"""
        description = "客户身份识别查询结果：\n"
        
        try:
            # 解析响应头信息
            svc_hdr = root.find('svcHdr')
            if svc_hdr is not None:
                resp_msg = svc_hdr.findtext('respMsg', '').strip()
                if resp_msg:
                    description += f"查询状态：{resp_msg}\n"
            
            # 解析应用体中的身份识别信息
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
                    
                    # 解析身份识别信息
                    result = data.find('result')
                    if result is not None:
                        verify_result = result.findtext('verifyResult', '').strip()
                        if verify_result:
                            description += f"核查结果：{'存在身份识别信息' if verify_result == '1' else '无身份识别信息'}\n"
                        
                        # 解析企业基本信息
                        data_element = result.find('data')
                        if data_element is not None:
                            # 解析企业基础信息
                            company_name = data_element.findtext('companyName', '').strip()
                            credit_code = data_element.findtext('creditCode', '').strip()
                            regist_capi = data_element.findtext('registCapi', '').strip()
                            lgl_repr = data_element.findtext('lglRepr', '').strip()
                            rgstr_stts = data_element.findtext('rgstrStts', '').strip()
                            start_date = data_element.findtext('startDate', '').strip()
                            address = data_element.findtext('address', '').strip()
                            scope = data_element.findtext('scope', '').strip()
                            
                            if company_name:
                                description += f"企业名称：{company_name}\n"
                            if credit_code:
                                description += f"统一社会信用代码：{credit_code}\n"
                            if regist_capi:
                                description += f"注册资本：{regist_capi}\n"
                            if lgl_repr:
                                description += f"法定代表人：{lgl_repr}\n"
                            if rgstr_stts:
                                description += f"经营状态：{rgstr_stts}\n"
                            if start_date:
                                description += f"成立日期：{start_date}\n"
                            if address:
                                description += f"注册地址：{address}\n"
                            
                            # 解析行业信息
                            industry = data_element.find('industry')
                            if industry is not None:
                                industry_desc = industry.findtext('industryDesc', '').strip()
                                sub_industry = industry.findtext('subIndustry', '').strip()
                                middle_category = industry.findtext('middleCategory', '').strip()
                                small_category = industry.findtext('smallCategory', '').strip()
                                
                                if industry_desc:
                                    description += f"行业门类：{industry_desc}\n"
                                if sub_industry:
                                    description += f"行业大类：{sub_industry}\n"
                                if middle_category:
                                    description += f"行业中类：{middle_category}\n"
                                if small_category:
                                    description += f"行业小类：{small_category}\n"
                            
                            # 解析股东信息
                            partner_list = data_element.findall('partnerList')
                            if partner_list:
                                description += "\n股东信息：\n"
                                for partner in partner_list[:5]:  # 只显示前5个股东
                                    name = partner.findtext('invesPrsnNm', '').strip()
                                    percent = partner.findtext('stockpercent', '').strip()
                                    if name and percent:
                                        description += f"  - {name}：{percent}\n"
                            
                            # 解析高管信息
                            employee_list = data_element.findall('employeeList')
                            if employee_list:
                                description += "\n高管信息：\n"
                                for employee in employee_list[:5]:  # 只显示前5个高管
                                    name = employee.findtext('name', '').strip()
                                    job = employee.findtext('job', '').strip()
                                    if name and job:
                                        description += f"  - {name}：{job}\n"
                            
                            # 解析经营范围
                            if scope:
                                description += f"\n经营范围：\n{scope}\n"
            
            return description
            
        except Exception as e:
            return f"解析客户身份识别信息时发生错误：{str(e)}"
    
    def get_field_mapping(self) -> Dict[str, str]:
        """返回字段映射字典"""
        return {
            # 基础字段
            "respMsg": "响应消息",
            "status": "状态码",
            "message": "消息",
            "verifyresult": "核查结果",
            
            # 行业信息字段
            "industryDesc": "行业门类",
            "subIndustry": "行业大类",
            "middleCategory": "行业中类",
            "smallCategory": "行业小类"
        }
