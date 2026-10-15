"""
数字人配置 Pydantic 模型
"""
from typing import Optional
from pydantic import BaseModel, Field

class DHConfigUpdate(BaseModel):
    """数字人配置更新"""
    name: Optional[str] = Field(None, max_length=64)
    scenic_area: Optional[str] = Field(None, max_length=128)
    status: Optional[str] = None  # online / offline
    model_path: Optional[str] = Field(None, max_length=256)  # 新增：Live2D 模型路径
    voice_timbre: Optional[str] = Field(None, max_length=32)
    voice_speed: Optional[float] = Field(None, ge=0.5, le=3.0)
    voice_intonation: Optional[float] = Field(None, ge=0.5, le=3.0)
    ai_model: Optional[str] = Field(None, max_length=64)
    ai_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    ai_max_tokens: Optional[int] = Field(None, ge=64, le=4096)
    ai_system_prompt: Optional[str] = None
    ai_response_style: Optional[str] = None

class SensitiveWordCreate(BaseModel):
    """添加敏感词"""
    word: str = Field(..., min_length=1, max_length=128)
    category: str = Field(default="general", max_length=32)

class SensitiveWordUpdate(BaseModel):
    """更新敏感词"""
    word: Optional[str] = Field(None, min_length=1, max_length=128)
    category: Optional[str] = Field(None, max_length=32)
    is_active: Optional[bool] = None

class SensitiveWordBatch(BaseModel):
    """批量导入敏感词"""
    words: str = Field(..., description="每行一个敏感词")
    category: str = Field(default="general", max_length=32)