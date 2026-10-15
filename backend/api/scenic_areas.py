"""
景区管理 API
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from models.scenic import ScenicArea
from schemas.scenic import ScenicAreaCreate, ScenicAreaUpdate
from middleware.auth_middleware import get_current_admin
from services.operation_log_service import record_log_dict
from utils.response import success_response, error_response, paginated_response

router = APIRouter()


@router.get("/scenic-areas")
def list_areas(
    page: int = 1, page_size: int = 50,
    is_active: bool = None,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取景区列表"""
    query = db.query(ScenicArea)
    if is_active is not None:
        query = query.filter(ScenicArea.is_active == is_active)
    total = query.count()
    items = query.order_by(ScenicArea.sort_order, ScenicArea.id).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return paginated_response(
        [a.to_dict() for a in items], total, page, page_size
    )


@router.post("/scenic-areas")
def create_area(
    req: ScenicAreaCreate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建景区"""
    area = ScenicArea(**req.model_dump())
    db.add(area)
    db.commit()
    db.refresh(area)

    record_log_dict(db, admin.id, admin.username, "create_scenic_area",
                    {"name": area.name},
                    request.client.host if request.client else "")

    return success_response(area.to_dict(), "景区创建成功")


@router.put("/scenic-areas/{area_id}")
def update_area(
    area_id: int, req: ScenicAreaUpdate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新景区"""
    area = db.query(ScenicArea).filter(ScenicArea.id == area_id).first()
    if not area:
        return error_response(404, "景区不存在")

    update_data = req.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(area, key, value)
    db.commit()
    db.refresh(area)

    record_log_dict(db, admin.id, admin.username, "update_scenic_area",
                    {"id": area_id, "changes": update_data},
                    request.client.host if request.client else "")

    return success_response(area.to_dict(), "景区更新成功")


@router.delete("/scenic-areas/{area_id}")
def delete_area(
    area_id: int, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """软删除景区"""
    area = db.query(ScenicArea).filter(ScenicArea.id == area_id).first()
    if not area:
        return error_response(404, "景区不存在")

    area.is_active = False
    db.commit()

    record_log_dict(db, admin.id, admin.username, "delete_scenic_area",
                    {"id": area_id, "name": area.name},
                    request.client.host if request.client else "")

    return success_response(None, "景区已删除")
