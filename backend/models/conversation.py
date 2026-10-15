"""
对话历史模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from database import Base


class ConversationHistory(Base):
    """游客与AI数字人的对话记录"""
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    user_identifier = Column(String(128), default="")     # 游客标识（设备指纹/IP等）
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    retrieved_docs = Column(Text, default="")              # JSON: 检索到的知识文档片段
    is_sensitive_blocked = Column(Boolean, default=False)  # 是否被敏感词拦截
    rating = Column(Integer, nullable=True)                # 1-5 评分，1/2分为低分可移入待解决
    feedback = Column(Text, default="")                    # 游客文字反馈

    # 新增：低分对话移入待解决问题标记
    moved_to_pending = Column(Boolean, default=False, comment="是否已移入待解决问题列表")
    unresolved_id = Column(Integer, ForeignKey("unresolved_questions.id"), nullable=True, comment="关联待解决问题ID")

    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_identifier": self.user_identifier,
            "question": self.question,
            "answer": self.answer,
            "retrieved_docs": self.retrieved_docs,
            "is_sensitive_blocked": self.is_sensitive_blocked,
            "rating": self.rating,
            "feedback": self.feedback,
            # 新增返回前端字段
            "moved_to_pending": self.moved_to_pending,
            "unresolved_id": self.unresolved_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }