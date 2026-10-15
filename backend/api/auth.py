"""
认证 API：登录、获取当前管理员信息
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from schemas.auth import LoginRequest
from services.auth_service import verify_password, create_access_token
from middleware.auth_middleware import get_current_admin
from utils.response import success_response, error_response

router = APIRouter()


@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """管理员登录"""
    admin = db.query(AdminUser).filter(
        AdminUser.username == req.username,
        AdminUser.is_active == True
    ).first()

    if not admin or not verify_password(req.password, admin.password_hash):
        return error_response(401, "用户名或密码错误")

    token = create_access_token({"sub": str(admin.id), "role": admin.role})
    return success_response({
        "token": token,
        "token_type": "bearer",
        "admin": admin.to_dict()
    }, "登录成功")


@router.get("/auth/me")
def get_me(admin: AdminUser = Depends(get_current_admin)):
    """获取当前登录管理员信息"""
    return success_response(admin.to_dict())
