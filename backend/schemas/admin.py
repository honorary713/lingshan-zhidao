"""
管理员 Pydantic 模型
"""
from typing import Optional
from pydantic import BaseModel, Field


class AdminCreate(BaseModel):
    """创建管理员"""
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)
    nickname: str = Field(..., min_length=1, max_length=64)
    role: str = Field(default="admin")  # admin / super_admin


class AdminUpdate(BaseModel):
    """更新管理员"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=64)
    role: Optional[str] = None  # admin / super_admin
    is_active: Optional[bool] = None


class PasswordReset(BaseModel):
    """重置密码"""
    new_password: str = Field(..., min_length=4, max_length=128)
