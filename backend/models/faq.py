"""
FAQ 问答 + 待解决问题模型
采用 is_active 软删除方案：删除不物理移除数据，仅标记失效，列表查询自动过滤失效数据
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class FAQ(Base):
    """常见问题与标准答案（管理员后台录入知识库，软删除依靠is_active字段）"""
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False, comment="标准问题")
    answer = Column(Text, nullable=False, comment="标准回答")
    category = Column(String(64), default="general", comment="分类：tickets门票, transport交通, accommodation住宿, food餐饮等")
    sort_order = Column(Integer, default=0, comment="排序权重")
    is_active = Column(Boolean, default=True, comment="是否启用，False=已软删除，列表接口不会展示、重建知识库不会读取")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 反向关联：这条FAQ对应的已收录待解决问题
    unresolved_links = relationship("UnresolvedQuestion", back_populates="bind_faq")

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "sort_order": self.sort_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UnresolvedQuestion(Base):
    """游客提出的待解决问题，管理员完善答案后可绑定为FAQ"""
    __tablename__ = "unresolved_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False, comment="游客提问内容")
    ask_count = Column(Integer, default=1, comment="重复询问次数")
    status = Column(String(16), default="pending", comment="状态：pending待处理 / resolved已转为FAQ / ignored忽略")
    faq_id = Column(Integer, ForeignKey("faqs.id"), nullable=True, comment="绑定的FAQ主键，仅status=resolved时有值")
    created_at = Column(DateTime, default=datetime.now, comment="首次提问时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="最后更新时间")

    # 正向关联绑定的FAQ
    bind_faq = relationship("FAQ", back_populates="unresolved_links")

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "ask_count": self.ask_count,
            "status": self.status,
            "faq_id": self.faq_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }