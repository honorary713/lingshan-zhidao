"""
黑名单模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from database import Base


class Blacklist(Base):
    """游客黑名单"""
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_identifier = Column(String(128), nullable=False)
    reason = Column(Text, default="")
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=True)  # 操作管理员
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self, admin_name=""):
        return {
            "id": self.id,
            "user_identifier": self.user_identifier,
            "reason": self.reason,
            "admin_id": self.admin_id,
            "admin_name": admin_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
