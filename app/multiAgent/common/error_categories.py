"""
错误分类模块
"""

from app.utils.logger import logger

# ==================== 异常类型白名单 ====================

# 导入 Pydantic ValidationError (参数校验)
try:
    from pydantic import ValidationError as PydanticValidationError
except ImportError:
    PydanticValidationError = None

# 导入数据库相关异常 (项目使用 psycopg2)
try:
    import psycopg2
    from psycopg2 import Error as Psycopg2Error
except ImportError:
    Psycopg2Error = None

# 导入网络相关异常 (项目使用 requests)
try:
    from requests.exceptions import RequestException
except ImportError:
    RequestException = None

# 导入 XML 解析异常
try:
    from xml.etree.ElementTree import ParseError as XMLParseError
except ImportError:
    XMLParseError = None

# 用户错误类型白名单 (参数校验、数据不存在等)
USER_ERROR_TYPES = tuple(
    filter(None, [
        PydanticValidationError,  # Pydantic 参数校验错误
        ValueError,               # 值错误
        KeyError,                 # 键不存在
        AttributeError,           # 属性不存在
        TypeError,                # 类型错误
        IndexError,               # 索引错误
        FileNotFoundError,        # 文件不存在
    ])
)

# 系统错误类型白名单 (数据库、网络、系统级错误等)
SYSTEM_ERROR_TYPES = tuple(
    filter(None, [
        # 数据库相关
        Psycopg2Error,           # psycopg2 数据库错误
        # 网络相关
        RequestException,        # requests 网络错误
        # XML 解析相关
        XMLParseError,           # XML 解析错误（通常是 API 返回异常）
        # 标准库系统级错误
        ConnectionError,         # 连接错误
        TimeoutError,            # 超时错误
        OSError,                 # 操作系统错误
        IOError,                 # IO 错误
        PermissionError,         # 权限错误
    ])
)


class ToolSystemError(Exception):
    """
    工具系统错误基类（避免与 Python 内置 SystemError 冲突）

    用于封装所有系统级错误（数据库连接、网络错误等），在 stream 层统一捕获

    属性：
        message: 错误消息
        original_exception: 原始异常对象
        context: 额外的上下文信息
    """

    def __init__(self, message: str, original_exception: Exception = None, context: str = None):
        self.message = message
        self.original_exception = original_exception
        self.context = context
        super().__init__(self.message)

    def __str__(self):
        parts = [self.message]
        if self.context:
            parts.append(f"[上下文: {self.context}]")
        if self.original_exception:
            parts.append(f"[原始错误: {type(self.original_exception).__name__}: {self.original_exception}]")
        return " ".join(parts)


class ToolUserError(Exception):
    """
    工具用户错误基类（避免与可能的其他 UserError 冲突）

    用于封装所有用户级错误（参数校验、数据不存在等），在 stream 层统一捕获

    属性：
        message: 错误消息
        original_exception: 原始异常对象
        field: 出错的字段名（可选）
        context: 额外的上下文信息
    """

    def __init__(
        self,
        message: str,
        original_exception: Exception = None,
        field: str = None,
        context: str = None
    ):
        self.message = message
        self.original_exception = original_exception
        self.field = field
        self.context = context
        super().__init__(self.message)

    def __str__(self):
        parts = [self.message]
        if self.field:
            parts.append(f"[字段: {self.field}]")
        if self.context:
            parts.append(f"[上下文: {self.context}]")
        if self.original_exception:
            parts.append(f"[原始错误: {type(self.original_exception).__name__}: {self.original_exception}]")
        return " ".join(parts)


# ==================== 核心转换逻辑 ====================


def convert_exception(exception: Exception, context: str = None):
    """
    将原始异常转换为 ToolSystemError 或 ToolUserError

    这是整个错误处理架构的核心方法，通过异常类型白名单进行精确分类

    Args:
        exception: 原始异常对象
        context: 额外的上下文信息（如工具名、参数等）

    Raises:
        ToolSystemError: 当错误属于系统级错误时
        ToolUserError: 当错误属于用户级错误时
    """
    # 优先检查用户错误类型
    if USER_ERROR_TYPES and isinstance(exception, USER_ERROR_TYPES):
        # 用户错误：参数校验失败、数据不存在等
        message = f"参数错误或数据不存在：{str(exception)[:200]}"

        # 尝试提取字段信息（针对 Pydantic ValidationError）
        field = None
        if hasattr(exception, 'errors') and callable(exception.errors):
            try:
                errors = exception.errors()
                if errors and len(errors) > 0:
                    loc = errors[0].get('loc', ())
                    field = ".".join(str(part) for part in loc) if loc else None
            except Exception:
                pass

        raise ToolUserError(
            message=message,
            original_exception=exception,
            field=field,
            context=context
        ) from exception  # 保留异常链

    # 检查系统错误类型
    elif SYSTEM_ERROR_TYPES and isinstance(exception, SYSTEM_ERROR_TYPES):
        # 系统错误：数据库连接、网络问题等
        message = f"系统暂时无法处理请求：{str(exception)[:200]}"
        raise ToolSystemError(
            message=message,
            original_exception=exception,
            context=context
        ) from exception  # 保留异常链

    else:
        # 未在白名单中的异常，默认作为系统错误处理
        logger.warning(
            f"异常类型 {type(exception).__name__} 未在白名单中，默认归类为系统错误"
        )
        message = f"系统发生未知错误：{str(exception)[:200]}"
        raise ToolSystemError(
            message=message,
            original_exception=exception,
            context=context
        ) from exception  # 保留异常链
