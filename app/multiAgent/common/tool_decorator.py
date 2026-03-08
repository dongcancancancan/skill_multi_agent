"""
工具装饰器 - 统一错误处理
自动将工具函数的原始异常转换为 SystemError/UserError

架构说明：
- 保持 handle_tool_errors=False，让错误冒泡到 stream 层
- 在工具执行时自动捕获原始异常（ValidationError、DatabaseError 等）
- 调用 convert_exception() 自动转换为 SystemError/UserError
- 保留完整的错误上下文（工具名、参数等）
- 特别处理 GraphBubbleUp：让 interrupt() 的异常直接向上抛出
"""

from functools import wraps
from typing import Callable, Any
from app.utils.logger import logger
from app.multiAgent.common.error_categories import ToolSystemError, ToolUserError, convert_exception
from langgraph.errors import GraphBubbleUp
import inspect


def with_error_handling(func: Callable) -> Callable:
    """
    工具错误处理装饰器

    功能：
    1. 自动捕获工具函数抛出的原始异常
    2. 使用 ToolErrorHandler 将原始异常转换为 SystemError/UserError
    3. 保留完整的错误上下文（工具名、参数等）

    使用方式：
        @tool("my_tool")
        @with_error_handling
        def my_tool(param: str) -> dict:
            # 工具逻辑
            pass

    注意：此装饰器应放在 @tool 装饰器之后（即更靠近函数定义）

    错误转换流程：
    1. 工具抛出 ValidationError/DatabaseError 等原始异常
    2. 装饰器捕获原始异常
    3. 调用 convert_exception() 转换
    4. 抛出 SystemError 或 UserError
    5. 异常冒泡到 stream 层统一处理
    """

    # 获取工具名称（从函数名或工具配置中提取）
    tool_name = getattr(func, 'name', func.__name__)

    # 判断是否为异步函数
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except GraphBubbleUp:
                raise
            except (ToolSystemError, ToolUserError):
                # 如果已经是自定义错误，直接向上抛出（避免重复转换）
                raise
            except Exception as e:
                # 捕获原始异常并转换
                logger.debug(
                    f"工具 [{tool_name}] 抛出原始异常，正在转换: "
                    f"{type(e).__name__}: {str(e)[:200]}"
                )

                # 构建上下文信息
                context = f"工具: {tool_name}"

                # 自动转换并抛出 ToolSystemError 或 ToolUserError
                convert_exception(exception=e, context=context)

        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except GraphBubbleUp:
                raise
            except (ToolSystemError, ToolUserError):
                # 如果已经是自定义错误，直接向上抛出（避免重复转换）
                raise
            except Exception as e:
                # 捕获原始异常并转换
                logger.debug(
                    f"工具 [{tool_name}] 抛出原始异常，正在转换: "
                    f"{type(e).__name__}: {str(e)[:200]}"
                )

                # 构建上下文信息
                context = f"工具: {tool_name}"

                # 自动转换并抛出 ToolSystemError 或 ToolUserError
                convert_exception(exception=e, context=context)

        return sync_wrapper
