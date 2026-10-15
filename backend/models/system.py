"""
系统配置模型：API 密钥 + 全局参数
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from database import Base


class ApiKey(Base):
    """第三方服务 API 密钥"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_name = Column(String(64), nullable=False)                 # 显示名称
    provider = Column(String(32), nullable=False)                 # siliconflow / baidu_asr / baidu_tts
    api_key = Column(String(512), nullable=False)                 # API Key
    api_secret = Column(String(512), default="")                  # Secret Key
    base_url = Column(String(256), default="")                     # API 端点
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self, mask_secret=True):
        data = {
            "id": self.id,
            "key_name": self.key_name,
            "provider": self.provider,
            "api_key": self._mask(self.api_key) if mask_secret else self.api_key,
            "api_secret": self._mask(self.api_secret) if mask_secret and self.api_secret else self.api_secret,
            "base_url": self.base_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        return data

    @staticmethod
    def _mask(s: str) -> str:
        """遮蔽敏感信息，只显示前4后4字符"""
        if len(s) <= 8:
            return s[:2] + "****" + s[-2:]
        return s[:4] + "****" + s[-4:]


class SystemConfig(Base):
    """系统全局参数（键值对）"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(64), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    description = Column(String(256), default="")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dict(self):
        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
