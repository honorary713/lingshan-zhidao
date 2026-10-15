"""
认证相关 Pydantic 模型
"""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    token_type: str = "bearer"
    admin: dict


class AdminInfo(BaseModel):
    """当前管理员信息"""
    id: int
    username: str
    nickname: str
    role: str
    is_active: bool
