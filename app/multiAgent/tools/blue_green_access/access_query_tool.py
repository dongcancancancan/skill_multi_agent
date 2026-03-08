"""
客户准入判断查询工具模块
提供绿色准入和蓝色准入判断功能
"""

import xml.etree.ElementTree as ET
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from app.utils.logger import agent_logger as logger
from langgraph.types import Command, interrupt
from langgraph.prebuilt import InjectedState
from app.multiAgent.tools.greenGold.http_403500 import ProjectGreenCertificationTool
from app.multiAgent.common.tool_decorator import with_error_handling
from app.multiAgent.tools.greenGold.http_403501 import NonProjectAssistTool
from app.multiAgent.tools.greenGold.http_403502 import FundUsageClassificationTool
from app.utils.config import get_config
from app.multiAgent.tools.query_knowledge_base import query_knowledge_base
from app.multiAgent.tools.common import send_progress_info, send_citation_info
from app.multiAgent.common.uni_state import UniState, StateFields
from app.multiAgent.tools.policy.policy_query_tool import merge_rag_segments


class AccessQueryTool:
    """客户准入判断查询工具类"""

    def __init__(self):
        pass


# 创建全局工具实例
access_query_tool = AccessQueryTool()


def get_access_query_tool() -> AccessQueryTool:
    """获取客户准入判断查询工具实例"""
    return access_query_tool


def parse_403501_response(xml_text: str) -> Dict[str, Any]:
    """解析403501接口的XML响应，提取fundsTipId和其他关键字段

    Args:
        xml_text: XML响应文本

    Returns:
        包含解析结果的字典，包括fundsTipId、fundsTip等字段
    """
    try:
        # 解析XML
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error(f"XML解析失败: {e}, XML内容: {xml_text[:500]}...")
        return {
            "fundsTipId": None,
            "fundsTip": None,
            "greenCode": None,
            "explain": None,
            "respCde": None,
            "respMsg": f"XML解析失败: {str(e)}",
            "parsed_successfully": False,
            "error": str(e),
        }

    # 定义命名空间（如果有的话）
    namespaces = {}

    # 查找所有records元素
    records_elems = root.findall(".//records")

    # 检查响应代码
    resp_cde = None
    resp_msg = None
    resp_cde_elem = root.find(".//respCde")
    if resp_cde_elem is not None and resp_cde_elem.text:
        resp_cde = resp_cde_elem.text.strip()

    resp_msg_elem = root.find(".//respMsg")
    if resp_msg_elem is not None and resp_msg_elem.text:
        resp_msg = resp_msg_elem.text.strip()

    # 如果没有找到任何records，返回空结果
    if not records_elems:
        result = {
            "fundsTipId": None,
            "fundsTip": None,
            "greenCode": None,
            "explain": None,
            "respCde": resp_cde,
            "respMsg": resp_msg,
            "parsed_successfully": False,
        }
        logger.info(f"XML解析失败: 未找到records元素, respCde={resp_cde}")
        return result

    # 如果只有一个record，直接返回
    if len(records_elems) == 1:
        records_elem = records_elems[0]
        funds_tip_id = None
        funds_tip = None
        green_code = None
        explain = None

        # 提取fundsTipId
        funds_tip_id_elem = records_elem.find("fundsTipId")
        if funds_tip_id_elem is not None and funds_tip_id_elem.text:
            funds_tip_id = funds_tip_id_elem.text.strip()

        # 提取fundsTip
        funds_tip_elem = records_elem.find("fundsTip")
        if funds_tip_elem is not None and funds_tip_elem.text:
            funds_tip = funds_tip_elem.text.strip()

        # 提取greenCode
        green_code_elem = records_elem.find("greenCode")
        if green_code_elem is not None and green_code_elem.text:
            green_code = green_code_elem.text.strip()

        # 提取explain
        explain_elem = records_elem.find("explain")
        if explain_elem is not None and explain_elem.text:
            explain = explain_elem.text.strip()

        result = {
            "fundsTipId": funds_tip_id,
            "fundsTip": funds_tip,
            "greenCode": green_code,
            "explain": explain,
            "respCde": resp_cde,
            "respMsg": resp_msg,
            "parsed_successfully": funds_tip_id is not None,
        }

        logger.info(f"XML解析成功: fundsTipId={funds_tip_id}, respCde={resp_cde}")
        return result

    # 如果有多个records，让用户选择
    funds_tip_options = []
    for i, record in enumerate(records_elems):
        funds_tip_elem = record.find("fundsTip")
        funds_tip_id_elem = record.find("fundsTipId")

        if funds_tip_elem is not None and funds_tip_elem.text:
            funds_tip_text = funds_tip_elem.text.strip()
            funds_tip_id = (
                funds_tip_id_elem.text.strip()
                if funds_tip_id_elem is not None and funds_tip_id_elem.text
                else f"选项{i+1}"
            )
            funds_tip_options.append(
                {"index": i + 1, "fundsTipId": funds_tip_id, "fundsTip": funds_tip_text}
            )

    # 构建中断负载 - 显示index和fundsTip
    interrupt_payload = {
        "type": "fund_usage_selection_required",
        "css_type": "checkbox",
        "message": "检测到多个可能的资金用途场景，请选择：",
        "options": [
            f"{option['index']}. {option['fundsTip']}" for option in funds_tip_options
        ],
        "options_detail": funds_tip_options,  # 包含详细信息的选项
        "requested_at": datetime.now().isoformat(),
    }

    # 中断并让用户选择
    while True:
        logger.info(interrupt_payload["message"])
        selected_index = interrupt(interrupt_payload)
        if isinstance(selected_index, str):
            try:
                selected_num = int(selected_index.strip())
                if 1 <= selected_num <= len(funds_tip_options):
                    selected_option = funds_tip_options[selected_num - 1]

                    # 获取选中的record元素
                    selected_record = records_elems[selected_num - 1]

                    # 提取选中记录的详细信息
                    funds_tip_id = selected_option["fundsTipId"]
                    funds_tip = selected_option["fundsTip"]

                    # 提取其他字段
                    green_code_elem = selected_record.find("greenCode")
                    green_code = (
                        green_code_elem.text.strip()
                        if green_code_elem is not None and green_code_elem.text
                        else None
                    )

                    explain_elem = selected_record.find("explain")
                    explain = (
                        explain_elem.text.strip()
                        if explain_elem is not None and explain_elem.text
                        else None
                    )

                    result = {
                        "fundsTipId": funds_tip_id,
                        "fundsTip": funds_tip,
                        "greenCode": green_code,
                        "explain": explain,
                        "respCde": resp_cde,
                        "respMsg": resp_msg,
                        "parsed_successfully": True,
                        "selected_index": selected_num,
                        "total_options": len(funds_tip_options),
                        "user_selection": selected_index,  # 记录用户原始输入
                    }

                    logger.info(
                        f"用户选择了资金用途场景: {selected_num}. {funds_tip}, fundsTipId={funds_tip_id}"
                    )
                    return result
                else:
                    interrupt_payload["message"] = (
                        f"选择无效，请输入1到{len(funds_tip_options)}之间的数字："
                    )
            except ValueError:
                interrupt_payload["message"] = "请输入有效的数字："
        else:
            interrupt_payload["message"] = "没有收到有效的选择，请输入数字："


def parse_403502_response(xml_text: str) -> Dict[str, Any]:
    """解析403502接口的XML响应，提取绿色认定结果和绿色代码

    Args:
        xml_text: XML响应文本

    Returns:
        包含解析结果的字典，包括绿色认定结果、绿色代码等字段
    """
    try:
        # 解析XML
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error(f"403502 XML解析失败: {e}, XML内容: {xml_text[:500]}...")
        return {
            "认定成功": False,
            "绿色代码": None,
            "respCde": None,
            "respMsg": f"XML解析失败: {str(e)}",
            "parsed_successfully": False,
            "error": str(e),
        }

    # 检查响应消息
    resp_msg = None
    resp_msg_elem = root.find(".//respMsg")
    if resp_msg_elem is not None and resp_msg_elem.text:
        resp_msg = resp_msg_elem.text.strip()

    # 检查响应代码
    resp_cde = None
    resp_cde_elem = root.find(".//respCde")
    if resp_cde_elem is not None and resp_cde_elem.text:
        resp_cde = resp_cde_elem.text.strip()

    # 提取绿色代码
    green_code = None
    green_code_elem = root.find(".//greenCode")
    if green_code_elem is not None and green_code_elem.text:
        green_code = green_code_elem.text.strip()

    # 判断是否交易成功
    is_success = resp_msg == "交易成功"

    result = {
        "认定成功": is_success,
        "绿色代码": green_code,
        "respCde": resp_cde,
        "respMsg": resp_msg,
        "parsed_successfully": True,
    }

    logger.info(f"403502 XML解析结果: 认定成功={is_success}, 绿色代码={green_code}, respMsg={resp_msg}")
    return result


import asyncio


def api_query_tool(project_name: str, purpose: str) -> Dict[str, Any]:
    """执行API查询，获取项目定义"""

    # 设置默认参数值
    business_type = "01"  # 业务类型：绿色金融
    industry_atgreen_code = "A001"  # 行业绿色代码
    standard_type = "PBOCGL"  # 标准类型
    project_industry_code = "A0111"
    context = "绿色认定"
    current_page = 1
    page_size = 20

    # 创建工具实例
    project_green_tool = ProjectGreenCertificationTool()
    non_project_tool = NonProjectAssistTool()
    fund_usage_tool = FundUsageClassificationTool()

    # 1. 首先调用403500接口：根据项目名称查询绿色金融项目认定
    re_http_403500 = project_green_tool.execute(
        business_type, project_name, project_industry_code, context, standard_type
    )

    # 2. 调用403501接口：根据资金用途获取fundsTipId
    re_http_403501 = non_project_tool.execute(
        business_type,
        industry_atgreen_code,
        purpose,
        standard_type,
        current_page,
        page_size,
    )

    # 解析403501返回的fundsTipId
    funds_tip_id = None
    funds_tip = None
    green_code = None
    explain = None

    parsed_403501_data = None

    # 检查响应是否为字典且包含XML响应
    if isinstance(re_http_403501, dict) and "raw_xml_response" in re_http_403501:
        # 调用XML解析函数
        xml_response = re_http_403501["raw_xml_response"]
        parsed_403501_data = parse_403501_response(xml_response)

        if parsed_403501_data.get("parsed_successfully"):
            funds_tip_id = parsed_403501_data["fundsTipId"]
            funds_tip = parsed_403501_data["fundsTip"]
            green_code = parsed_403501_data["greenCode"]
            explain = parsed_403501_data["explain"]
            logger.info(f"成功解析fundsTipId: {funds_tip_id}")
        else:
            logger.warning(
                f"XML解析失败: {parsed_403501_data.get('error', '未知错误')}"
            )
    elif isinstance(re_http_403501, dict) and "fundsTipId" in re_http_403501:
        # 如果响应已经是结构化数据（非XML）
        funds_tip_id = re_http_403501["fundsTipId"]
    elif hasattr(re_http_403501, "get") and callable(re_http_403501.get):
        # 兼容性处理
        funds_tip_id = re_http_403501.get("fundsTipId")

    # 3. 调用403502接口：使用403501返回的fundsTipId查询分类信息
    re_http_403502 = None
    parsed_403502_data = None
    if funds_tip_id:
        logger.info(f"使用fundsTipId调用403502接口: {funds_tip_id}")
        re_http_403502 = fund_usage_tool.execute(funds_tip_id, standard_type)
        
        # 解析403502响应
        if isinstance(re_http_403502, dict) and "raw_xml_response" in re_http_403502:
            xml_response = re_http_403502["raw_xml_response"]
            parsed_403502_data = parse_403502_response(xml_response)
            logger.info(f"403502解析结果: 认定成功={parsed_403502_data.get('认定成功')}, 绿色代码={parsed_403502_data.get('绿色代码')}")
    else:
        logger.warning("无法获取fundsTipId，跳过403502接口调用")

    # 构建完整的绿色认定信息
    if parsed_403502_data and parsed_403502_data.get("认定成功"):
        # 认定成功的情况
        result = {
            "资金用途提示ID": funds_tip_id,
            "资金用途": funds_tip,
            "绿色认定码": parsed_403502_data.get("绿色代码") or green_code,
            "绿色认定结果": "认定成功"
        }
    else:
        # 认定失败的情况
        result = {
            "资金用途提示ID": funds_tip_id,
            "资金用途": funds_tip,
            "绿色认定码": parsed_403502_data.get("绿色代码") if parsed_403502_data else green_code,
            "绿色认定结果": "认定失败"
        }

    logger.info(f"执行API查询成功，获取企业详细信息result:{result}")

    return result


def blue_access_query(
    project_name: str, purpose: Optional[str] = None
) -> Dict[str, Any]:
    """执行蓝色准入判断查询

    Args:
        project_name: 项目名称
        purpose: 资金用途，可选

    Returns:
        蓝色准入判断结果
    """
    if not project_name:
        return interrupt("请提供项目名称")

    if not purpose:
        purpose = "项目融资"  # 设置默认资金用途

    # 构建政策查询内容
    policy_query = f"蓝色金融准入条件 {project_name} {purpose}"

    # 调用政策库工具
    # policy_result = policy_query_tool(policy_query)
    logger.info(f"政策库查询params：{policy_query}")
    if not policy_query:
        interrupt("请提供详细的政策信息，如对公金融政策、环保政策等")
    DATASET_ID = get_config("knowledge.policy_dataset_id")
    # 查询知识库获取政策信息（使用异步调用）
    knowledge_result = asyncio.run(
        query_knowledge_base(query=policy_query, dataset_id=DATASET_ID)
    )
    logger.info(f"政策库查询结果：{knowledge_result}")
    policy_result = {
        "status": "success",
        "query": policy_query,
        "dataset_id": DATASET_ID,
        "result": {
            "content": knowledge_result.get("records", "未找到相关政策"),
        },
    }

    logger.info(f"蓝色准入判断查询结果: {policy_result}")

    return {
        "access_type": "blue",
        "project_name": project_name,
        "purpose": purpose,
        "policy_query": policy_query,
        "policy_result": policy_result,
        "knowledge_result": knowledge_result,  # 添加原始结果用于RAG合并
    }


@tool("access_query_tool_function")
@with_error_handling
def access_query_tool_function(
    project_name: str,
    purpose: str,
    access_type: str = "green",
    agent: str = "blue_green_access_agent",
    state: Annotated[UniState, InjectedState] = None,
    tool_call_id: Annotated[str, InjectedToolCallId] = "",
) -> Command:
    """客户准入判断查询工具函数

    Args:
        project_name: 项目名称
        purpose: 资金用途，可选
        access_type: 准入类型，'green'表示绿色准入，'blue'表示蓝色准入，默认为'green'

    Returns:
        准入判断结果
    """

    # 验证access_type参数
    if access_type not in ["green", "blue"]:
        return interrupt(
            "准入类型参数错误，请使用'green'表示绿色准入或'blue'表示蓝色准入"
        )

    # 输出进度信息
    progress_data = "🎯 客户准入判断查询"
    params = []
    if access_type:
        access_type_display = "绿色准入" if access_type == "green" else "蓝色准入"
        params.append(f"类型：{access_type_display}")
    if project_name:
        params.append(f"项目：{project_name}")
    if purpose:
        params.append(f"用途：{purpose}")
    if params:
        progress_data += f" | {', '.join(params)}"
    send_progress_info(progress_data)
    
    # 发送角标信息 - 蓝绿准入查询使用[s1]格式
    if access_type == "green":
        send_citation_info("[s1]", "外部API接口: 403500/403501/403502")
    else:
        send_citation_info("[s1]", "知识库: 政策文档")

    logger.info(f"客户准入判断查询工具函数 - 准入类型: {access_type}")

    if access_type == "green":
        if not project_name:
            return interrupt("请提供项目名称")

        if not purpose:
            purpose = "项目融资"  # 设置默认资金用途
        # 执行绿色准入判断
        api_results = api_query_tool(project_name, purpose)
        results = api_results

        # 在响应文本中添加角标标记
        if isinstance(results, dict):
            # 添加角标到响应文本的开头
            results_with_citation = results.copy()
            # 将角标添加到响应文本的开头
            if "资金用途提示ID" in results_with_citation:
                # 在现有文本前添加角标
                results_with_citation["角标"] = "[s1]"
                results_with_citation["数据来源"] = "外部API接口: 403500/403501/403502"
                # 同时确保角标在文本中显示
                if "说明" in results_with_citation:
                    results_with_citation["说明"] = f"[s1] {results_with_citation['说明']}"
                elif "绿色认定结果" in results_with_citation:
                    # 创建一个新的说明字段
                    results_with_citation["说明"] = f"[s1] 以上信息来自实时API接口调用，绿色准入工具认定该项目为'{results_with_citation.get('绿色认定结果', '未知')}'状态。"
            results = results_with_citation

        # 绿色准入返回 Command（不处理 RAG）
        result_payload = {"status": "success", "result": results}
        tool_message = ToolMessage(
            content=json.dumps(result_payload, ensure_ascii=False, indent=2),
            name="access_query_tool_function",
            tool_call_id=tool_call_id,
        )
        current_messages = list(state.get(StateFields.MESSAGES, []))
        return Command(update={StateFields.MESSAGES: current_messages + [tool_message]})
    else:
        # 执行蓝色准入判断
        results = blue_access_query(project_name, purpose)
        # 蓝色准入：合并 RAG history
        knowledge_result = results.get("knowledge_result", {})
        current_records = knowledge_result.get("records", [])
        rag_history = state.get(StateFields.RAG_HISTORY) or {}

        # 使用新的 merge_rag_segments 函数合并并去重 segments
        updated_rag_history = merge_rag_segments(
            current_rag_history=rag_history,
            new_segments=current_records,
            agent_name=agent,
        )

        # 返回 Command（包含 RAG history）
        result_payload = {"status": "success", "result": results}
        tool_message = ToolMessage(
            content=json.dumps(result_payload, ensure_ascii=False, indent=2),
            name="access_query_tool_function",
            tool_call_id=tool_call_id,
        )
        current_messages = list(state.get(StateFields.MESSAGES, []))
        return Command(
            update={
                StateFields.MESSAGES: current_messages + [tool_message],
                StateFields.RAG_HISTORY: updated_rag_history,
            }
        )
