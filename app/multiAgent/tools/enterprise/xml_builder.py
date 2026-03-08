"""
XML构建工具模块
专门用于构建各种API的XML请求
"""

from typing import Dict, Optional
from app.utils.logger import agent_logger as logger
import uuid


class XMLBuilder:
    """XML构建工具类"""
    
    def __init__(self):
        pass
    
    def build_identity_check_xml(self, company_name: str) -> str:
        """构建身份识别API的XML请求
        
        Args:
            company_name: 企业名称
        Returns:
            XML请求字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<reqt>
    <svcHdr>
        <corrId></corrId>
        <svcId>401008</svcId>
        <verNbr>105</verNbr>
        <csmrId>167000</csmrId>
        <csmrSerNbr>100010001000</csmrSerNbr>
        <tmStamp>2011.12.29-15.00.00-218</tmStamp>
        <reqtIp>10.1.80.185</reqtIp>
    </svcHdr>
    <campHdr>
        <custNbr></custNbr>
        <drivTrd></drivTrd>
        <srcChlNbr></srcChlNbr>
        <maxAmt></maxAmt>
        <custLoc></custLoc>
        <stepFlag>E</stepFlag>
        <custType></custType>
        <custUniqInfo></custUniqInfo>
        <attr1></attr1>
        <attr2></attr2>
        <attr3></attr3>
        <attr4></attr4>
        <attr5></attr5>
    </campHdr>
    <appHdr>
        <edsIntrfOrg>IQCC058</edsIntrfOrg>
        <edsOprtUsrnm>QD00000666</edsOprtUsrnm>
        <edsOprteOrgnm>80201</edsOprteOrgnm>
        <edsScene>AIJL</edsScene>
        <edsAcct>AIJL_ACCT1</edsAcct>
    </appHdr>
    <appBody>
        <searchKey>{search_key}</searchKey>
        <qryRsn>0</qryRsn>
        <edsValidday>1</edsValidday>
    </appBody>
</reqt>'''
        
        return xml_template.format(search_key=company_name
        )
    
    def build_judicial_risk_xml(self, company_name: str) -> str:
        """构建司法风险企业画像XML请求
        
        Args:
            company_name: 企业名称
        Returns:
            XML请求字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<reqt>
    <svcHdr>
        <corrId></corrId>
        <svcId>400631</svcId>
        <verNbr>105</verNbr>
        <csmrId>167000</csmrId>
        <csmrSerNbr>100010001000</csmrSerNbr>
        <tmStamp>2011.12.29-15.00.00-218</tmStamp>
        <reqtIp>10.1.80.185</reqtIp>
    </svcHdr>
    <campHdr>
        <custNbr></custNbr>
        <drivTrd></drivTrd>
        <srcChlNbr></srcChlNbr>
        <maxAmt></maxAmt>
        <custLoc></custLoc>
        <stepFlag>E</stepFlag>
        <custType></custType>
        <custUniqInfo></custUniqInfo>
        <attr1></attr1>
        <attr2></attr2>
        <attr3></attr3>
        <attr4></attr4>
        <attr5></attr5>
    </campHdr>
    <appHdr>
        <edsIntrfOrg>IPortCourtCountEex</edsIntrfOrg>
        <edsOprtUsrnm>QD00000666</edsOprtUsrnm>
        <edsOprteOrgnm>80201</edsOprteOrgnm>
        <edsScene>AIJL</edsScene>
        <edsAcct>AIJL_ACCT1</edsAcct>
    </appHdr>
    <appBody>
        <idNo>76549811-1</idNo>                                        
        <certTypID>0</certTypID>                                       
        <nm>{search_key}</nm>                                           
        <qryRsn>0</qryRsn>                                               
        <occOrgn>XXXXXXXXXXXXXXXXXX</occOrgn>                          
        <searchKey></searchKey>                                         
        <pageIndex></pageIndex>                                         
        <pageSize></pageSize>                                                   
        <syear></syear>                                                         
        <accuracy></accuracy>                                                   
    </appBody>
</reqt>'''
        
        return xml_template.format(search_key=company_name
        )
    
    def build_operation_abnormal_xml(self, company_name: str) -> str:
        """构建经营异常核查XML请求
        
        Args:
            company_name: 企业名称
        Returns:
            XML请求字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<reqt>
    <svcHdr>
        <corrId></corrId>
        <svcId>400687</svcId>
        <verNbr>105</verNbr>
        <csmrId>167000</csmrId>
        <csmrSerNbr>100010001000</csmrSerNbr>
        <tmStamp>2011.12.29-15.00.00-218</tmStamp>
        <reqtIp>10.1.80.185</reqtIp>
    </svcHdr>
    <campHdr>
        <custNbr></custNbr>
        <drivTrd></drivTrd>
        <srcChlNbr></srcChlNbr>
        <maxAmt></maxAmt>
        <custLoc></custLoc>
        <stepFlag>E</stepFlag>
        <custType></custType>
        <custUniqInfo></custUniqInfo>
        <attr1></attr1>
        <attr2></attr2>
        <attr3></attr3>
        <attr4></attr4>
        <attr5></attr5>
    </campHdr>
    <appHdr>
        <edsIntrfOrg>IQCC041</edsIntrfOrg>
        <edsOprtUsrnm>XXXXXXXX</edsOprtUsrnm>
        <edsOprteOrgnm>XXXXX</edsOprteOrgnm>
        <edsScene>AIJL</edsScene>
        <edsAcct>AIJL_ACCT1</edsAcct>
    </appHdr>
    <appBody>
        <searchKey>{search_key}</searchKey>
        <qryRsn>0</qryRsn>
    </appBody>
</reqt>'''
        
        return xml_template.format(search_key=company_name
        )
    
    def build_annual_report_xml(self, company_name: str) -> str:
        """构建企业年报信息XML请求
        
        Args:
            company_name: 企业名称
        Returns:
            XML请求字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<reqt>
    <svcHdr>
        <corrId></corrId>
        <svcId>400690</svcId>
        <verNbr>105</verNbr>
        <csmrId>167000</csmrId>
        <csmrSerNbr>100010001000</csmrSerNbr>
        <tmStamp>2011.12.29-15.00.00-218</tmStamp>
        <reqtIp>10.1.80.185</reqtIp>
    </svcHdr>
    <campHdr>
        <custNbr></custNbr>
        <drivTrd></drivTrd>
        <srcChlNbr></srcChlNbr>
        <maxAmt></maxAmt>
        <custLoc></custLoc>
        <stepFlag>E</stepFlag>
        <custType></custType>
        <custUniqInfo></custUniqInfo>
        <attr1></attr1>
        <attr2></attr2>
        <attr3></attr3>
        <attr4></attr4>
        <attr5></attr5>
    </campHdr>
    <appHdr>
        <edsIntrfOrg>IQCC044</edsIntrfOrg>
        <edsOprtUsrnm>XXXXXXXX</edsOprtUsrnm>
        <edsOprteOrgnm>XXXXX</edsOprteOrgnm>
        <edsScene>AIJL</edsScene>
        <edsAcct>AIJL_ACCT1</edsAcct>
    </appHdr>
    <appBody>
        <searchKey>{search_key}</searchKey>
        <qryRsn>0</qryRsn>
    </appBody>
</reqt>'''
        
        return xml_template.format(search_key=company_name
        )
    
    def build_env_credit_xml(self, company_name: str) -> str:
        """构建环保信用评价XML请求
        
        Args:
            company_name: 企业名称
        Returns:
            XML请求字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<reqt>
    <svcHdr>
        <corrId></corrId>
        <svcId>401058</svcId>
        <verNbr>105</verNbr>
        <csmrId>167000</csmrId>
        <csmrSerNbr>100010001000</csmrSerNbr>
        <tmStamp>2011.12.29-15.00.00-218</tmStamp>
        <reqtIp>10.1.80.185</reqtIp>
    </svcHdr>
    <campHdr>
        <custNbr></custNbr>
        <drivTrd></drivTrd>
        <srcChlNbr></srcChlNbr>
        <maxAmt></maxAmt>
        <custLoc></custLoc>
        <stepFlag>E</stepFlag>
        <custType></custType>
        <custUniqInfo></custUniqInfo>
        <attr1></attr1>
        <attr2></attr2>
        <attr3></attr3>
        <attr4></attr4>
        <attr5></attr5>
    </campHdr>
    <appHdr>
        <edsIntrfOrg>IQCC068</edsIntrfOrg>
        <edsOprtUsrnm>QD00000666</edsOprtUsrnm>
        <edsOprteOrgnm>80201</edsOprteOrgnm>
        <edsScene>AIJL</edsScene>
        <edsAcct>AIJL_ACCT1</edsAcct>
    </appHdr>
    <appBody>
        <searchKey>{search_key}</searchKey>
        <pageIndex>1</pageIndex>                                               
        <pageSize>20</pageSize>                                                
        <edsValidday>1</edsValidday>                                           
    </appBody>
</reqt>'''
        
        return xml_template.format(search_key=company_name
        )
    
    def build_admin_penalty_xml(self, company_name: str) -> str:
        """构建行政处罚核查XML请求
        
        Args:
            company_name: 企业名称
        Returns:
            XML请求字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<reqt>
    <svcHdr>
        <corrId></corrId>
        <svcId>400682</svcId>
        <verNbr>105</verNbr>
        <csmrId>167000</csmrId>
        <csmrSerNbr>100010001000</csmrSerNbr>
        <tmStamp>2011.12.29-15.00.00-218</tmStamp>
        <reqtIp>10.1.80.185</reqtIp>
    </svcHdr>
    <campHdr>
        <custNbr></custNbr>
        <drivTrd></drivTrd>
        <srcChlNbr></srcChlNbr>
        <maxAmt></maxAmt>
        <custLoc></custLoc>
        <stepFlag>E</stepFlag>
        <custType></custType>
        <custUniqInfo></custUniqInfo>
        <attr1></attr1>
        <attr2></attr2>
        <attr3></attr3>
        <attr4></attr4>
        <attr5></attr5>
    </campHdr>
    <appHdr>
        <edsIntrfOrg>IQCC038</edsIntrfOrg>
        <edsOprtUsrnm>XXXXXXXX</edsOprtUsrnm>
        <edsOprteOrgnm>XXXXX</edsOprteOrgnm>
        <edsScene>AIJL</edsScene>
        <edsAcct>AIJL_ACCT1</edsAcct>
    </appHdr>
    <appBody>
        <searchKey>{search_key}</searchKey>
        <qryRsn>0</qryRsn>
    </appBody>
</reqt>'''
        
        return xml_template.format(search_key=company_name
        )
    
    def build_equity_freeze_xml(self, company_name: str) -> str:
        """构建股权冻结核查XML请求
        
        Args:
            company_name: 企业名称
        Returns:
            XML请求字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<reqt>
    <svcHdr>
        <corrId></corrId>
        <svcId>400639</svcId>
        <verNbr>105</verNbr>
        <csmrId>167000</csmrId>
        <csmrSerNbr>100010001000</csmrSerNbr>
        <tmStamp>2011.12.29-15.00.00-218</tmStamp>
        <reqtIp>10.1.80.185</reqtIp>
    </svcHdr>
    <campHdr>
        <custNbr></custNbr>
        <drivTrd></drivTrd>
        <srcChlNbr></srcChlNbr>
        <maxAmt></maxAmt>
        <custLoc></custLoc>
        <stepFlag>E</stepFlag>
        <custType></custType>
        <custUniqInfo></custUniqInfo>
        <attr1></attr1>
        <attr2></attr2>
        <attr3></attr3>
        <attr4></attr4>
        <attr5></attr5>
    </campHdr>
    <appHdr>
        <edsIntrfOrg>IQCC036</edsIntrfOrg>
        <edsOprtUsrnm>QD00000666</edsOprtUsrnm>
        <edsOprteOrgnm>80201</edsOprteOrgnm>
        <edsScene>AIJL</edsScene>
        <edsAcct>AIJL_ACCT1</edsAcct>
    </appHdr>
    <appBody>
        <searchKey>{search_key}</searchKey>
        <pageIndex></pageIndex>
        <pageSize></pageSize>
        <qryRsn>0</qryRsn>
    </appBody>
</reqt>'''
        
        return xml_template.format(search_key=company_name
        )
    
    def build_env_penalty_xml(self, company_name: str) -> str:
        """构建环保处罚核查XML请求
        
        Args:
            company_name: 企业名称
        Returns:
            XML请求字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<reqt>
    <svcHdr>
        <corrId></corrId>
        <svcId>400637</svcId>
        <verNbr>105</verNbr>
        <csmrId>167000</csmrId>
        <csmrSerNbr>100010001000</csmrSerNbr>
        <tmStamp>2011.12.29-15.00.00-218</tmStamp>
        <reqtIp>10.1.80.185</reqtIp>
    </svcHdr>
    <campHdr>
        <custNbr></custNbr>
        <drivTrd></drivTrd>
        <srcChlNbr></srcChlNbr>
        <maxAmt></maxAmt>
        <custLoc></custLoc>
        <stepFlag>E</stepFlag>
        <custType></custType>
        <custUniqInfo></custUniqInfo>
        <attr1></attr1>
        <attr2></attr2>
        <attr3></attr3>
        <attr4></attr4>
        <attr5></attr5>
    </campHdr>
    <appHdr>
        <edsIntrfOrg>IQCC034</edsIntrfOrg>
        <edsOprtUsrnm>QD00000666</edsOprtUsrnm>
        <edsOprteOrgnm>80201</edsOprteOrgnm>
        <edsScene>AIJL</edsScene>
        <edsAcct>AIJL_ACCT1</edsAcct>
    </appHdr>
    <appBody>
        <searchKey>{search_key}</searchKey>
        <pageIndex></pageIndex>
        <pageSize></pageSize>
        <qryRsn>0</qryRsn>
    </appBody>
</reqt>'''
        
        return xml_template.format(search_key=company_name
        )
    
    def build_dishonest_xml(self, company_name: str) -> str:
        """构建企查查失信核查XML请求
        
        Args:
            company_name: 企业名称
        Returns:
            XML请求字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<reqt>
    <svcHdr>
        <corrId></corrId>
        <svcId>401049</svcId>
        <verNbr>105</verNbr>
        <csmrId>167000</csmrId>
        <csmrSerNbr>100010001000</csmrSerNbr>
        <tmStamp>2011.12.29-15.00.00-218</tmStamp>
        <reqtIp>10.1.80.185</reqtIp>
    </svcHdr>
    <campHdr>
        <custNbr></custNbr>
        <drivTrd></drivTrd>
        <srcChlNbr></srcChlNbr>
        <maxAmt></maxAmt>
        <custLoc></custLoc>
        <stepFlag>E</stepFlag>
        <custType></custType>
        <custUniqInfo></custUniqInfo>
        <attr1></attr1>
        <attr2></attr2>
        <attr3></attr3>
        <attr4></attr4>
        <attr5></attr5>
    </campHdr>
    <appHdr>
        <edsIntrfOrg>IQCC064</edsIntrfOrg>
        <edsOprtUsrnm>XXXXXXXX</edsOprtUsrnm>
        <edsOprteOrgnm>XXXXX</edsOprteOrgnm>
        <edsScene>AIJL</edsScene>
        <edsAcct>AIJL_ACCT1</edsAcct>
    </appHdr>
    <appBody>
        <searchKey>{search_key}</searchKey>
        <pageIndex></pageIndex>
        <pageSize></pageSize>
        <qryRsn>0</qryRsn>
        <edsValidday>1.0</edsValidday>
    </appBody>
</reqt>'''
        
        return xml_template.format(search_key=company_name
        )
    
    def build_shareholder_info_xml(self, company_name: str) -> str:
        """构建企查查股东信息工商登记XML请求
        
        Args:
            company_name: 企业名称
        Returns:
            XML请求字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<reqt>
    <svcHdr>
        <corrId/>
        <svcId>401015</svcId>
        <verNbr>105</verNbr>
        <csmrId>167000</csmrId>
        <csmrSerNbr>100010001000</csmrSerNbr>
        <tmStamp>2011.12.29-15.00.00-218</tmStamp>
        <reqtIp>10.1.80.185</reqtIp>
    </svcHdr>
    <campHdr>
        <custNbr/>
        <drivTrd/>
        <srcChlNbr/>
        <maxAmt/>
        <custLoc/>
        <stepFlag>E</stepFlag>
        <custType/>
        <custUniqInfo/>
        <attr1/>
        <attr2/>
        <attr3/>
        <attr4/>
        <attr5/>
    </campHdr>
    <appHdr>
        <edsIntrfOrg>IQCC011</edsIntrfOrg>
        <edsOprtUsrnm>QDXXXXXXXX</edsOprtUsrnm>
        <edsOprteOrgnm>80201</edsOprteOrgnm>
        <edsScene>AIJL</edsScene>
        <edsAcct>AIJL_ACCT1</edsAcct>
    </appHdr>
    <appBody>
        <searchKey>{search_key}</searchKey>
        <pageIndex>1</pageIndex>
        <pageSize>20</pageSize>
        <edsValidday>1</edsValidday>
        <searchType>1</searchType>
    </appBody>
</reqt>'''
        
        return xml_template.format(search_key=company_name
        )
    
    def build_historical_executives_xml(self, company_name: str) -> str:
        """构建企查查历史高管核查XML请求
        
        Args:
            company_name: 企业名称
        Returns:
            XML请求字符串
        """
        xml_template = '''<?xml version="1.0" encoding="UTF-8"?>
<reqt>
    <svcHdr>
        <corrId></corrId>
        <svcId>401029</svcId>
        <verNbr>105</verNbr>
        <csmrId>167000</csmrId>
        <csmrSerNbr>100010001000</csmrSerNbr>
        <tmStamp>2011.12.29-15.00.00-218</tmStamp>
        <reqtIp>10.1.80.185</reqtIp>
    </svcHdr>
    <campHdr>
        <custNbr></custNbr>
        <drivTrd></drivTrd>
        <srcChlNbr></srcChlNbr>
        <maxAmt></maxAmt>
        <custLoc></custLoc>
        <stepFlag>E</stepFlag>
        <custType></custType>
        <custUniqInfo></custUniqInfo>
        <attr1></attr1>
        <attr2></attr2>
        <attr3></attr3>
        <attr4></attr4>
        <attr5></attr5>
    </campHdr>
    <appHdr>
        <edsIntrfOrg>IQCC063</edsIntrfOrg>
        <edsOprtUsrnm>QD00000666</edsOprtUsrnm>
        <edsOprteOrgnm>80201</edsOprteOrgnm>
        <edsScene>AIJL</edsScene>
        <edsAcct>AIJL_ACCT1</edsAcct>
    </appHdr>
    <appBody>
        <searchKey>{search_key}</searchKey>
        <companyKey></companyKey>
        <pageIndex>1</pageIndex>
        <pageSize>20</pageSize>
        <edsValidday>1</edsValidday>
    </appBody>
</reqt>'''
        
        return xml_template.format(search_key=company_name
        )
    
    def build_xml_by_api_type(self, api_type: str, company_name: str) -> str:
        """根据API类型构建XML请求
        
        Args:
            api_type: API类型
            company_name: 企业名称
            corr_id: 关联ID
            detail_id: 详情ID（仅用于需要详情的API）
            
        Returns:
            XML请求字符串
        """
        api_type_to_method = {
            "identity_check": self.build_identity_check_xml,
            "judicial_risk": self.build_judicial_risk_xml,
            "operation_abnormal": self.build_operation_abnormal_xml,
            "annual_report": self.build_annual_report_xml,
            "env_credit": self.build_env_credit_xml,
            "admin_penalty": self.build_admin_penalty_xml,
            "equity_freeze": self.build_equity_freeze_xml,
            "env_penalty": self.build_env_penalty_xml,
            "dishonest": self.build_dishonest_xml,
            "shareholder_info": self.build_shareholder_info_xml,
            "historical_executives": self.build_historical_executives_xml,
        }
        
        if api_type not in api_type_to_method:
            raise ValueError(f"不支持的API类型: {api_type}")
        
        method = api_type_to_method[api_type]
        
        return method(company_name)
