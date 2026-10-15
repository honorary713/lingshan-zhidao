"""
数据统计 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from middleware.auth_middleware import get_current_admin
from services.stats_service import (
    get_overview, get_hot_questions, get_accuracy_stats, get_satisfaction_trend
)
from utils.response import success_response

router = APIRouter()


@router.get("/stats/overview")
def stats_overview(
    period: str = "daily",
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取统计概览（period: daily/weekly/monthly）"""
    data = get_overview(db, period)
    return success_response(data)


@router.get("/stats/hot-questions")
def hot_questions(
    limit: int = 20,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取热门问题排行"""
    data = get_hot_questions(db, limit=limit)
    return success_response(data)


@router.get("/stats/accuracy")
def accuracy_stats(
    period: str = "daily",  # 新增
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取回答准确率统计（评分分布）"""
    data = get_accuracy_stats(db)
    return success_response(data)


@router.get("/stats/satisfaction")
def satisfaction_trend(
    days: int = 30,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取满意度趋势"""
    data = get_satisfaction_trend(db, days=days)
    return success_response(data)
@router.post("/stats/visitor-tap")
def tap_visitor(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """模拟进人：点一次按钮记录一位游客"""
    from services.stats_service import add_visitor
    data = add_visitor(db)
    return success_response(data, f"今日已接待 {data['today_visitors']} 人")


@router.get("/stats/visitor-counts")
def visitor_counts(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取来访人次统计"""
    from services.stats_service import get_visitor_counts
    data = get_visitor_counts(db)
    return success_response(data)
