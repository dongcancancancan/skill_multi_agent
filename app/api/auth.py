"""
认证API模块，处理用户登录和token管理
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional
import secrets
import time
from app.utils.postgresql_client import get_postgresql_client
from app.utils.logger import app_logger as logger
from app.utils.snowflake import SnowflakeGenerator

# 创建雪花ID生成器（本地实现）
# machine_id 是机器ID，范围 0-1023，可根据部署调整以避免跨实例冲突
generator = SnowflakeGenerator(machine_id=0)

# 内存中存储token和用户信息
token_store = {}
security = HTTPBearer()

router = APIRouter(prefix="/api/auth", tags=["认证"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    expires_at: datetime

class UserInfo(BaseModel):
    username: str
    userid: str
    login_time: datetime

def verify_token(token: str) -> Optional[UserInfo]:
    """验证token有效性"""
    if token in token_store:
        user_info = token_store[token]
        # 检查token是否过期（1天有效期）
        if datetime.now() < user_info["expires_at"]:
            # 返回完整的 UserInfo，确保包含 userid 字段
            return UserInfo(
                username=user_info.get("username"),
                userid=str(user_info.get("userid")) if user_info.get("userid") is not None else "",
                login_time=user_info.get("login_time"),
            )
        else:
            # token过期，从存储中移除
            del token_store[token]
    return None

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response):
    """用户登录接口"""
    # 简单的用户名密码验证（实际项目中应该使用数据库验证）
    if request.username and request.password:
        # 根据用户名查询数据库：存在则校验密码，否则新增用户
        import hashlib

        client = get_postgresql_client()
        query_table_sql = (
            "SELECT id, password_hash FROM sys_user "
            "WHERE username = %s AND del_flag = 0"
        )
        logger.info("执行查询用户SQL: %s", query_table_sql % request.username)
        try:
            result = client.execute_query(query_table_sql, (request.username,))
        except Exception as e:
            logger.error(f"数据库查询失败: {e}")
            raise HTTPException(status_code=500, detail="内部数据库错误")

        logger.info("查询用户结果: %s", result)

        # 计算传入密码的 hash（使用 sha256，若需更强加密请切换到 bcrypt）
        pw_hash = hashlib.sha256(request.password.encode("utf-8")).hexdigest()
        id = None
        if result:
            # 用户存在，校验密码
            user = result[0]
            stored_hash = user.get("password_hash")
            if stored_hash != pw_hash:
                raise HTTPException(status_code=401, detail="用户名或密码错误")
            logger.info("用户 %s 验证通过", request.username)
            # 从查询结果读取用户 id（转换为字符串以便统一存储）
            id = str(user.get("id")) if user.get("id") is not None else None
        else:
            # 用户不存在，插入新用户
            
            # 生成雪花ID
            new_id = generator.next_id()
            insert_sql = (
                "INSERT INTO sys_user (id,username, password_hash, del_flag, create_time) "
                "VALUES (%s,%s, %s, 0, NOW())"
            )
            try:
                client.execute_dml(insert_sql, (new_id,request.username, pw_hash))
                logger.info("已创建新用户: %s", request.username)
                id = str(new_id)
            except Exception as e:
                logger.error(f"创建用户失败: {e}")
                raise HTTPException(status_code=500, detail="创建用户失败")
        # 生成随机token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=1)
        
        # 存储token信息
        token_store[token] = {
            "username": request.username,
            "login_time": datetime.now(),
            "expires_at": expires_at,
            "userid": id
        }
        
        # 设置cookie（可选）
        response.set_cookie(
            key="session_token",
            value=token,
            expires=expires_at.timestamp(),
            httponly=True,
            samesite="lax"
        )
        
        return LoginResponse(token=token, expires_at=expires_at)
    else:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

@router.post("/logout")
async def logout(response: Response, token: str = Depends(security)):
    """用户登出接口"""
    token_value = token.credentials
    if token_value in token_store:
        del token_store[token_value]
    
    # 清除cookie
    response.delete_cookie(key="session_token")
    return {"message": "登出成功"}

@router.get("/verify")
async def verify_token_endpoint(token: str = Depends(security)):
    """验证token有效性"""
    token_value = token.credentials
    user_info = verify_token(token_value)
    if user_info:
        return {"valid": True, "user": user_info}
    else:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
