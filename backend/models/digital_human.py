"""
数字人配置模型 + 敏感词模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from database import Base

class DigitalHumanConfig(Base):
    """数字人单例配置（只有一行数据，id=1）"""
    __tablename__ = "digital_human_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, default="AI导游")
    scenic_area = Column(String(128), nullable=False, default="校园智导")
    status = Column(String(16), nullable=False, default="online")  # online / offline

    # 数字人外观
    model_path = Column(String(256), default="/live2d/hiyori/hiyori_free_t08.model3.json")

    # 语音参数
    voice_timbre = Column(String(32), default="111")  # 百度精品音库：度小萌（甜美活泼女声）
    voice_speed = Column(Float, default=1.0)       # 0.5 ~ 3.0
    voice_intonation = Column(Float, default=1.0)   # 音调

    # AI 模型参数
    ai_model = Column(String(64), default="deepseek-chat")  # DeepSeek V3
    ai_temperature = Column(Float, default=0.1)     # 0.0 ~ 2.0
    ai_max_tokens = Column(Integer, default=512)
    ai_system_prompt = Column(Text, default="")
    ai_response_style = Column(Text, default="")

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "scenic_area": self.scenic_area,
            "status": self.status,
            "model_path": self.model_path,
            "voice_timbre": self.voice_timbre,
            "voice_speed": self.voice_speed,
            "voice_intonation": self.voice_intonation,
            "ai_model": self.ai_model,
            "ai_temperature": self.ai_temperature,
            "ai_max_tokens": self.ai_max_tokens,
            "ai_system_prompt": self.ai_system_prompt,
            "ai_response_style": self.ai_response_style,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class SensitiveWord(Base):
    """敏感词"""
    __tablename__ = "sensitive_words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(128), nullable=False)
    category = Column(String(32), default="general")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "word": self.word,
            "category": self.category,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }