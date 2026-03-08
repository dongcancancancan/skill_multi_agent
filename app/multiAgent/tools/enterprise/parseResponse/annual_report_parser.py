"""
企业年报信息解析器
服务ID: 400690
"""

import xml.etree.ElementTree as ET
from typing import Dict, List

class AnnualReportParser:
    """企业年报信息解析器"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析企业年报信息XML并生成描述文字"""
        description = "企业年报信息查询结果：\n"
        
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
            
            # 解析应用体中的年报信息
            app_body = root.find('appBody')
            if app_body is not None:
                data = app_body.find('data')
                if data is not None:
                    # 解析状态信息
                    status = data.findtext('status', '').strip()
                    message = data.findtext('message', '').strip()
                    order_number = data.findtext('orderNumber', '').strip()
                    if status:
                        description += f"状态码：{status}\n"
                    if message:
                        description += f"消息：{message}\n"
                    if order_number:
                        description += f"订单号：{order_number}\n"
                    
                    # 解析年报详细信息
                    result = data.find('result')
                    if result is not None:
                        description += self._parse_result_details(result)
            
            return description
            
        except Exception as e:
            return f"解析企业年报信息时发生错误：{str(e)}"
    
    def _parse_result_details(self, result: ET.Element) -> str:
        """解析年报详细信息"""
        description = ""
        
        # 解析基本信息
        resp_year = result.findtext('respYear', '').strip()
        remarks = result.findtext('remarks', '').strip()
        has_detail_info = result.findtext('hasDetailInfo', '').strip()
        publish_date = result.findtext('publishDate', '').strip()
        
        if resp_year:
            description += f"报送年度：{resp_year}\n"
        if remarks:
            description += f"备注：{remarks}\n"
        if has_detail_info:
            description += f"是否有详细信息：{has_detail_info}\n"
        if publish_date:
            description += f"发布日期：{publish_date}\n"
        
        # 解析企业基本信息
        basic_info = result.find('basicInfoData')
        if basic_info is not None:
            description += self._parse_basic_info(basic_info)
        
        # 解析企业资产状况信息
        assets_data = result.find('assetsData')
        if assets_data is not None:
            description += self._parse_assets_data(assets_data)
        
        # 解析股东及出资信息
        partner_list = result.find('partnerList')
        if partner_list is not None:
            description += self._parse_partner_list(partner_list)
        
        # 解析对外投资信息
        invest_info_list = result.find('investInfoList')
        if invest_info_list is not None:
            description += self._parse_invest_info_list(invest_info_list)
        
        # 解析员工信息
        employee_list = result.find('employeeList')
        if employee_list is not None:
            description += self._parse_employee_list(employee_list)
        
        return description
    
    def _parse_basic_info(self, basic_info: ET.Element) -> str:
        """解析企业基本信息"""
        description = "\n企业基本信息：\n"
        
        fields = {
            'regNo': '注册号',
            'entName': '企业名称',
            'creditCode': '统一社会信用代码',
            'operatorName': '经营者姓名',
            'contactNo': '企业联系电话',
            'postCode': '邮政编码',
            'rAddress': '企业通信地址',
            'email': '邮箱',
            'isStockRightTransfer': '是否发生股东股权转让',
            'jyStatus': '企业经营状态',
            'hasNewStockOrByStock': '是否有投资信息或购买其他公司股权',
            'operationPlaces': '经营场所',
            'mainType': '主体类型',
            'operationDuration': '经营期限',
            'ifContentSame': '章程信息是否一致',
            'differentContent': '章程信息不一致内容',
            'generalOperationItem': '经营范围(一般经营项目)',
            'approvedOperationItem': '经营范围(许可经营项目)'
        }
        
        for field, label in fields.items():
            value = basic_info.findtext(field, '').strip()
            if value and value != "企业年报":  # 过滤掉示例数据
                description += f"  {label}：{value}\n"
        
        return description
    
    def _parse_assets_data(self, assets_data: ET.Element) -> str:
        """解析企业资产状况信息"""
        description = "\n企业资产状况信息：\n"
        
        fields = {
            'totalAssets': '资产总额',
            'totalOwnersEquityte': '所有者权益合计',
            'grossTradingIncome': '营业总收入',
            'totalProfit': '利润总额',
            'mainBusinessIncome': '主营业务收入',
            'netProfite': '净利润',
            'totalTaxAmount': '纳税总额',
            'totalLiabilities': '负债总额',
            'bankingCredit': '金融贷款',
            'governmentSubsidyCredit': '获得政府扶持资金、补助'
        }
        
        for field, label in fields.items():
            value = assets_data.findtext(field, '').strip()
            if value and value != "企业年报":  # 过滤掉示例数据
                description += f"  {label}：{value}\n"
        
        return description
    
    def _parse_partner_list(self, partner_list: ET.Element) -> str:
        """解析股东及出资信息"""
        description = "\n股东及出资信息：\n"
        partners = partner_list.findall('.')
        
        for i, partner in enumerate(partners, 1):
            name = partner.findtext('name', '').strip()
            should_capi = partner.findtext('shouldCapi', '').strip()
            should_date = partner.findtext('shouldDate', '').strip()
            should_type = partner.findtext('shouldTypetSubsidyCredit', '').strip()
            real_capi = partner.findtext('realCapi', '').strip()
            real_date = partner.findtext('realDate', '').strip()
            real_type = partner.findtext('realType', '').strip()
            
            if name or should_capi or real_capi:
                description += f"  股东{i}：\n"
                if name:
                    description += f"    名称：{name}\n"
                if should_capi and should_capi != "企业年报":
                    description += f"    认缴出资额：{should_capi}\n"
                if should_date:
                    description += f"    认缴出资时间：{should_date}\n"
                if should_type:
                    description += f"    认缴出资方式：{should_type}\n"
                if real_capi:
                    description += f"    实缴出资额：{real_capi}\n"
                if real_date:
                    description += f"    实缴出资时间：{real_date}\n"
                if real_type:
                    description += f"    实缴出资方式：{real_type}\n"
        
        return description
    
    def _parse_invest_info_list(self, invest_info_list: ET.Element) -> str:
        """解析对外投资信息"""
        description = "\n对外投资信息：\n"
        investments = invest_info_list.findall('.')
        
        for i, investment in enumerate(investments, 1):
            name = investment.findtext('name', '').strip()
            reg_no = investment.findtext('regNo', '').strip()
            should_capi = investment.findtext('shouldCapi', '').strip()
            stock_percent = investment.findtext('stockpercent', '').strip()
            
            if name or reg_no or should_capi:
                description += f"  投资{i}：\n"
                if name and name != "企业年报":
                    description += f"    企业名称：{name}\n"
                if reg_no:
                    description += f"    注册号：{reg_no}\n"
                if should_capi:
                    description += f"    认缴出资额：{should_capi}\n"
                if stock_percent:
                    description += f"    持股比例：{stock_percent}\n"
        
        return description
    
    def _parse_employee_list(self, employee_list: ET.Element) -> str:
        """解析员工信息"""
        description = "\n工商登记主要人员信息：\n"
        employees = employee_list.findall('.')
        
        for i, employee in enumerate(employees, 1):
            name = employee.findtext('name', '').strip()
            e_job = employee.findtext('eJob', '').strip()
            cer_no = employee.findtext('cerNo', '').strip()
            scert_name = employee.findtext('scertName', '').strip()
            
            if name or e_job:
                description += f"  人员{i}：\n"
                if name and name != "企业年报":
                    description += f"    姓名：{name}\n"
                if e_job:
                    description += f"    职位：{e_job}\n"
                if cer_no:
                    description += f"    证件号码：{cer_no}\n"
                if scert_name:
                    description += f"    证件名称：{scert_name}\n"
        
        return description
    
    def get_field_mapping(self) -> Dict[str, str]:
        """返回字段映射字典"""
        return {
            "respYear": "报送年度",
            "remarks": "备注",
            "hasDetailInfo": "是否有详细信息",
            "publishDate": "发布日期",
            "status": "状态码",
            "message": "消息",
            "respMsg": "查询状态"
        }
