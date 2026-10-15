from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from database import Base


class VisitorRecord(Base):
    """每次游客来访记录（点一次按钮记一条）"""
    __tablename__ = "visitor_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }