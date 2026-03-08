"""
企业基本信息查询工具模块
提供对los_ent_info表的查询功能 - PostgreSQL版本
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.multiAgent.common.postgresql_connection import PostgreSQLConnection
from langchain_core.tools import tool
from app.utils.logger import agent_logger as logger
from langgraph.types import interrupt
from app.multiAgent.tools.enterprise.xml_api_tool import xml_api_tool
from app.multiAgent.common.tool_decorator import with_error_handling
from app.multiAgent.common.error_categories import ToolUserError
from app.multiAgent.tools.enterprise.xml_builder import XMLBuilder
from app.multiAgent.tools.common import send_progress_info, send_citation_info


class EnterpriseBasicInfoTool:
    """企业基本信息查询工具类 - PostgreSQL版本"""

    def __init__(self):
        self.db = PostgreSQLConnection()
        # 支持PostgreSQL
        self.db_type = "postgresql"

    def query_by_company_name_credit_code(
        self, company_name: str, credit_code: str
    ) -> Dict[str, Any]:
        """根据企业名称查询综合信息 - 包含企业基本信息、债券评级和评级机构"""
        results = {}

        # 查询企业基本信息
        if company_name or credit_code:
            basic_info = self.query_enterprise_basic_info(company_name, credit_code)
            # 添加来源标记
            if basic_info:
                for item in basic_info:
                    item["_source"] = "数据库表: los_ent_info"
            results["basic_info"] = basic_info
            if not basic_info:
                return results

            # 如果找到多个企业，直接返回结果让上层处理
            if len(basic_info) > 1:
                return results

        # 查询债券发行主体信用评级
        if (
            company_name
            and results.get("basic_info")
            and len(results["basic_info"]) == 1
        ):
            bond_rating = self.query_bond_issuer_rating(company_name)
            # 添加来源标记
            if bond_rating:
                for item in bond_rating:
                    item["_source"] = "数据库表: cbondissuerrating"
            results["bond_rating"] = bond_rating

        # 查询债券评级机构
        rating_agencies = self.query_rating_agencies()
        # 添加来源标记
        if rating_agencies:
            for item in rating_agencies:
                item["_source"] = "数据库表: cbondratingdefinition"
        results["rating_agencies"] = rating_agencies

        return results

    def query_enterprise_basic_info(
        self, company_name: str, credit_code: str
    ) -> List[Dict[str, Any]]:
        """查询企业基本信息 - PostgreSQL专用"""
        where_conditions = []
        params = []

        if company_name:
            where_conditions.append("enterprisename LIKE %s")
            params.append(f"%{company_name}%")

        if (
            credit_code
            and len(credit_code) == 18
            and re.match(r"^[A-Z0-9]{18}$", credit_code)
        ):
            where_conditions.append("uscreditcode LIKE %s")
            params.append(f"%{credit_code}%")

        where_clause = ""
        if where_conditions:
            where_clause = f"WHERE {' OR '.join(where_conditions)}"

        query = f"""
            SELECT 
                sysid AS 系统简称,
                customerid AS 客户编号,
                corpid AS 法人或组织机构代码,
                enterprisename AS 企业名称,
                englishname AS 客户英文名称,
                fictitiousperson AS 法人代表,
                orgnature AS 机构类型,
                financetype AS 金融机构类型,
                enterprisebelong AS 企业隶属,
                industrytype AS 行业类型,
                industrytype1 AS 行业类型1,
                industrytype2 AS 行业类型2,
                private AS 民营标志,
                economytype AS 经济类型,
                orgtype AS 组织形式,
                mostbusiness AS 主营业务,
                budgettype AS 预算管理类型,
                rccurrency AS 注册资本币种,
                registercapital AS 注册资本,
                pccurrency AS 实收资本币种,
                paiclupcapital AS 实收资本,
                fundsource AS 经费来源,
                totalassets AS 总资产,
                netassets AS 净资产,
                annualincome AS 年收入,
                scope AS 企业规模,
                myscope AS 修改前企业规模,
                limit1 AS 额度,
                creditdate AS 首次建立信贷关系年月,
                licenseno AS 工商执照登记号,
                licensedate AS 工商执照登记日期,
                licensematurity AS 工商执照到期日,
                enddate AS 证件到期日,
                setupdate AS 公司成立日期,
                inspectionyear AS 工商执照最新年检年份,
                locksituation AS 工商局锁定情况,
                taxno AS 税务登记号（国税）,
                banklicense AS 金融机构许可证,
                bankid AS 金融机构代码,
                managearea AS 金融机构经营区域范围,
                banchamount AS 金融机构一级分支机构数量,
                exchangeid AS 交换号,
                countrycode AS 办公地址所在国家地区,
                regioncode AS 办公地址所在行政区域,
                officeadd AS 办公地址,
                officecountrycode AS 注册地址所在国家地区,
                officeregioncode AS 注册地址所在行政区域,
                registeradd AS 注册地址,
                chargedepartment AS 上级主管部门,
                officezip AS 邮政编码,
                villagecode AS 所属行政村编号,
                relativetype AS 联系方式,
                officetel AS 联系电话,
                officefax AS 传真号码,
                webadd AS 公司网址,
                emailadd AS 公司邮件地址,
                employeenumber AS 员工人数,
                mainproduction AS 主要产品和服务情况,
                listingcorpornot AS 是否上市企业,
                hasieright AS 由无进出口经营权,
                hasdirectorate AS 有无董事会,
                mainbank AS 主要结算行,
                basicbank AS 基本帐户行,
                basicaccount AS 基本帐户号,
                manageinfo AS 合法经营情况,
                customerhistory AS 客户历史沿革、管理水平简介,
                projectflag AS 企业目前是否有项目,
                realtyflag AS 是否从事房地产开发,
                workfieldarea AS 经营场地面积,
                workfieldfee AS 经营场地所有权,
                accountdate AS 开户时间,
                loancardno AS 贷款卡号,
                loancardpassword AS 贷款卡密码,
                loancardinsyear AS 贷款卡最新年审年份,
                loancardinsresult AS 贷款卡最新年审结果,
                loanflag AS 贷款卡是否有效,
                financeornot AS 是否无须提供财务报表,
                financebelong AS 财务报表所属,
                evaluatedate AS 本行评估日期,
                othercreditlevel AS 外部机构评估信用等级,
                otherevaluatedate AS 外部机构评估日期,
                otherorgname AS 外部评级机构名称,
                inputorgid AS 登记单位,
                inputuserid AS 登记人,
                inputdate AS 登记日期,
                updateorgid AS 更新机构,
                updateuserid AS 更新人,
                updatedate AS 更新日期,
                taxno1 AS 税务登记号（地税）,
                fictitiouspersonid AS 法人代表身份证,
                groupflag AS 是否关联集团,
                evaluatelevel AS 信用等级认定级别,
                mybank AS 我行账户行,
                mybankaccount AS 我行帐号,
                otherbank AS 他行账户行,
                otherbankaccount AS 他行帐号,
                tempsaveflag AS 暂存标志,
                financedepttel AS 财务部联系方式,
                ecgroupflag AS 是否集团客户,
                belonggroupname AS 所属集团,
                supercorpname AS 上级公司名称,
                superloancardno AS 上级公司贷款卡号,
                supercerttype AS 上级公司证件类型,
                supercertid AS 上级公司证件编号,
                sellsum AS SELLSUM,
                smeindustrytype AS SMEINDUSTRYTYPE,
                rwscheckstatus AS 客户预警状态,
                isconfirm AS 是否预警认定中,
                totalbalance AS 业务总余额,
                totalexposure AS 业务总敞口,
                lowestclassifylevel AS 资产分类最低等级,
                statetype AS 国别,
                swiftcode AS SWIFT代码,
                aliketype AS 同业类型,
                aliketypedown AS 同业子类型,
                isfinancingcustomer AS 是否政府融资平台,
                ishightech AS 是否高新技术行业,
                isnonlocal AS 是否异地客户,
                simplename AS 客户简称,
                licensesymbol AS 营业执照年检标志,
                licensetime AS 营业执照年检时间,
                limitflag AS 是否限制性行业,
                userdefineflag AS 是否重点监测客户,
                entholdingtype AS 企业控股类型,
                stockholderflag AS 是否本行股东,
                countryflag AS 注册地是否在农村,
                ficilitycredit AS 机构信用代码,
                corporatebondsflag AS 是否企业债客户,
                corpmaturity AS 组织机构代码到期日,
                creditmaturity AS 机构信用代码到期日,
                islongterm AS 营业执照是否长期有效,
                registeraddupdatedate AS 注册地址更新日期,
                officeaddupdatedate AS 办公地址更新日期,
                corpidupdatedate AS 组织机构代码更新日期,
                agencylicenseupdatedate AS 营业执照更新日期,
                villagename AS 所属行政村名称,
                newtechcorpornot AS 是否高新技术企业,
                technologyflag AS 是否科技型企业,
                isimportandexport AS 是否进出口企业,
                shflag AS 双惠标识,
                customertypelevel AS 客户类型级别,
                isthreecert AS 三证合一标示,
                ingrade AS 内部评级,
                outgrade AS 外部评级,
                effectstatus AS 准入状态,
                myscopesource AS 修改前企业规模,
                applygrade AS 申请人等级,
                remark AS 备注,
                street AS 街道,
                uscreditcode AS 统一社会信用代码,
                basicbankno AS 基本户开户行号,
                ispreipocompanie AS 是否拟上市企业,
                isdevelopzone AS 是否开发区,
                developzone AS 开发区,
                racaddress AS 居委会地址,
                tx_dt AS 数据日期
            FROM los_ent_info 
            {where_clause}
            ORDER BY setupdate DESC
        """
        logger.info(f"企业基本信息查询语句：{query}")
        logger.info(f"查询参数：{params}")

        results = self.db.execute_query(query, params)

        # 处理Decimal类型，确保可以JSON序列化
        processed_results = []
        for result in results:
            processed_result = {}
            for key, value in result.items():
                if hasattr(value, "__class__") and "Decimal" in str(value.__class__):
                    # 将Decimal转换为float或str
                    processed_result[key] = float(value)
                else:
                    processed_result[key] = value
            processed_results.append(processed_result)

        return processed_results

    def query_bond_issuer_rating(self, company_name: str) -> List[Dict[str, Any]]:
        """查询企业债券发行主体信用评级"""
        if not company_name:
            return []

        query = """
            SELECT 
                objct_id AS 对象ID,
                cocn_nm AS 公司中文名称,
                rat_dt AS 评级日期,
                rattyp AS 评级类型,
                crdtrat AS 信用评级,
                ratotlk AS 信用评级,
                ratinst_id AS 评级机构代码,
                bndsbjctco_id AS 债券主体公司id,
                crdtratdscr AS 信用评级说明,
                prvcrdtrat AS 前次信用评级,
                ratchngdir AS 评级变动方向,
                ratobjcttyp_id AS 评级对象类型代码,
                anno_dt AS 公告日期,
                tx_dt AS 数据日期
            FROM cbondissuerrating 
            WHERE cocn_nm LIKE %s
            ORDER BY rat_dt DESC
        """
        params = [f"%{company_name}%"]

        logger.info(f"债券发行主体评级查询语句：{query}")
        logger.info(f"查询参数：{params}")

        results = self.db.execute_query(query, params)
        return results

    def query_rating_agencies(self) -> List[Dict[str, Any]]:
        """查询中国债券信用评估机构名单"""
        query = """
            SELECT 
                object_id AS 对象ID,
                b_info_creditratingagency AS 评估机构代码,
                b_info_creditrating_name AS 评估机构名称,
                s_info_compcode AS 公司ID,
                opmode AS 更新动作,
                opdate AS 更新时间,
                mopdate AS 操作时间,
                data_tm AS 数据日期,
                tx_dt AS 数据日期
            FROM cbondratingdefinition 
            ORDER BY b_info_creditratingagency
        """

        logger.info(f"债券评级机构查询语句：{query}")

        results = self.db.execute_query(query)
        return results

    def generate_database_interpretation(self, comprehensive_results: Dict[str, Any]) -> str:
        """生成数据库查询结果的解析描述，用于大模型理解
        
        Args:
            comprehensive_results: 综合查询结果
            
        Returns:
            数据库解析描述字符串
        """
        interpretation = "这是企业基础信息数据库查询结果，包含："
        
        basic_info = comprehensive_results.get("basic_info", [])
        bond_rating = comprehensive_results.get("bond_rating", [])
        rating_agencies = comprehensive_results.get("rating_agencies", [])
        
        # 企业基本信息解析
        if basic_info:
            company_count = len(basic_info)
            if company_count == 1:
                company = basic_info[0]
                interpretation += f"企业基本信息（共1家企业）：企业名称：{company.get('company_name', '未知')}，"
                interpretation += f"统一社会信用代码：{company.get('unified_social_credit_code', '未知')}，"
                interpretation += f"法定代表人：{company.get('legal_representative', '未知')}，"
                interpretation += f"注册资本：{company.get('registered_capital', '未知')}，"
                interpretation += f"成立日期：{company.get('establishment_date', '未知')}，"
                interpretation += f"注册地址：{company.get('registered_address', '未知')}，"
                interpretation += f"行业类别：{company.get('industry_category', '未知')}，"
                interpretation += f"企业规模：{company.get('enterprise_scale', '未知')}，"
                interpretation += f"总资产：{company.get('total_assets', '未知')}，"
                interpretation += f"净资产：{company.get('net_assets', '未知')}，"
                interpretation += f"年收入：{company.get('annual_revenue', '未知')}。"
            else:
                interpretation += f"企业基本信息（共{company_count}家企业），请选择具体企业。"
        else:
            interpretation += "未找到企业基本信息。"
        
        # 债券评级信息解析
        if bond_rating:
            rating_count = len(bond_rating)
            interpretation += f"债券发行主体信用评级（共{rating_count}条记录）："
            for i, rating in enumerate(bond_rating[:3]):  # 只显示前3条
                interpretation += f"评级日期：{rating.get('rating_date', '未知')}，"
                interpretation += f"信用评级：{rating.get('credit_rating', '未知')}，"
                interpretation += f"评级展望：{rating.get('rating_outlook', '未知')}；"
            if rating_count > 3:
                interpretation += f"等{rating_count}条记录。"
        else:
            interpretation += "未找到债券评级信息。"
        
        # 评级机构信息解析
        if rating_agencies:
            agency_count = len(rating_agencies)
            interpretation += f"债券评级机构（共{agency_count}家机构）："
            agency_names = [agency.get('agency_name', '未知') for agency in rating_agencies[:5]]  # 只显示前5家
            interpretation += "、".join(agency_names)
            if agency_count > 5:
                interpretation += f"等{agency_count}家机构。"
        else:
            interpretation += "未找到评级机构信息。"
        
        return interpretation


# 创建全局工具实例
enterprise_basic_info_tool = EnterpriseBasicInfoTool()


def get_enterprise_basic_info_tool() -> EnterpriseBasicInfoTool:
    """获取企业基本信息查询工具实例"""
    return enterprise_basic_info_tool


def api_query_tool(company_name: str) -> Dict[str, Any]:
    """执行API查询，获取企业详细信息

    流程：
    1. 先调用身份识别接口(401008)获取corrId
    2. 将corrId作为参数传递给其他需要身份验证的API
    3. 对于需要详情ID的API，需要额外的详情ID参数
    
    现在使用直接XML解析方法，跳过字典转换步骤
    """
    api_type_to_service_id = {
        "identity_check": "401008",  # 企查查客户身份识别
        "equity_freeze": "400639",  # 股权冻结核查
        "env_penalty": "400637",  # 环保处罚详情核查
        "dishonest": "401049",  # 失信详情核查
        "env_credit": "401058",  # 企查查环保信用评价
        "judicial_risk": "400631",  # 汇法司法风险企业画像换签版
        "operation_abnormal": "400687",  # 经营异常核查
        "annual_report": "400690",  # 企业年报信息
        "admin_penalty": "400682",  # 行政处罚核查
        "shareholder_info": "401015",  # 企查查股东信息工商登记
        "historical_executives": "401029"  # 企查查历史高管核查
    }

    # API类型到中文描述的映射
    api_type_to_description = {
        "identity_check": "企查查客户身份识别接口",
        "equity_freeze": "股权冻结核查接口",
        "env_penalty": "环保处罚详情核查接口",
        "dishonest": "失信详情核查接口",
        "env_credit": "企查查环保信用评价接口",
        "judicial_risk": "汇法司法风险企业画像换签版接口",
        "operation_abnormal": "经营异常核查接口",
        "annual_report": "企业年报信息接口",
        "admin_penalty": "行政处罚核查接口",
        "shareholder_info": "企查查股东信息工商登记接口",
        "historical_executives": "企查查历史高管核查接口"
    }

    result = {}
    xml_builder = XMLBuilder()
    
    # 角标计数器，从1开始
    citation_counter = 1

    # 第一步：使用corrId调用其他API
    for api_type, service_id in api_type_to_service_id.items():

        # logger.info(f"执行API查询, api_type: {api_type}, service_id: {service_id}")

        # 构建XML请求
        xml_payload = xml_builder.build_xml_by_api_type(api_type, company_name)

        # 调用API - 现在使用新的直接XML解析方法
        api_response = xml_api_tool.call_api(service_id, xml_payload)
        
        # 获取解析后的描述文字
        interpretation = api_response.get("interpretation", "解析失败")
        
        # 添加来源标记到描述文字中
        api_description = api_type_to_description.get(api_type, "API接口")
        # 不再在文本中包含来源信息，而是通过send_citation_info传输
        result[api_type] = interpretation
        
        # 通过send_citation_info传输来源信息
        # 为每个API查询分配不同的角标编号，格式为[s数字]
        citation_key = f"[s{citation_counter}]"
        send_citation_info(citation_key, f"{api_description}")
        
        # 递增角标计数器
        citation_counter += 1
        
    return result


@tool(
    description="""企业基本信息查询工具：
                    示例调用：enterprise_basic_info_tool_function("即墨市自来水服务公司", "")或enterprise_basic_info_tool_function("即墨市自来水服务公司", "913702821234567890")
                    功能：
                      - 企业基本信息查询：包括企业名称、统一社会信用代码、法定代表人、注册资本、成立日期、经营范围、注册地址、行业类别、企业规模、实际控制人、总资产、净资产、年收入等
                      - 债券发行主体信用评级查询：包括评级日期、评级类型、信用评级、评级展望、评级机构、评级描述、先前信用评级、评级变化方向等
                      - 债券评级机构查询：获取中国债券信用评估机构名单"""
)
@with_error_handling
def enterprise_basic_info_tool_function(
    company_name: str, credit_code: Optional[str] = None
) -> Dict:
    if not company_name and not credit_code:
        # 参数缺失 - 用户级错误
        raise ToolUserError("请提供企业名称或者社会统一信用代码")

    logger.info("企业基础信息查询工具函数enterprise_basic_info_tool_function")

    # 使用公共方法输出进度信息
    progress_data = "🔍 企业基础信息查询"
    params = []
    if company_name:
        params.append(f"企业：{company_name}")
    if credit_code:
        params.append(f"信用代码：{credit_code}")
    if params:
        progress_data += f" | {', '.join(params)}"
    send_progress_info(progress_data)

    tool_instance = get_enterprise_basic_info_tool()

    selected_name = company_name
    credit_code = credit_code or ""
    while True:
        last_basic_info: List[Dict[str, Any]] = []
        comprehensive_results: Dict[str, Any] = {}

        comprehensive_results = tool_instance.query_by_company_name_credit_code(
            selected_name, credit_code
        )
        last_basic_info = comprehensive_results.get("basic_info") or []
        
        # 确定最终企业名称 - 修复字段名引用
        final_company_name = selected_name or (
            last_basic_info[0].get("企业名称") if last_basic_info else ""
        )
        if not final_company_name:
            raise ToolUserError("未能确定企业名称，请提供企业的工商注册全称。")

        # 获取API查询结果
        api_results = api_query_tool(final_company_name)

        # 检查企查查客户身份识别结果
        identity_check_result = api_results.get("identity_check", "")
        
        # 如果企查查返回"【有效请求】查询无结果"且数据库为空，则中断要求重新输入
        if "查询状态：【有效请求】查询无结果" in identity_check_result and not last_basic_info:
            interrupt_payload = {
                "type": "enterprise_name_required",
                "css_type": "textInput",
                "message": "没有收到有效的企业名称，请重新提供企业的工商注册全称。",
                "requested_at": datetime.now().isoformat(),
            }
            while True:
                logger.info(interrupt_payload["message"])
                selected_name = interrupt(interrupt_payload)
                if isinstance(selected_name, str):
                    selected_name = selected_name.strip()
                    if selected_name:
                        break
                    interrupt_payload["message"] = "企业名称不能为空，请重新提供企业的工商注册全称。"
                    continue
                interrupt_payload["message"] = "没有收到有效的企业名称，请重新提供企业的工商注册全称。"
            continue  # 重新开始外部循环

        # 如果企查查返回"【有效请求】查询无结果"且数据库有多条，则中断要求选择
        if "查询状态：【有效请求】查询无结果" in identity_check_result and len(last_basic_info) > 1:
            company_names = [
                company.get("企业名称") for company in last_basic_info if company.get("企业名称")
            ]
            interrupt_payload = {
                "type": "enterprise_selection_required",
                "css_type": "checkbox",
                "message": "找到多个匹配企业，请提供更精确的企业名称。",
                "options": company_names,
                "requested_at": datetime.now().isoformat(),
            }
            while True:
                logger.info(interrupt_payload["message"])
                selected_name = interrupt(interrupt_payload)
                if isinstance(selected_name, str):
                    selected_name = selected_name.strip()
                    if selected_name:
                        break
                    interrupt_payload["message"] = "企业名称不能为空，请重新提供企业的工商注册全称。"
                    continue
                interrupt_payload["message"] = "没有收到有效的企业名称，请重新提供企业的工商注册全称。"
            continue  # 重新开始外部循环

        # 合并综合查询结果和API查询结果
        results: Dict[str, Any] = {}
        results.update(comprehensive_results)
        results.update(api_results)
        results["selected_company_name"] = final_company_name

        # 如果最终企业名称与原始查询不同，添加明确说明，避免LLM混淆
        if final_company_name != company_name:
            results["_execution_note"] = (
                f"注意：原始查询的企业名称'{company_name}'未找到数据，"
                f"用户提供了修正后的企业名称'{final_company_name}'进行查询。"
                f"请基于'{final_company_name}'的数据进行分析，不要再次查询'{company_name}'。"
            )
        break
    if not results:
        # 数据不存在 - 用户级错误
        raise ToolUserError("请提供详细的企业名称或者社会统一信用代码")
    logger.info(f"查询企业基本信息成功，返回内容：{results}")
    return results
