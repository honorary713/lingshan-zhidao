"""
黑名单 Pydantic 模型
"""
from typing import Optional
from pydantic import BaseModel, Field


class BlacklistCreate(BaseModel):
    """添加黑名单"""
    user_identifier: str = Field(..., min_length=1, max_length=128)
    reason: str = ""


class BlacklistUpdate(BaseModel):
    """更新黑名单"""
    user_identifier: Optional[str] = Field(None, min_length=1, max_length=128)
    reason: Optional[str] = None
