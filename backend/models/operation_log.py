"""
操作日志模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from database import Base


class OperationLog(Base):
    """管理员操作日志（审计）"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, nullable=True)      # 操作管理员ID（系统操作时为None）
    admin_name = Column(String(64), default="")     # 操作管理员用户名（冗余，方便查询）
    action = Column(String(128), nullable=False)    # 操作类型
    detail = Column(Text, default="")               # 详情（JSON字符串）
    ip_address = Column(String(45), default="")     # 客户端IP
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "admin_name": self.admin_name,
            "action": self.action,
            "detail": self.detail,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
