import xml.etree.ElementTree as ET
from typing import Dict, List, Optional


class DishonestCheckParser:
    """企查查失信核查解析器 (服务ID: 401049)"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析失信核查XML并生成描述文字"""
        result_lines = []
        
        # 首先检查verifyresult字段，0表示没有查询到失信记录
        verify_result = root.findtext(".//result/verifyresult", "").strip()
        
        if verify_result == "0":
            return "失信核查结果：未查询到"
        
        # 查找失信被执行人信息 - 根据实际XML结构查找data节点
        data_nodes = root.findall(".//result/data")
        
        if not data_nodes:
            return "失信核查结果：未查询到"
        
        result_lines.append("失信核查结果：")
        
        for i, data_node in enumerate(data_nodes, 1):
            result_lines.append(f"\n第{i}条失信记录：")
            
            # 解析失信被执行人基本信息 - 根据实际XML字段名
            pk = data_node.findtext("pk", "").strip()
            rgstr_tm = data_node.findtext("rgstrTm", "").strip()
            an_no = data_node.findtext("anNo", "").strip()
            exct_crt = data_node.findtext("exctCrt", "").strip()
            execute_status = data_node.findtext("executeStatus", "").strip()
            pblsh_tm = data_node.findtext("pblshTm", "").strip()
            execute_no = data_node.findtext("executeNo", "").strip()
            action_type_name = data_node.findtext("actionTypeName", "").strip()
            amount = data_node.findtext("amount", "").strip()
            
            if pk:
                result_lines.append(f"  记录ID：{pk}")
            if rgstr_tm:
                result_lines.append(f"  立案时间：{rgstr_tm}")
            if an_no:
                result_lines.append(f"  案号：{an_no}")
            if exct_crt:
                result_lines.append(f"  执行法院：{exct_crt}")
            if execute_status:
                result_lines.append(f"  履行情况：{execute_status}")
            if pblsh_tm:
                result_lines.append(f"  发布时间：{pblsh_tm}")
            if execute_no:
                result_lines.append(f"  执行依据文号：{execute_no}")
            if action_type_name:
                result_lines.append(f"  失信具体情形：{action_type_name}")
            if amount:
                result_lines.append(f"  执行标的金额：{amount}元")
        
        return "\n".join(result_lines)
    
    def get_field_mapping(self) -> Dict[str, str]:
        """返回失信核查字段映射字典"""
        return {
            "pk": "记录ID",
            "rgstrTm": "立案时间",
            "anNo": "案号",
            "exctCrt": "执行法院",
            "executeStatus": "履行情况",
            "pblshTm": "发布时间",
            "executeNo": "执行依据文号",
            "actionTypeName": "失信具体情形",
            "amount": "执行标的金额"
        }
