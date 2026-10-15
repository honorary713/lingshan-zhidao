"""
系统配置 API：API 密钥管理 + 全局参数
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from models.system import ApiKey, SystemConfig
from schemas.system import ApiKeyCreate, ApiKeyUpdate, SystemConfigBulkUpdate
from middleware.auth_middleware import get_current_admin
from services.operation_log_service import record_log_dict
from utils.response import success_response, error_response, paginated_response

router = APIRouter()


# ==================== API 密钥管理 ====================

@router.get("/system/api-keys")
def list_api_keys(
    page: int = 1, page_size: int = 50,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取 API 密钥列表（密钥信息已遮蔽）"""
    query = db.query(ApiKey)
    total = query.count()
    items = query.order_by(ApiKey.id).offset((page - 1) * page_size).limit(page_size).all()
    return paginated_response(
        [k.to_dict(mask_secret=True) for k in items], total, page, page_size
    )


@router.post("/system/api-keys")
def create_api_key(
    req: ApiKeyCreate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """添加 API 密钥"""
    key = ApiKey(**req.model_dump())
    db.add(key)
    db.commit()
    db.refresh(key)

    record_log_dict(db, admin.id, admin.username, "create_api_key",
                    {"key_name": req.key_name, "provider": req.provider},
                    request.client.host if request.client else "")

    return success_response(key.to_dict(mask_secret=True), "API 密钥添加成功")


@router.put("/system/api-keys/{key_id}")
def update_api_key(
    key_id: int, req: ApiKeyUpdate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新 API 密钥"""
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        return error_response(404, "API 密钥不存在")

    update_data = req.model_dump(exclude_none=True)
    for k, v in update_data.items():
        setattr(key, k, v)
    db.commit()
    db.refresh(key)

    record_log_dict(db, admin.id, admin.username, "update_api_key",
                    {"id": key_id, "key_name": key.key_name},
                    request.client.host if request.client else "")

    return success_response(key.to_dict(mask_secret=True), "API 密钥更新成功")


@router.delete("/system/api-keys/{key_id}")
def delete_api_key(
    key_id: int, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除 API 密钥"""
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not key:
        return error_response(404, "API 密钥不存在")

    db.delete(key)
    db.commit()

    record_log_dict(db, admin.id, admin.username, "delete_api_key",
                    {"id": key_id, "key_name": key.key_name},
                    request.client.host if request.client else "")

    return success_response(None, "API 密钥已删除")


# ==================== 系统全局参数 ====================

@router.get("/system/configs")
def get_system_configs(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取所有全局配置"""
    configs = db.query(SystemConfig).all()
    return success_response({c.config_key: c.config_value for c in configs})


@router.put("/system/configs")
def update_system_configs(
    req: SystemConfigBulkUpdate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """批量更新全局配置"""
    for item in req.configs:
        config = db.query(SystemConfig).filter(
            SystemConfig.config_key == item.config_key
        ).first()
        if config:
            config.config_value = item.config_value
        else:
            db.add(SystemConfig(config_key=item.config_key, config_value=item.config_value))
    db.commit()

    record_log_dict(db, admin.id, admin.username, "update_system_configs",
                    {"keys": [c.config_key for c in req.configs]},
                    request.client.host if request.client else "")

    return success_response(None, "系统配置更新成功")
