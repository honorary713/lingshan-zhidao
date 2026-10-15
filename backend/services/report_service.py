"""
游客感受度报告服务
聚合对话数据 + AI 分析 → 生成报告
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.conversation import ConversationHistory
from models.faq import UnresolvedQuestion
from models.visitor import VisitorRecord


def _get_date_range(period: str):
    """根据 period 返回起止日期"""
    now = datetime.now()
    if period == "weekly":
        start = now - timedelta(days=7)
    elif period == "monthly":
        start = now - timedelta(days=30)
    else:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def build_report_data(db: Session, period: str = "daily") -> dict:
    """
    聚合报告所需的原始数据
    """
    start, end = _get_date_range(period)

    base = db.query(ConversationHistory).filter(
        ConversationHistory.created_at >= start
    )

    # 核心指标
    total_questions = base.count()
    total_sessions = db.query(func.count(func.distinct(
        ConversationHistory.session_id
    ))).filter(
        ConversationHistory.created_at >= start
    ).scalar() or 0

    avg_rating = base.filter(ConversationHistory.rating != None)
    avg_rating_val = db.query(func.avg(ConversationHistory.rating)).filter(
        ConversationHistory.rating != None,
        ConversationHistory.created_at >= start
    ).scalar()
    avg_rating_val = round(float(avg_rating_val), 2) if avg_rating_val else 0.0

    rated_count = base.filter(ConversationHistory.rating != None).count()
    positive_count = base.filter(ConversationHistory.rating >= 4).count()
    positive_rate = round(positive_count / rated_count * 100, 1) if rated_count > 0 else 0.0

    # 游客来访人次
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_visitors = db.query(VisitorRecord).filter(
        VisitorRecord.created_at >= today_start
    ).count()

    week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_visitors = db.query(VisitorRecord).filter(
        VisitorRecord.created_at >= week_start
    ).count()

    # 热门问题 TOP10
    hot = db.query(
        ConversationHistory.question,
        func.count(ConversationHistory.id).label("cnt")
    ).filter(
        ConversationHistory.created_at >= start
    ).group_by(
        ConversationHistory.question
    ).order_by(
        func.count(ConversationHistory.id).desc()
    ).limit(10).all()

    hot_questions = [{"question": h.question[:30], "count": h.cnt} for h in hot]

    # 评分分布
    excellent = base.filter(ConversationHistory.rating == 5).count()
    good = base.filter(ConversationHistory.rating == 4).count()
    fair = base.filter(ConversationHistory.rating == 3).count()
    poor = base.filter(ConversationHistory.rating <= 2).count()

    # 情感趋势（按天：平均评分 + 提问量）
    trend_days = 30 if period in ("weekly", "monthly") else 1
    trend_results = db.query(
        func.date(ConversationHistory.created_at).label("date"),
        func.avg(ConversationHistory.rating).label("avg_r"),
        func.count(ConversationHistory.id).label("cnt")
    ).filter(
        ConversationHistory.created_at >= (datetime.now() - timedelta(days=trend_days)),
        ConversationHistory.rating != None
    ).group_by(
        func.date(ConversationHistory.created_at)
    ).order_by(
        func.date(ConversationHistory.created_at)
    ).all()

    sentiment_trend = [
        {
            "date": str(r.date),
            "avg_rating": round(float(r.avg_r), 2) if r.avg_r else 0.0,
            "count": r.cnt
        }
        for r in trend_results
    ]

    # 待解决问题数
    pending = db.query(UnresolvedQuestion).filter(
        UnresolvedQuestion.status == "pending"
    ).count()

    return {
        "period": period,
        "total_questions": total_questions,
        "total_sessions": total_sessions,
        "avg_rating": avg_rating_val,
        "positive_rate": positive_rate,
        "today_visitors": today_visitors,
        "week_visitors": week_visitors,
        "hot_questions": hot_questions,
        "rating_dist": {"excellent": excellent, "good": good, "fair": fair, "poor": poor},
        "sentiment_trend": sentiment_trend,
        "pending_unresolved": pending,
    }


def generate_ai_analysis(data: dict) -> dict:
    """
    把聚合数据喂给 AI 模型，生成分析报告 + 服务建议
    """
    hot_text = "\n".join([
        f"- {h['question']}（{h['count']}次）"
        for h in data.get("hot_questions", [])[:8]
    ])

    prompt = f"""作为景区运营分析人员，请根据以下数据生成一份游客感受度分析。

数据概览：
时间段：{data['period']}
提问总数：{data['total_questions']}
游客会话数：{data['total_sessions']}
平均评分：{data['avg_rating']}分（满分5分）
好评率：{data['positive_rate']}%
评分分布：好评{data['rating_dist']['excellent']}条，较好{data['rating_dist']['good']}条，一般{data['rating_dist']['fair']}条，差评{data['rating_dist']['poor']}条
待解决问题：{data['pending_unresolved']}个
今日来访：{data.get('today_visitors', '-')}人

游客最常问的问题：
{hot_text if hot_text else '暂无数据'}

请生成以下内容：
首先写一段游客关注点分析，约100字，分析游客主要关心哪些方面。
然后写一段满意度评价，约100字，评估整体服务情况。
最后列出3到5条改进建议，每条用-开头。

直接输出结果。"""

    try:
        from app.services.llm import llm_service
        ai_text = llm_service.chat([{"role": "user", "content": prompt}]).strip()

        # 简单切分三段
        lines = ai_text.split("\n")
        analysis = ""
        sentiment = ""
        suggestions = []
        section = 0
        for line in lines:
            if "建议" in line or line.startswith("•"):
                section = 2
            elif "情感" in line or "满意度" in line or "趋势" in line:
                section = 1
            if section == 0:
                analysis += line
            elif section == 1:
                sentiment += line
            elif section == 2:
                if line.strip():
                    suggestions.append(line.strip().lstrip("•").strip())

        return {
            "analysis": analysis[:300] or "暂无关注点分析数据",
            "sentiment": sentiment[:300] or "暂无情感趋势数据",
            "suggestions": suggestions[:5] or ["暂无服务建议"],
            "raw": ai_text
        }
    except Exception as e:
        return {
            "analysis": f"AI分析暂时不可用（{str(e)[:50]}）",
            "sentiment": "请检查模型服务是否正常",
            "suggestions": ["建议联系技术人员排查"],
            "raw": ""
        }
