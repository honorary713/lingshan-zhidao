"""
统计数据 Pydantic 模型
"""
from typing import Optional, List
from pydantic import BaseModel


class StatsOverview(BaseModel):
    """统计概览"""
    total_questions: int = 0
    total_sessions: int = 0
    avg_rating: float = 0.0
    positive_rate: float = 0.0     # 好评率（4-5分）
    active_areas: int = 0
    pending_unresolved: int = 0
    today_questions: int = 0


class HotQuestion(BaseModel):
    """热门问题"""
    question: str
    count: int
    last_asked: Optional[str] = None


class AccuracyStat(BaseModel):
    """准确率统计"""
    excellent: int = 0     # 5分
    good: int = 0          # 4分
    fair: int = 0          # 3分
    poor: int = 0          # 1-2分
    total: int = 0


class SatisfactionTrend(BaseModel):
    """满意度趋势"""
    date: str
    avg_rating: float
    question_count: int
