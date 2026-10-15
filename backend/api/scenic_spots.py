"""
景点管理 API
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models.admin import AdminUser
from models.scenic import ScenicSpot, ScenicArea
from schemas.scenic import ScenicSpotCreate, ScenicSpotUpdate
from middleware.auth_middleware import get_current_admin
from services.operation_log_service import record_log_dict
from utils.response import success_response, error_response, paginated_response

router = APIRouter()


@router.get("/scenic-spots")
def list_spots(
    page: int = 1, page_size: int = 50,
    area_id: int = None,
    is_active: bool = None,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取景点列表"""
    query = db.query(ScenicSpot).options(joinedload(ScenicSpot.area))
    if area_id:
        query = query.filter(ScenicSpot.scenic_area_id == area_id)
    if is_active is not None:
        query = query.filter(ScenicSpot.is_active == is_active)
    total = query.count()
    items = query.order_by(ScenicSpot.sort_order, ScenicSpot.id).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return paginated_response(
        [s.to_dict() for s in items], total, page, page_size
    )


@router.post("/scenic-spots")
def create_spot(
    req: ScenicSpotCreate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建景点"""
    # 验证景区存在
    area = db.query(ScenicArea).filter(ScenicArea.id == req.scenic_area_id).first()
    if not area:
        return error_response(400, "所属景区不存在")

    spot = ScenicSpot(**req.model_dump())
    db.add(spot)
    db.commit()
    db.refresh(spot)
    # 重新加载关联
    spot = db.query(ScenicSpot).options(joinedload(ScenicSpot.area)).filter(ScenicSpot.id == spot.id).first()

    record_log_dict(db, admin.id, admin.username, "create_scenic_spot",
                    {"name": spot.name, "area": spot.area.name if spot.area else ""},
                    request.client.host if request.client else "")

    return success_response(spot.to_dict(), "景点创建成功")


@router.put("/scenic-spots/{spot_id}")
def update_spot(
    spot_id: int, req: ScenicSpotUpdate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新景点"""
    spot = db.query(ScenicSpot).filter(ScenicSpot.id == spot_id).first()
    if not spot:
        return error_response(404, "景点不存在")

    update_data = req.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(spot, key, value)
    db.commit()
    spot = db.query(ScenicSpot).options(joinedload(ScenicSpot.area)).filter(ScenicSpot.id == spot_id).first()

    record_log_dict(db, admin.id, admin.username, "update_scenic_spot",
                    {"id": spot_id, "changes": update_data},
                    request.client.host if request.client else "")

    return success_response(spot.to_dict(), "景点更新成功")


@router.delete("/scenic-spots/{spot_id}")
def delete_spot(
    spot_id: int, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """软删除景点"""
    spot = db.query(ScenicSpot).filter(ScenicSpot.id == spot_id).first()
    if not spot:
        return error_response(404, "景点不存在")

    spot.is_active = False
    db.commit()

    record_log_dict(db, admin.id, admin.username, "delete_scenic_spot",
                    {"id": spot_id, "name": spot.name},
                    request.client.host if request.client else "")

    return success_response(None, "景点已删除")
