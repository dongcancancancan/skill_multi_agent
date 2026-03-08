from langchain_core.messages import AIMessage, AIMessageChunk
from pydantic import BaseModel, Field
from typing import List, Any, Literal, Optional, Union
import uuid


class BaseRequest(BaseModel):
    """请求模型基类"""

    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="会话ID，如果未提供则自动生成",
    )
    is_resume: bool = Field(default=False, description="是否为恢复中断的请求")


class MainGraphRequest(BaseRequest):
    """主图代理请求模型"""

    input: str = Field(..., min_length=1, description="用户的输入内容，不能为空")
    token: str = Field(..., min_length=1, description="token，不能为空")
    company_name: Optional[str] = Field(None, description="目标公司名称")
    query_type: Optional[str] = Field(None, description="查询/任务类型")
    metadata: Optional[dict] = Field(
        None, description="附加的元数据，用于提供上下文信息"
    )

class GraphStreamResult(BaseModel):
    """图流式结果模型"""

    status: Literal["success", "error", "interrupted"] = Field(..., description="状态")
    stream_mode: Optional[str] = Field(None, description="流式模式")
    data: Optional[Any] = Field(None, description="流式数据")
    interrupt_data: Optional[Any] = Field(None, description="中断提示")
    error_message: Optional[str] = Field(None, description="错误信息")
    trace_info: Optional[Any] = Field(None, description="溯源信息")
    thinking: Optional[Any] = Field(None, description="思考信息")
