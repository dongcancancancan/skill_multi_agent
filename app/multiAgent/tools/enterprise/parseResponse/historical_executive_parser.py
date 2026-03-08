import xml.etree.ElementTree as ET
from typing import Dict, List, Optional


class HistoricalExecutiveParser:
    """企查查历史高管核查解析器 (服务ID: 401029)"""
    
    def parse(self, root: ET.Element) -> str:
        """直接解析历史高管核查XML并生成描述文字"""
        result_lines = []
        
        # 查找历史高管信息 - 正确的XML路径
        historical_executives = root.findall(".//result/data")
        
        if not historical_executives:
            return "未查询到历史高管信息"
        
        result_lines.append("历史高管核查结果：")
        
        for i, executive in enumerate(historical_executives, 1):
            result_lines.append(f"\n第{i}位历史高管：")
            
            # 解析高管基本信息 - 根据实际XML结构
            employee_name = executive.findtext("employeeName", "").strip()
            job = executive.findtext("job", "").strip()
            in_date = executive.findtext("inDate", "").strip()
            change_date = executive.findtext("changeDate", "").strip()
            key_no = executive.findtext("keyNo", "").strip()
            
            if employee_name:
                result_lines.append(f"  姓名：{employee_name}")
            if job:
                result_lines.append(f"  职位：{job}")
            if in_date:
                result_lines.append(f"  入职时间：{in_date}")
            if change_date:
                result_lines.append(f"  变更时间：{change_date}")
            if key_no:
                result_lines.append(f"  关键编号：{key_no}")
        
        return "\n".join(result_lines)
    
    def get_field_mapping(self) -> Dict[str, str]:
        """返回历史高管核查字段映射字典"""
        return {
            "employeeName": "姓名",
            "job": "职位",
            "inDate": "入职时间",
            "changeDate": "变更时间",
            "keyNo": "关键编号"
        }
