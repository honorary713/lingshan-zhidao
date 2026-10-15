"""
操作日志 API
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from models.operation_log import OperationLog
from middleware.auth_middleware import get_current_admin
from utils.response import success_response, error_response, paginated_response

router = APIRouter()


@router.get("/logs")
def list_logs(
    page: int = 1, page_size: int = 30,
    admin_id: int = None,
    action: str = "",
    date_from: str = "", date_to: str = "",
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取操作日志（支持筛选）"""
    query = db.query(OperationLog)

    if admin_id:
        query = query.filter(OperationLog.admin_id == admin_id)
    if action:
        query = query.filter(OperationLog.action == action)
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(OperationLog.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(OperationLog.created_at < dt_to)
        except ValueError:
            pass

    total = query.count()
    items = query.order_by(OperationLog.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return paginated_response(
        [log.to_dict() for log in items], total, page, page_size
    )
