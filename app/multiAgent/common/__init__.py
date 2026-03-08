"""
多Agent系统通用模块
提供数据库连接等通用功能
仅支持PostgreSQL连接
"""

from app.utils.config import get_db_connection_string
from typing import Optional, Dict, Any, List
import threading
import psycopg2
from psycopg2.extras import RealDictCursor
from queue import Queue
import time

# 数据库连接池
_db_pool = None
_pool_lock = threading.Lock()
_pool_size = 10  # 连接池大小

class DatabaseConnection:
    """数据库连接类，提供查询和执行功能"""
    
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor(cursor_factory=RealDictCursor)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """执行查询并返回结果列表"""
        try:
            # 如果params为None，使用空元组
            if params is None:
                params = ()
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            raise Exception(f"查询执行失败: {str(e)}")
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """执行更新操作并返回影响的行数"""
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return self.cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            raise Exception(f"更新执行失败: {str(e)}")
    
    def close(self):
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

def _initialize_pool():
    """初始化PostgreSQL数据库连接池"""
    global _db_pool
    
    connection_string = get_db_connection_string()
    if not connection_string:
        raise ValueError("PostgreSQL连接字符串未配置")
    
    if not connection_string.startswith("postgresql://"):
        raise ValueError(f"不支持的数据库连接字符串格式: {connection_string}")
    
    # 使用Python内置队列实现简单的连接池
    try:
        _db_pool = Queue(maxsize=_pool_size)
        
        # 创建初始连接
        for _ in range(_pool_size):
            connection = psycopg2.connect(connection_string)
            _db_pool.put(connection)
            
    except Exception as e:
        raise Exception(f"初始化PostgreSQL连接池失败: {str(e)}")

def get_db_connection() -> DatabaseConnection:
    """获取数据库连接"""
    global _db_pool
    
    with _pool_lock:
        if _db_pool is None:
            _initialize_pool()
    
    try:
        # 从连接池获取连接，设置超时时间
        connection = _db_pool.get(timeout=30)
        return DatabaseConnection(connection)
    except Exception as e:
        raise Exception(f"获取数据库连接失败: {str(e)}")

def release_db_connection(connection: DatabaseConnection):
    """释放数据库连接回连接池"""
    try:
        # 重置连接状态
        if connection.connection and not connection.connection.closed:
            connection.connection.rollback()  # 回滚任何未提交的事务
        _db_pool.put(connection.connection)
    except Exception as e:
        # 如果连接有问题，创建新连接
        try:
            connection_string = get_db_connection_string()
            new_connection = psycopg2.connect(connection_string)
            _db_pool.put(new_connection)
        except:
            pass  # 忽略创建新连接的失败

def execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
    """执行查询并返回结果（简化接口）"""
    conn = get_db_connection()
    try:
        return conn.execute_query(query, params)
    finally:
        release_db_connection(conn)

def execute_update(query: str, params: Optional[tuple] = None) -> int:
    """执行更新操作（简化接口）"""
    conn = get_db_connection()
    try:
        return conn.execute_update(query, params)
    finally:
        release_db_connection(conn)

# 导出主要功能
__all__ = ['get_db_connection', 'execute_query', 'execute_update', 'DatabaseConnection', 'release_db_connection']
