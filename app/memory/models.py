"""长期记忆系统数据模型"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class MemoryType(str, Enum):
    """记忆类型枚举"""
    GENERAL = "general"  # 通用记忆
    ENTERPRISE_PROFILE = "enterprise_profile"  # 企业画像
    INTERACTION = "interaction"  # 交互记录
    KNOWLEDGE = "knowledge"  # 知识记忆
    PREFERENCE = "preference"  # 偏好记忆


class StorageType(str, Enum):
    """存储类型枚举"""
    MEMORY = "memory"  # 内存存储
    FILE = "file"  # 文件存储
    DATABASE = "database"  # 数据库存储
    VECTOR = "vector"  # 向量存储


@dataclass
class MemoryRecord:
    """记忆记录数据模型"""
    
    id: str  # 唯一标识符
    content: str  # 记忆内容
    memory_type: MemoryType  # 记忆类型
    metadata: Dict[str, Any]  # 元数据
    embedding: Optional[List[float]] = None  # 向量嵌入
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间
    access_count: int = 0  # 访问次数
    importance_score: float = 0.0  # 重要性评分
    tags: List[str] = field(default_factory=list)  # 标签
    agent_id: Optional[str] = None  # 所属智能体ID
    session_id: Optional[str] = None  # 会话ID
    user_id: Optional[str] = None  # 用户ID
    expires_at: Optional[datetime] = None  # 过期时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "metadata": self.metadata,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count,
            "importance_score": self.importance_score,
            "tags": self.tags,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryRecord":
        """从字典创建"""
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            metadata=data["metadata"],
            embedding=data.get("embedding"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            access_count=data.get("access_count", 0),
            importance_score=data.get("importance_score", 0.0),
            tags=data.get("tags", []),
            agent_id=data.get("agent_id"),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
        )


@dataclass
class EnterpriseProfileMemory:
    """企业画像专用记忆结构"""
    
    enterprise_id: str  # 企业ID
    enterprise_name: str  # 企业名称
    basic_info: Dict[str, Any]  # 基础信息
    financial_data: Dict[str, Any]  # 财务数据
    credit_info: Dict[str, Any]  # 信用信息
    industry_analysis: Dict[str, Any]  # 行业分析
    green_attributes: Dict[str, Any]  # 绿色属性
    risk_assessment: Dict[str, Any]  # 风险评估
    interaction_history: List[Dict[str, Any]]  # 交互历史
    last_updated: datetime  # 最后更新时间
    confidence_score: float = 0.0  # 数据置信度
    data_sources: List[str] = field(default_factory=list)  # 数据来源
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enterprise_id": self.enterprise_id,
            "enterprise_name": self.enterprise_name,
            "basic_info": self.basic_info,
            "financial_data": self.financial_data,
            "credit_info": self.credit_info,
            "industry_analysis": self.industry_analysis,
            "green_attributes": self.green_attributes,
            "risk_assessment": self.risk_assessment,
            "interaction_history": self.interaction_history,
            "last_updated": self.last_updated.isoformat(),
            "confidence_score": self.confidence_score,
            "data_sources": self.data_sources,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnterpriseProfileMemory":
        """从字典创建"""
        return cls(
            enterprise_id=data["enterprise_id"],
            enterprise_name=data["enterprise_name"],
            basic_info=data["basic_info"],
            financial_data=data["financial_data"],
            credit_info=data["credit_info"],
            industry_analysis=data["industry_analysis"],
            green_attributes=data["green_attributes"],
            risk_assessment=data["risk_assessment"],
            interaction_history=data["interaction_history"],
            last_updated=datetime.fromisoformat(data["last_updated"]),
            confidence_score=data.get("confidence_score", 0.0),
            data_sources=data.get("data_sources", []),
        )


@dataclass
class SearchQuery:
    """搜索查询参数"""
    
    query: Optional[str] = None  # 查询文本
    embedding: Optional[List[float]] = None  # 查询向量
    filters: Optional[Dict[str, Any]] = None  # 过滤条件
    memory_type: Optional[MemoryType] = None  # 记忆类型
    agent_id: Optional[str] = None  # 智能体ID
    session_id: Optional[str] = None  # 会话ID
    user_id: Optional[str] = None  # 用户ID
    tags: Optional[List[str]] = None  # 标签
    time_range: Optional[Tuple[datetime, datetime]] = None  # 时间范围
    limit: int = 10  # 返回数量限制
    offset: int = 0  # 偏移量
    sort_by: str = "relevance"  # 排序方式: relevance, recency, importance, access_count
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "embedding": self.embedding,
            "filters": self.filters,
            "memory_type": self.memory_type.value if self.memory_type else None,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tags": self.tags,
            "time_range": (
                self.time_range[0].isoformat(),
                self.time_range[1].isoformat()
            ) if self.time_range else None,
            "limit": self.limit,
            "offset": self.offset,
            "sort_by": self.sort_by,
        }


@dataclass
class SearchResult:
    """搜索结果"""
    
    memories: List[MemoryRecord]  # 记忆列表
    total_count: int  # 总数量
    query_time_ms: float  # 查询时间（毫秒）
    query: SearchQuery  # 原始查询
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "memories": [memory.to_dict() for memory in self.memories],
            "total_count": self.total_count,
            "query_time_ms": self.query_time_ms,
            "query": self.query.to_dict(),
        }
