"""
景区 + 景点模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class ScenicArea(Base):
    """景区"""
    __tablename__ = "scenic_areas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, default="")
    hours = Column(String(256), default="")         # 开放时间
    ticket_info = Column(Text, default="")          # 门票信息
    transport_info = Column(Text, default="")       # 交通信息
    image_url = Column(String(512), default="")
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联景点
    spots = relationship("ScenicSpot", back_populates="area", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "hours": self.hours,
            "ticket_info": self.ticket_info,
            "transport_info": self.transport_info,
            "image_url": self.image_url,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "spot_count": len(self.spots) if self.spots else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ScenicSpot(Base):
    """景点"""
    __tablename__ = "scenic_spots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenic_area_id = Column(Integer, ForeignKey("scenic_areas.id"), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text, default="")
    image_url = Column(String(512), default="")
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    area = relationship("ScenicArea", back_populates="spots")

    def to_dict(self):
        return {
            "id": self.id,
            "scenic_area_id": self.scenic_area_id,
            "area_name": self.area.name if self.area else "",
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
