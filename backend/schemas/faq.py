"""
FAQ Pydantic 模型
"""
from typing import Optional
from pydantic import BaseModel, Field


class FAQCreate(BaseModel):
    """创建FAQ"""
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    category: str = Field(default="general", max_length=64)
    sort_order: int = 0


class FAQUpdate(BaseModel):
    """更新FAQ"""
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = Field(None, max_length=64)
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class UnresolvedResolve(BaseModel):
    """解决未解决问题（转为FAQ）"""
    answer: str = Field(..., min_length=1)
    category: str = Field(default="general", max_length=64)
