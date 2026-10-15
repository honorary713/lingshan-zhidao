"""
认证中间件：JWT 校验依赖 & 角色守卫
"""
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from services.auth_service import decode_access_token

security = HTTPBearer()


def get_current_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """
    从 JWT token 解析当前管理员，验证有效性。
    此函数作为 FastAPI 依赖注入使用。
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

    admin_id = payload.get("sub")
    if admin_id is None:
        raise HTTPException(status_code=401, detail="Token 格式错误")

    admin = db.query(AdminUser).filter(
        AdminUser.id == int(admin_id),
        AdminUser.is_active == True
    ).first()
    if admin is None:
        raise HTTPException(status_code=401, detail="管理员不存在或已被禁用")

    return admin


def require_role(role: str):
    """
    角色守卫工厂函数。
    用法：Depends(require_role("super_admin"))
    """
    def role_checker(admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
        if admin.role != role and admin.role != "super_admin":
            raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")
        return admin
    return role_checker
