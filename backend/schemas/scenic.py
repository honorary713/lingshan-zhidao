"""
景区/景点 Pydantic 模型
"""
from typing import Optional
from pydantic import BaseModel, Field


class ScenicAreaCreate(BaseModel):
    """创建景区"""
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    hours: str = ""
    ticket_info: str = ""
    transport_info: str = ""
    image_url: str = ""
    sort_order: int = 0


class ScenicAreaUpdate(BaseModel):
    """更新景区"""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    hours: Optional[str] = None
    ticket_info: Optional[str] = None
    transport_info: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class ScenicSpotCreate(BaseModel):
    """创建景点"""
    scenic_area_id: int
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    image_url: str = ""
    sort_order: int = 0


class ScenicSpotUpdate(BaseModel):
    """更新景点"""
    scenic_area_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
