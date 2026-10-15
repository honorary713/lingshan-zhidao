"""
管理员账号管理 API（超管专属）
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from schemas.admin import AdminCreate, AdminUpdate, PasswordReset
from middleware.auth_middleware import get_current_admin, require_role
from services.auth_service import hash_password
from services.operation_log_service import record_log_dict
from utils.response import success_response, error_response, paginated_response

router = APIRouter()


@router.get("/admins")
def list_admins(
    page: int = 1, page_size: int = 20,
    admin: AdminUser = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """获取管理员列表"""
    query = db.query(AdminUser)
    total = query.count()
    items = query.order_by(AdminUser.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return paginated_response(
        [a.to_dict() for a in items], total, page, page_size
    )


@router.post("/admins")
def create_admin(
    req: AdminCreate, request: Request,
    admin: AdminUser = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """创建管理员"""
    existing = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if existing:
        return error_response(400, "用户名已存在")

    new_admin = AdminUser(
        username=req.username,
        password_hash=hash_password(req.password),
        nickname=req.nickname,
        role=req.role if req.role in ("super_admin", "admin") else "admin"
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    record_log_dict(db, admin.id, admin.username, "create_admin",
                    {"target": new_admin.username, "role": new_admin.role},
                    request.client.host if request.client else "")

    return success_response(new_admin.to_dict(), "管理员创建成功")


@router.put("/admins/{admin_id}")
def update_admin(
    admin_id: int, req: AdminUpdate, request: Request,
    current_admin: AdminUser = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """更新管理员信息"""
    target = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if not target:
        return error_response(404, "管理员不存在")

    if req.nickname is not None:
        target.nickname = req.nickname
    if req.role is not None and req.role in ("super_admin", "admin"):
        target.role = req.role
    if req.is_active is not None:
        target.is_active = req.is_active

    db.commit()
    db.refresh(target)

    record_log_dict(db, current_admin.id, current_admin.username, "update_admin",
                    {"target": target.username, "changes": req.model_dump(exclude_none=True)},
                    request.client.host if request.client else "")

    return success_response(target.to_dict(), "管理员更新成功")


@router.delete("/admins/{admin_id}")
def delete_admin(
    admin_id: int, request: Request,
    current_admin: AdminUser = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """软删除管理员（设为禁用）"""
    if admin_id == current_admin.id:
        return error_response(400, "不能禁用自己")

    target = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if not target:
        return error_response(404, "管理员不存在")

    target.is_active = False
    db.commit()

    record_log_dict(db, current_admin.id, current_admin.username, "delete_admin",
                    {"target": target.username},
                    request.client.host if request.client else "")

    return success_response(None, "管理员已禁用")


@router.put("/admins/{admin_id}/password")
def reset_password(
    admin_id: int, req: PasswordReset, request: Request,
    current_admin: AdminUser = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """重置管理员密码"""
    target = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if not target:
        return error_response(404, "管理员不存在")

    target.password_hash = hash_password(req.new_password)
    db.commit()

    record_log_dict(db, current_admin.id, current_admin.username, "reset_password",
                    {"target": target.username},
                    request.client.host if request.client else "")

    return success_response(None, "密码重置成功")
