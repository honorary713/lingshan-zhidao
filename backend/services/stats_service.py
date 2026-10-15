"""
统计服务：汇总对话数据生成统计指标
"""
from datetime import datetime, timedelta
from sqlalchemy import func, extract, and_
from sqlalchemy.orm import Session
from models.conversation import ConversationHistory
from models.scenic import ScenicArea, ScenicSpot
from models.faq import FAQ, UnresolvedQuestion


def get_overview(db: Session, period: str = "daily") -> dict:
    """
    获取统计概览。
    period: daily / weekly / monthly
    """
    now = datetime.now()

    if period == "weekly":
        start_date = now - timedelta(days=7)
    elif period == "monthly":
        start_date = now - timedelta(days=30)
    else:  # daily
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 期间内对话统计
    period_query = db.query(ConversationHistory).filter(
        ConversationHistory.created_at >= start_date
    )

    total_questions = period_query.count()
    total_sessions = db.query(func.count(func.distinct(ConversationHistory.session_id))).filter(
        ConversationHistory.created_at >= start_date
    ).scalar() or 0

    # 平均评分
    avg_rating_result = db.query(func.avg(ConversationHistory.rating)).filter(
        ConversationHistory.rating != None,
        ConversationHistory.created_at >= start_date
    ).scalar()
    avg_rating = round(float(avg_rating_result), 2) if avg_rating_result else 0.0

    # 好评率（4-5分）
    positive_count = period_query.filter(ConversationHistory.rating >= 4).count()
    rated_count = period_query.filter(ConversationHistory.rating != None).count()
    positive_rate = round(positive_count / rated_count * 100, 1) if rated_count > 0 else 0.0

    # 活跃景区数
    active_areas = db.query(ScenicArea).filter(ScenicArea.is_active == True).count()

    # 待处理未解决问题数
    pending_unresolved = db.query(UnresolvedQuestion).filter(
        UnresolvedQuestion.status == "pending"
    ).count()

    # 今日问题数
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_questions = db.query(ConversationHistory).filter(
        ConversationHistory.created_at >= today_start
    ).count()
    # 今日和本周来访人次
    from models.visitor import VisitorRecord
    today_visitors = db.query(VisitorRecord).filter(
        VisitorRecord.created_at >= today_start
    ).count()

    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_visitors = db.query(VisitorRecord).filter(
        VisitorRecord.created_at >= week_start
    ).count()
    return {
        "total_questions": total_questions,
        "total_sessions": total_sessions,
        "avg_rating": avg_rating,
        "positive_rate": positive_rate,
        "active_areas": active_areas,
        "pending_unresolved": pending_unresolved,
        "today_questions": today_questions,
        "period": period,
        "today_visitors": today_visitors,
        "week_visitors": week_visitors,
    }


def get_hot_questions(db: Session, limit: int = 20) -> list[dict]:
    """获取热门问题排行（按出现次数排序）"""
    results = db.query(
        ConversationHistory.question,
        func.count(ConversationHistory.id).label("count"),
        func.max(ConversationHistory.created_at).label("last_asked")
    ).group_by(
        ConversationHistory.question
    ).order_by(
        func.count(ConversationHistory.id).desc()
    ).limit(limit).all()

    return [
        {
            "question": r.question,
            "count": r.count,
            "last_asked": r.last_asked.isoformat() if r.last_asked else None
        }
        for r in results
    ]


def get_accuracy_stats(db: Session, period: str = "daily") -> dict:
    """获取回答准确率统计（基于评分分布）"""
    from sqlalchemy import case as sa_case

    now = datetime.now()
    if period == "weekly":
        start_date = now - timedelta(days=7)
    elif period == "monthly":
        start_date = now - timedelta(days=30)
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    base_query = db.query(ConversationHistory).filter(
        ConversationHistory.created_at >= start_date
    )

    results = db.query(
        func.sum(sa_case((ConversationHistory.rating == 5, 1), else_=0)).label("excellent"),
        func.sum(sa_case((ConversationHistory.rating == 4, 1), else_=0)).label("good"),
        func.sum(sa_case((ConversationHistory.rating == 3, 1), else_=0)).label("fair"),
        func.sum(sa_case((ConversationHistory.rating <= 2, 1), else_=0)).label("poor"),
        func.count(ConversationHistory.rating).label("rated"),  # 已评
        func.count(ConversationHistory.id).label("total")  # 全部
    ).filter(ConversationHistory.rating != None).first()

    # 没有评分数据时返回全0
    if results is None or results.total == 0:
        return {"excellent": 0, "good": 0, "fair": 0, "poor": 0, "total": 0}

    return {
        "excellent": results.excellent or 0,
        "good": results.good or 0,
        "fair": results.fair or 0,
        "poor": results.poor or 0,
        "rated": results.rated or 0,
        "unrated": (results.total or 0) - (results.rated or 0),
        "total": results.total or 0,
    }


def get_satisfaction_trend(db: Session, days: int = 30) -> list[dict]:
    """获取满意度趋势（最近N天的每日评分）"""
    start_date = datetime.now() - timedelta(days=days)

    results = db.query(
        func.date(ConversationHistory.created_at).label("date"),
        func.avg(ConversationHistory.rating).label("avg_rating"),
        func.count(ConversationHistory.id).label("question_count")
    ).filter(
        ConversationHistory.created_at >= start_date,
        ConversationHistory.rating != None
    ).group_by(
        func.date(ConversationHistory.created_at)
    ).order_by(
        func.date(ConversationHistory.created_at)
    ).all()

    return [
        {
            "date": str(r.date),
            "avg_rating": round(float(r.avg_rating), 2) if r.avg_rating else 0.0,
            "question_count": r.question_count
        }
        for r in results
    ]

# ========== 游客来访人次统计 ==========

def add_visitor(db: Session) -> dict:
    """新增一条来访记录（模拟进人按钮）"""
    from models.visitor import VisitorRecord
    record = VisitorRecord()
    db.add(record)
    db.commit()
    db.refresh(record)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(VisitorRecord).filter(
        VisitorRecord.created_at >= today
    ).count()

    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_count = db.query(VisitorRecord).filter(
        VisitorRecord.created_at >= week_start
    ).count()

    total_count = db.query(VisitorRecord).count()

    return {
        "today_visitors": today_count,
        "week_visitors": week_count,
        "total_visitors": total_count,
    }


def get_visitor_counts(db: Session) -> dict:
    """获取当前来访人次统计"""
    from models.visitor import VisitorRecord

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(VisitorRecord).filter(
        VisitorRecord.created_at >= today
    ).count()

    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_count = db.query(VisitorRecord).filter(
        VisitorRecord.created_at >= week_start
    ).count()

    total_count = db.query(VisitorRecord).count()

    return {
        "today_visitors": today_count,
        "week_visitors": week_count,
        "total_visitors": total_count,
    }