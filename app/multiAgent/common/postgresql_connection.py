"""
PostgreSQL数据库连接模块
专门用于PostgreSQL数据库操作
"""

import psycopg2
from psycopg2 import pool
from typing import Optional, Dict, Any, List, Tuple
from app.utils.config import get_config, get_db_connection_string
from app.utils.logger import get_logger
import threading

logger = get_logger(__name__)

class PostgreSQLConnection:
    """PostgreSQL数据库连接类，提供查询和执行功能"""
    
    def __init__(self, connection_string: str = None):
        if connection_string:
            self.connection_string = connection_string
        else:
            # 使用配置中的PostgreSQL连接字符串（通过修复函数确保密码正确编码）
            self.connection_string = get_db_connection_string()
        self.connection = None
        self.cursor = None
        
    def connect(self) -> bool:
        """建立数据库连接"""
        self.connection = psycopg2.connect(self.connection_string)
        self.cursor = self.connection.cursor()
        logger.info("PostgreSQL连接成功建立")
        return True
            
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """执行查询并返回结果列表"""
        if not self.connection or self.connection.closed:
            self.connect()
            
        # 如果params为None，使用空元组
        if params is None:
            params = ()
            
        self.cursor.execute(query, params)
        
        # 获取列名
        if self.cursor.description:
            columns = [desc[0] for desc in self.cursor.description]
            results = []
            for row in self.cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        else:
            return []
    
    def execute_update(self, query: str, params: Optional[Tuple] = None) -> int:
        """执行更新操作并返回影响的行数"""
        if not self.connection or self.connection.closed:
            self.connect()
            
        self.cursor.execute(query, params or ())
        self.connection.commit()
        return self.cursor.rowcount
    
    def close(self):
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.debug("PostgreSQL连接已关闭")

# PostgreSQL连接池
_postgresql_pool = None
_pool_lock = threading.Lock()
_min_connections = 1
_max_connections = 10

def _initialize_postgresql_pool():
    """初始化PostgreSQL连接池"""
    global _postgresql_pool
    
    # 使用修复函数确保密码正确编码
    connection_string = get_db_connection_string()
    if not connection_string:
        raise ValueError("未配置PostgreSQL连接字符串")
    
    # 使用psycopg2内置的连接池，添加更多连接参数
    try:
        _postgresql_pool = pool.SimpleConnectionPool(
            _min_connections, 
            _max_connections, 
            connection_string
        )
        logger.info("PostgreSQL连接池初始化成功")
    except Exception as e:
        logger.error(f"初始化PostgreSQL连接池失败: {str(e)}")
        raise Exception(f"初始化PostgreSQL连接池失败: {str(e)}")

def get_postgresql_connection() -> PostgreSQLConnection:
    """获取PostgreSQL数据库连接"""
    global _postgresql_pool
    
    with _pool_lock:
        if _postgresql_pool is None:
            _initialize_postgresql_pool()
    
    try:
        # 从连接池获取连接，设置超时
        raw_connection = _postgresql_pool.getconn(timeout=5)
        
        # 检查连接是否有效
        if raw_connection.closed:
            logger.warning("从连接池获取的连接已关闭，重新创建连接")
            # 使用修复函数确保密码正确编码
            raw_connection = psycopg2.connect(get_db_connection_string())
        
        # 包装成PostgreSQLConnection对象
        connection = PostgreSQLConnection()
        connection.connection = raw_connection
        connection.cursor = raw_connection.cursor()
        return connection
        
    except Exception as e:
        logger.error(f"从连接池获取连接失败: {str(e)}")
        # 如果连接池获取失败，直接创建新连接
        connection = PostgreSQLConnection()
        connection.connect()
        return connection

def release_postgresql_connection(connection: PostgreSQLConnection):
    """释放PostgreSQL数据库连接回连接池"""
    if connection.connection:
        try:
            if not connection.connection.closed:
                connection.connection.rollback()  # 回滚任何未提交的事务
                _postgresql_pool.putconn(connection.connection)
            else:
                logger.warning("尝试释放已关闭的连接")
        except Exception as e:
            logger.error(f"释放连接回连接池失败: {str(e)}")
            # 如果连接池操作失败，直接关闭连接
            connection.close()

def execute_postgresql_query(query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """执行PostgreSQL查询并返回结果（简化接口）"""
    conn = get_postgresql_connection()
    try:
        return conn.execute_query(query, params)
    finally:
        release_postgresql_connection(conn)

def execute_postgresql_update(query: str, params: Optional[Tuple] = None) -> int:
    """执行PostgreSQL更新操作（简化接口）"""
    conn = get_postgresql_connection()
    try:
        return conn.execute_update(query, params)
    finally:
        release_postgresql_connection(conn)

# 导出主要功能
__all__ = [
    'PostgreSQLConnection', 
    'get_postgresql_connection', 
    'execute_postgresql_query', 
    'execute_postgresql_update',
    'release_postgresql_connection'
]
