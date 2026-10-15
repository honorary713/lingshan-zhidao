"""
系统配置 Pydantic 模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    """创建API密钥"""
    key_name: str = Field(..., min_length=1, max_length=64)
    provider: str = Field(..., min_length=1, max_length=32)
    api_key: str = Field(..., min_length=1, max_length=512)
    api_secret: str = ""
    base_url: str = Field(default="", max_length=256)


class ApiKeyUpdate(BaseModel):
    """更新API密钥"""
    key_name: Optional[str] = Field(None, min_length=1, max_length=64)
    api_key: Optional[str] = Field(None, min_length=1, max_length=512)
    api_secret: Optional[str] = None
    base_url: Optional[str] = Field(None, max_length=256)
    is_active: Optional[bool] = None


class SystemConfigItem(BaseModel):
    """单个系统配置项"""
    config_key: str
    config_value: str


class SystemConfigBulkUpdate(BaseModel):
    """批量更新系统配置"""
    configs: List[SystemConfigItem]
