"""
统一Supervisor流式输出测试用例

测试 stream_with_unified_supervisor 函数的流式输出功能
"""

import asyncio
import uuid
import pytest
from typing import List

from app.api.models import MainGraphRequest, GraphStreamResult
from app.multiAgent.dispatch.unified_supervisor import stream_with_unified_supervisor
from app.utils.logger import logger


class TestUnifiedSupervisorStream:
    """统一Supervisor流式输出测试类"""

    @pytest.mark.asyncio
    async def test_simple_query_stream(self):
        """测试简单查询的流式输出"""
        logger.info("=" * 80)
        logger.info("开始测试: 简单查询的流式输出")
        logger.info("=" * 80)

        # 构造请求对象
        request = MainGraphRequest(
            input="你好，请介绍一下你自己",
            session_id="test_simple_query_001",
        )

        # 调用流式函数
        stream_iterator = stream_with_unified_supervisor(request)

        # 收集流式结果
        results: List[GraphStreamResult] = []
        try:
            async for result in stream_iterator:
                logger.info(
                    f"收到流式结果: status={result.status}, stream_mode={result.stream_mode}"
                )
                results.append(result)

                # 打印流式内容
                if result.status == "success" and result.data:
                    if hasattr(result.data, "content"):
                        logger.info(f"内容: {result.data.content}")
                    else:
                        logger.info(f"数据: {result.data}")
        except Exception as e:
            logger.error(f"流式输出过程中出错: {str(e)}", exc_info=True)
            pytest.fail(f"流式输出失败: {str(e)}")

        # 断言验证
        assert len(results) > 0, "应该至少收到一条流式结果"
        logger.info(f"总共收到 {len(results)} 条流式结果")
        logger.info("简单查询流式输出测试完成")

    @pytest.mark.asyncio
    async def test_complex_task_stream(self):
        """测试复杂任务的流式输出（会触发计划制定并模拟中断恢复）"""
        logger.info("=" * 80)
        logger.info("开始测试: 复杂任务的流式输出")
        logger.info("=" * 80)

        session_id = str(uuid.uuid4())

        # 构造复杂任务请求
        request = MainGraphRequest(
            input="产品库中有哪些蓝绿色金融产品？产品准入条件是什么？",
            session_id=session_id,
        )

        # 调用流式函数
        stream_iterator = stream_with_unified_supervisor(request)

        # 收集流式结果
        results: List[GraphStreamResult] = []
        has_interrupt = False

        try:
            async for result in stream_iterator:
                logger.info(
                    f"收到流式结果: status={result.status}, stream_mode={result.stream_mode}"
                )
                results.append(result)

                # 检查是否有中断
                if result.status == "interrupted":
                    has_interrupt = True
                    logger.info(f"检测到中断: {result.interrupt_data}")
                    # 检测到中断后立即跳出第一轮循环
                    break

                # 打印流式内容
                if result.status == "success" and result.data:
                    if hasattr(result.data, "content"):
                        print(result.data.content, end="", flush=True)
                        # logger.info(
                        #     f"内容: {result.data.content[:100] if result.data.content else ''}"
                        # )
                    elif isinstance(result.data, dict):
                        logger.info(f"数据类型: {result.data.get('type', 'unknown')}")
        except Exception as e:
            logger.error(f"流式输出过程中出错: {str(e)}", exc_info=True)
            pytest.fail(f"流式输出失败: {str(e)}")

        # 如果检测到中断，发送恢复请求
        if has_interrupt:
            logger.info("=" * 80)
            logger.info("模拟用户审批: 发送 'yes' 恢复执行")
            logger.info("=" * 80)

            # 创建恢复请求
            resume_request = MainGraphRequest(
                input="yes",
                session_id=session_id,
                is_resume=True,
            )

            # 继续处理恢复后的流式输出
            resume_iterator = stream_with_unified_supervisor(resume_request)

            try:
                async for result in resume_iterator:

                    # logger.info(
                    #     f"恢复后收到流式结果: status={result.status}, stream_mode={result.stream_mode}"
                    # )
                    results.append(result)

                    # 打印流式内容
                    if result.status == "success" and result.data:
                        if hasattr(result.data, "content"):
                            print(result.data.content, end="", flush=True)
                            # logger.info(
                            #     f"内容: {result.data.content[:100] if result.data.content else ''}"
                            # )
                        elif isinstance(result.data, dict):
                            logger.info(
                                f"数据类型: {result.data.get('type', 'unknown')}"
                            )
            except Exception as e:
                logger.error(f"恢复执行过程中出错: {str(e)}", exc_info=True)
                pytest.fail(f"恢复执行失败: {str(e)}")

        # 断言验证
        assert len(results) > 0, "应该至少收到一条流式结果"
        assert has_interrupt, "复杂任务应该触发中断（计划审批）"
        logger.info(f"总共收到 {len(results)} 条流式结果")
        logger.info(f"是否触发中断: {has_interrupt}")
        logger.info("复杂任务流式输出测试完成（包含中断恢复）")

    @pytest.mark.asyncio
    async def test_toolbox_query_stream(self):
        """测试ToolBox查询的流式输出"""
        logger.info("=" * 80)
        logger.info("开始测试: ToolBox查询的流式输出")
        logger.info("=" * 80)

        # 构造ToolBox查询请求
        request = MainGraphRequest(
            input="查询“山东晟俐建设工程闪财公司”的企业基础信息，给出股东名称和持股比例",
            session_id=str(uuid.uuid4()),
        )

        # 调用流式函数
        stream_iterator = stream_with_unified_supervisor(request)

        # 收集流式结果
        results: List[GraphStreamResult] = []
        has_thinking = False
        has_knowledge_base = False

        try:
            async for result in stream_iterator:
                # logger.info(
                #     f"收到流式结果: status={result.status}, stream_mode={result.stream_mode}"
                # )
                results.append(result)

                # 检查不同类型的流式数据
                if result.stream_mode == "custom" and isinstance(result.data, dict):
                    data_type = result.data.get("type")
                    if data_type == "thinking":
                        has_thinking = True
                        logger.info(f"思考信息: {result.data.get('data', '')[:100]}")
                    elif data_type == "knowledge_base":
                        has_knowledge_base = True
                        logger.info(f"知识库信息: {result.data}")

                # 打印消息内容
                if result.stream_mode == "messages" and result.data:
                    if hasattr(result.data, "content"):
                        print(result.data.content, end="", flush=True)
                        # logger.info(
                        #     f"消息内容: {result.data.content[:100] if result.data.content else ''}"
                        # )
        except Exception as e:
            logger.error(f"流式输出过程中出错: {str(e)}", exc_info=True)
            pytest.fail(f"流式输出失败: {str(e)}")

        # 断言验证
        assert len(results) > 0, "应该至少收到一条流式结果"
        logger.info(f"总共收到 {len(results)} 条流式结果")
        logger.info(f"是否包含thinking信息: {has_thinking}")
        logger.info(f"是否包含knowledge_base信息: {has_knowledge_base}")
        logger.info("ToolBox查询流式输出测试完成")

    @pytest.mark.asyncio
    async def test_stream_result_structure(self):
        """测试流式结果的数据结构"""
        logger.info("=" * 80)
        logger.info("开始测试: 流式结果数据结构")
        logger.info("=" * 80)

        # 构造请求对象
        request = MainGraphRequest(
            input="你能做什么？",
            session_id="test_structure_001",
        )

        # 调用流式函数
        stream_iterator = stream_with_unified_supervisor(request)

        # 验证流式结果结构
        try:
            async for result in stream_iterator:
                # 验证基本字段
                assert hasattr(result, "status"), "结果应该有status字段"
                assert result.status in [
                    "success",
                    "error",
                    "interrupted",
                ], "status应该是有效值"

                # 验证可选字段
                if result.status == "success":
                    assert hasattr(
                        result, "stream_mode"
                    ), "成功结果应该有stream_mode字段"
                    assert hasattr(result, "data"), "成功结果应该有data字段"

                if result.status == "interrupted":
                    assert hasattr(
                        result, "interrupt_data"
                    ), "中断结果应该有interrupt_data字段"

                if result.status == "error":
                    assert hasattr(
                        result, "error_message"
                    ), "错误结果应该有error_message字段"

                logger.info(f"结果结构验证通过: status={result.status}")
        except Exception as e:
            logger.error(f"流式输出过程中出错: {str(e)}", exc_info=True)
            pytest.fail(f"流式输出失败: {str(e)}")

        logger.info("流式结果数据结构测试完成")

    @pytest.mark.asyncio
    async def test_multiple_messages_stream(self):
        """测试多轮对话的流式输出"""
        logger.info("=" * 80)
        logger.info("开始测试: 多轮对话的流式输出")
        logger.info("=" * 80)

        session_id = "test_multiple_messages_001"

        # 第一轮对话
        logger.info("第一轮对话: 问候")
        request1 = MainGraphRequest(
            input="你好",
            session_id=session_id,
        )

        stream_iterator1 = stream_with_unified_supervisor(request1)
        results1 = []

        try:
            async for result in stream_iterator1:
                results1.append(result)
                if result.status == "success" and hasattr(result.data, "content"):
                    logger.info(f"第一轮回复: {result.data.content[:50]}")
        except Exception as e:
            logger.error(f"第一轮对话出错: {str(e)}", exc_info=True)
            pytest.fail(f"第一轮对话失败: {str(e)}")

        assert len(results1) > 0, "第一轮对话应该有结果"
        logger.info(f"第一轮对话收到 {len(results1)} 条结果")

        # 等待一小段时间
        await asyncio.sleep(1)

        # 第二轮对话
        logger.info("第二轮对话: 查询功能")
        request2 = MainGraphRequest(
            input="你有什么功能？",
            session_id=session_id,
        )

        stream_iterator2 = stream_with_unified_supervisor(request2)
        results2 = []

        try:
            async for result in stream_iterator2:
                results2.append(result)
                if result.status == "success" and hasattr(result.data, "content"):
                    logger.info(f"第二轮回复: {result.data.content[:50]}")
        except Exception as e:
            logger.error(f"第二轮对话出错: {str(e)}", exc_info=True)
            pytest.fail(f"第二轮对话失败: {str(e)}")

        assert len(results2) > 0, "第二轮对话应该有结果"
        logger.info(f"第二轮对话收到 {len(results2)} 条结果")
        logger.info("多轮对话流式输出测试完成")


@pytest.mark.asyncio
async def test_stream_output_standalone():
    """独立测试函数：直接调用stream_with_unified_supervisor"""
    logger.info("=" * 80)
    logger.info("开始独立测试: 直接调用stream_with_unified_supervisor")
    logger.info("=" * 80)

    # 构造请求
    request = MainGraphRequest(
        input="你好，请问你能帮我做什么？",
        session_id="standalone_test_001",
    )

    logger.info(f"请求参数: input='{request.input}', session_id='{request.session_id}'")

    # 调用流式函数
    stream_iterator = stream_with_unified_supervisor(request)

    # 收集和打印结果
    result_count = 0
    full_content = ""

    try:
        async for result in stream_iterator:
            result_count += 1
            logger.info(f"\n第 {result_count} 条结果:")
            logger.info(f"  - status: {result.status}")
            logger.info(f"  - stream_mode: {result.stream_mode}")

            # 处理不同类型的数据
            if result.status == "success" and result.data:
                if hasattr(result.data, "content") and result.data.content:
                    content = result.data.content
                    full_content += content
                    logger.info(f"  - content: {content}")
                elif isinstance(result.data, dict):
                    logger.info(f"  - data: {result.data}")

            if result.status == "interrupted":
                logger.info(f"  - interrupt_data: {result.interrupt_data}")

            if result.status == "error":
                logger.info(f"  - error_message: {result.error_message}")

    except Exception as e:
        logger.error(f"流式输出过程中出错: {str(e)}", exc_info=True)
        raise

    logger.info(f"\n总结:")
    logger.info(f"  - 总共收到 {result_count} 条流式结果")
    logger.info(f"  - 完整内容长度: {len(full_content)} 字符")
    if full_content:
        logger.info(f"  - 完整内容: {full_content}")

    logger.info("=" * 80)
    logger.info("独立测试完成")
    logger.info("=" * 80)

    # 断言
    assert result_count > 0, "应该至少收到一条流式结果"


if __name__ == "__main__":
    """直接运行测试"""
    import sys
    import os

    # 确保项目根目录在Python路径中
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # 运行独立测试
    asyncio.run(test_stream_output_standalone())
