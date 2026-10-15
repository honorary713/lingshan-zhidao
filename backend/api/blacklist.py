"""
黑名单管理 API
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.admin import AdminUser
from models.blacklist import Blacklist
from schemas.blacklist import BlacklistCreate, BlacklistUpdate
from middleware.auth_middleware import get_current_admin
from services.operation_log_service import record_log_dict
from utils.response import success_response, error_response, paginated_response

router = APIRouter()


@router.get("/blacklist")
def list_blacklist(
    page: int = 1, page_size: int = 50,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取黑名单列表"""
    query = db.query(Blacklist)
    total = query.count()
    items = query.order_by(Blacklist.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 获取管理员名称映射
    admin_ids = set(b.admin_id for b in items if b.admin_id)
    admin_map = {}
    if admin_ids:
        admins = db.query(AdminUser).filter(AdminUser.id.in_(admin_ids)).all()
        admin_map = {a.id: a.username for a in admins}

    return paginated_response(
        [b.to_dict(admin_name=admin_map.get(b.admin_id, "")) for b in items],
        total, page, page_size
    )


@router.post("/blacklist")
def add_blacklist(
    req: BlacklistCreate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """添加黑名单"""
    existing = db.query(Blacklist).filter(
        Blacklist.user_identifier == req.user_identifier
    ).first()
    if existing:
        return error_response(400, "该用户已在黑名单中")

    entry = Blacklist(
        user_identifier=req.user_identifier,
        reason=req.reason,
        admin_id=admin.id
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    record_log_dict(db, admin.id, admin.username, "add_blacklist",
                    {"user": req.user_identifier},
                    request.client.host if request.client else "")

    return success_response(entry.to_dict(admin_name=admin.username), "已加入黑名单")


@router.delete("/blacklist/{entry_id}")
def remove_blacklist(
    entry_id: int, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """移除黑名单"""
    entry = db.query(Blacklist).filter(Blacklist.id == entry_id).first()
    if not entry:
        return error_response(404, "黑名单记录不存在")

    db.delete(entry)
    db.commit()

    record_log_dict(db, admin.id, admin.username, "remove_blacklist",
                    {"id": entry_id, "user": entry.user_identifier},
                    request.client.host if request.client else "")

    return success_response(None, "已移除黑名单")
