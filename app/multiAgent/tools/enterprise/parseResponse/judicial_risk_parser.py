"""
司法风险企业画像解析器 - 直接解析XML并生成描述文字
服务ID: 400631
"""

import xml.etree.ElementTree as ET
from typing import Dict

class JudicialRiskParser:
    """司法风险企业画像解析器"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析司法风险企业画像XML并生成描述文字"""
        description = "企业司法风险画像查询结果：\n"
        
        try:
            # 解析响应头信息
            svc_hdr = root.find('svcHdr')
            if svc_hdr is not None:
                resp_msg = svc_hdr.findtext('respMsg', '').strip()
                if resp_msg:
                    description += f"查询状态：{resp_msg}\n"
            
            # 解析应用体中的司法风险信息
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
                    
                    # 解析司法风险数据
                    resp_body = data.find('respBody')
                    if resp_body is not None:
                        pd_flag = resp_body.findtext('pdFlag', '').strip()
                        if pd_flag:
                            description += f"查得标识：{'查得风险信息' if pd_flag == '1.0' else '未查得风险信息'}\n"
                        
                        # 解析风险内容
                        pd_data = resp_body.find('pdData')
                        if pd_data is not None:
                            serialnum = pd_data.findtext('serialnum', '').strip()
                            fxmsgnum = pd_data.findtext('fxmsgnum', '').strip()
                            fxpgnum = pd_data.findtext('fxpgnum', '').strip()
                            
                            if serialnum:
                                description += f"请求流水号：{serialnum}\n"
                            if fxmsgnum:
                                description += f"风险信息条数：{fxmsgnum}条\n"
                            if fxpgnum:
                                description += f"风险信息页数：{fxpgnum}页\n"
                            
                            # 解析各类风险信息
                            fxcontent = pd_data.find('fxcontent')
                            if fxcontent is not None:
                                risk_types = {
                                    'shixin': '失信被执行人',
                                    'xiangao': '限制高消费',
                                    'zhixing': '执行公开',
                                    'caipan': '民商事裁判文书',
                                    'shenpan': '民商事审判流程',
                                    'weifa': '行政违法',
                                    'qiankuan': '或有负债',
                                    'feizheng': '纳税非正常户',
                                    'zuifan': '罪犯及嫌疑人',
                                    'xianchu': '限制出入境'
                                }
                                
                                for risk_key, risk_name in risk_types.items():
                                    risk_records = fxcontent.findall(risk_key)
                                    if risk_records:
                                        description += f"\n{risk_name}信息（{len(risk_records)}条）：\n"
                                        for i, record in enumerate(risk_records, 1):
                                            title = record.findtext('titl', '').strip()
                                            register_time = record.findtext('rgstrTm', '').strip()
                                            amount = record.findtext('invldAmt', '').strip()
                                            court = record.findtext('exctCrt', '').strip()
                                            status_text = record.findtext('rcvTimeCaseStts', '').strip()
                                            
                                            description += f"  第{i}条记录：\n"
                                            if title:
                                                description += f"    标题：{title}\n"
                                            if register_time:
                                                description += f"    立案时间：{register_time}\n"
                                            if amount:
                                                description += f"    涉案金额：{amount}元\n"
                                            if court:
                                                description += f"    执行法院：{court}\n"
                                            if status_text:
                                                description += f"    案件状态：{status_text}\n"
            
            return description
            
        except Exception as e:
            return f"解析司法风险信息时发生错误：{str(e)}"
    
    def get_field_mapping(self) -> Dict[str, str]:
        """返回司法风险字段映射字典"""
        return {
            # 基础司法风险字段
            "serialnum": "序列号",
            "fxmsgnum": "风险消息编号",
            "fxpgnum": "风险页面编号",
            
            # 通用司法风险字段
            "caseNo": "案件号",
            "caseName": "案件名称",
            "court": "执行法院",
            "amount": "涉案金额",
            "status": "执行状态",
            "filingDate": "立案时间",
            "closingDate": "结案时间",
            "executionSubject": "执行标的",
            "executionCourt": "执行法院",
            "executionDate": "执行日期",
            "executionStatus": "执行状态",
            
            # 失信被执行人字段
            "dishonestPerson": "失信被执行人",
            "performanceStatus": "履行情况",
            "specificCircumstances": "具体情形",
            "releaseDate": "发布时间",
            "province": "省份",
            "executionBasis": "执行依据文号",
            
            # 限制高消费字段
            "restrictedPerson": "限制消费人员",
            "restrictionContent": "限制内容",
            "restrictionPeriod": "限制期限",
            "restrictionCourt": "限制法院",
            "restrictionDate": "限制日期",
            
            # 执行公开字段
            "executionCaseNo": "执行案号",
            "executionApplicant": "申请执行人",
            "executedPerson": "被执行人",
            "executionAmount": "执行金额",
            "executionResult": "执行结果",
            
            # 裁判文书字段
            "judgmentNo": "裁判文书号",
            "judgmentCourt": "裁判法院",
            "judgmentDate": "裁判日期",
            "judgmentType": "裁判类型",
            "judgmentResult": "裁判结果",
            
            # 审判流程字段
            "trialCaseNo": "审判案号",
            "trialCourt": "审判法院",
            "trialStage": "审判阶段",
            "trialDate": "审判日期",
            "trialStatus": "审判状态",
            
            # 行政违法字段
            "penaltyNo": "处罚决定书文号",
            "penaltyAuthority": "处罚机关",
            "penaltyDate": "处罚日期",
            "penaltyContent": "处罚内容",
            "penaltyAmount": "处罚金额",
            
            # 或有负债字段
            "debtAmount": "负债金额",
            "debtType": "负债类型",
            "debtDate": "负债日期",
            "creditor": "债权人",
            "debtStatus": "负债状态",
            
            # 纳税非正常户字段
            "abnormalDate": "非正常户认定日期",
            "abnormalReason": "非正常户原因",
            "abnormalStatus": "非正常户状态",
            "taxAuthority": "税务机关",
            
            # 罪犯及嫌疑人字段
            "criminalName": "罪犯姓名",
            "crimeType": "犯罪类型",
            "sentence": "判决结果",
            "sentenceDate": "判决日期",
            "prisonTerm": "刑期",
            
            # 限制出入境字段
            "restrictedPersonName": "限制人员姓名",
            "restrictionType": "限制类型",
            "restrictionStartDate": "限制开始日期",
            "restrictionEndDate": "限制结束日期",
            "restrictionAuthority": "限制机关",
            
            # 从XML文档中提取的英文字段映射
            "dataOrgnlPK": "数据原始主键",
            "typet": "数据原始类别编号",
            "dataTyp": "数据类型",
            "csNoDtls": "案号详情",
            "exctCsNo": "执行案号",
            "titl": "标题",
            "rgstrTm": "立案时间",
            "nptNo": "输入的证件号码",
            "exctCrt": "执行法院",
            "invldAmt": "涉案金额(元)",
            "exctCntnt": "执行内容",
            "rcvTimeCaseStts": "收录时案件状态",
            "dssntRmrk": "异议备注",
            "prtyPrvnc": "当事人省份",
            "bnkSttn": "履行情况",
            "spcfc": "具体情形",
            "pblshTm": "发布时间",
            "exctBssDocNo": "执行依据文号",
            "outExctBssUnit": "做出执行依据单位",
            "thsDt": "终本日期",
            "notBnkAmt": "未履行金额(元)",
            "applyExctr": "申请执行人",
            "wbstStts": "网站状态",
            "dssntCmplntStts": "异议申诉状态",
            "evntBnkStts": "事件履行状态",
            "crdtStts": "信用修复状态",
            "accuracy": "匹配度",
            "nptNm": "输入的名称",
            "cncldDt": "审结日期",
            "ltgtnStts": "诉讼地位",
            "trlCrt": "审理法院",
            "psNgt": "正负面",
            "paperTyp": "文书类型",
            "thCsBy": "案由",
            "trlRslt": "审理结果",
            "trlPrgrm": "审理程序",
            "caseTyp": "案件类型",
            "trlPers": "审理人员",
            "cmpltCntntChckAddr": "完整内容查看地址",
            "plainPrty": "原告当事人",
            "defenPrty": "被告当事人",
            "othrPrty": "其他当事人",
            "lwyrNm": "律师姓名",
            "lwfrmsNm": "律所名称",
            "spcfcDt": "具体日期",
            "csNo": "案号",
            "trlOffc": "审理机关",
            "annoTyp": "公告类型",
            "annoCntnt": "公告内容",
            "dtCtgry": "日期类别",
            "plain": "原告",
            "iwEnfOffc": "执法/复议/审判机关",
            "illglRsn": "违法事由",
            "mnyAmt": "金额(元)",
            "admiLwEnfRslt": "行政执法结果",
            "orHaveDebtIdent": "或有负债方身份",
            "orHaveDebtRsn": "或有负债原因",
            "orHaveDebtAmt": "或有负债金额(元)",
            "statTm": "统计日期",
            "idntfDt": "认定日期",
            "drctrTaxOffc": "主管税务机关",
            "cntnt": "内容",
            "txpyrStts": "纳税人状态",
            "instPChrgNm": "法定代表人或负责人姓名",
            "oprtPlc": "经营地点",
            "paperDocNo": "文书文号",
            "illglRsn": "违法事由",
            "judgmRslt": "判决结果",
            "judgmPrd": "刑期",
            "exctAmt": "执行金额(元)",
            "pdResultId": "朴道查询流水号",
            "pdFlag": "查得标识",
            "pdData": "数据源原始报文",
            "fxcontent": "风险内容模块",
            "fxpgturn": "风险分页模块",
            "fxnavigate": "导航参数",
            "prepage": "上页",
            "nexpage": "下页",
            "pg": "页码",
            "url": "访问URL",
            "para": "参数",
            "num": "条数"
        }
