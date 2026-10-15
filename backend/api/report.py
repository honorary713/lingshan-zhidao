"""
游客感受度报告 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from middleware.auth_middleware import get_current_admin
from services.report_service import build_report_data, generate_ai_analysis
from utils.response import success_response

router = APIRouter()


@router.get("/report/data")
def get_report_data(
    period: str = "daily",
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取报告原始统计数据（含热门问题、评分分布、情感趋势）"""
    data = build_report_data(db, period)
    return success_response(data)


@router.get("/report/analysis")
def get_report_analysis(
    period: str = "daily",
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取 AI 生成的游客感受度分析报告"""
    # 先汇总数据
    data = build_report_data(db, period)
    # 再调 AI 生成分析
    ai_result = generate_ai_analysis(data)
    return success_response({
        "data": data,
        "ai": ai_result
    })
