from typing import Dict, Type, Optional
import xml.etree.ElementTree as ET

from .shareholder_parser import ShareholderInfoParser
from .operation_abnormal_parser import OperationAbnormalParser
from .judicial_risk_parser import JudicialRiskParser
from .equity_freeze_parser import EquityFreezeParser
from .environmental_penalty_parser import EnvPenaltyParser
from .admin_penalty_parser import AdminPenaltyParser
from .annual_report_parser import AnnualReportParser
from .environmental_credit_parser import EnvCreditParser
from .identity_check_parser import IdentityCheckParser
from .historical_executive_parser import HistoricalExecutiveParser
from .dishonest_check_parser import DishonestCheckParser


class ParserFactory:
    """解析器工厂类 - 根据服务ID创建对应的解析器"""
    
    # 服务ID到解析器的映射 - 根据用户提供的最新服务ID调整
    SERVICE_PARSER_MAP: Dict[str, Type] = {
        "401008": IdentityCheckParser,  # 企查查客户身份识别
        "400639": EquityFreezeParser,  # 股权冻结核查
        "400637": EnvPenaltyParser,  # 环保处罚详情核查
        "401049": DishonestCheckParser,  # 失信详情核查
        "401058": EnvCreditParser,  # 企查查环保信用评价
        "400631": JudicialRiskParser,  # 汇法司法风险企业画像换签版
        "400687": OperationAbnormalParser,  # 经营异常核查
        "400690": AnnualReportParser,  # 企业年报信息
        "400682": AdminPenaltyParser,  # 行政处罚核查
        "401015": ShareholderInfoParser,  # 企查查股东信息工商登记
        "401029": HistoricalExecutiveParser,  # 企查查历史高管核查
    }
    
    @classmethod
    def get_parser(cls, service_id: str):
        """根据服务ID获取对应的解析器实例"""
        parser_class = cls.SERVICE_PARSER_MAP.get(service_id)
        if parser_class:
            return parser_class()
        return None
    
    @classmethod
    def parse_xml_directly(cls, service_id: str, xml_content: str) -> str:
        """直接解析XML内容并生成描述文字"""
        try:
            # 解析XML
            root = ET.fromstring(xml_content)
            
            # 获取对应的解析器
            parser = cls.get_parser(service_id)
            if parser:
                return parser.parse(root)
            else:
                return f"未找到服务ID {service_id} 对应的解析器"
                
        except ET.ParseError as e:
            return f"XML解析错误: {str(e)}"
        except Exception as e:
            return f"解析过程中发生错误: {str(e)}"
    
    @classmethod
    def get_supported_services(cls) -> list:
        """获取支持的服务ID列表"""
        return list(cls.SERVICE_PARSER_MAP.keys())
