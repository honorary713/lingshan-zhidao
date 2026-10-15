"""
FAQ 管理 API
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from models.faq import FAQ
from schemas.faq import FAQCreate, FAQUpdate
from middleware.auth_middleware import get_current_admin
from services.operation_log_service import record_log_dict
from utils.response import success_response, error_response, paginated_response
# 新增导入向量重建函数
from utils.faiss_loader import rebuild_faiss_index

router = APIRouter()


@router.get("/faqs")
def list_faqs(
    page: int = 1, page_size: int = 50,
    category: str = "",
    keyword: str = "",
    # 修改：默认None时自动筛选is_active=True，前端页面不传参只展示有效FAQ
    is_active: bool = None,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    获取 FAQ 列表
    - 不传is_active：仅返回未删除（is_active=True）的正常FAQ（前端页面默认走这个逻辑）
    - 传is_active=False：仅查询已软删除的FAQ（后台恢复功能专用）
    - 传is_active=True：仅查询正常启用FAQ
    """
    query = db.query(FAQ)

    # 默认过滤：只展示启用、未删除的FAQ
    if is_active is None:
        query = query.filter(FAQ.is_active == True)
    else:
        query = query.filter(FAQ.is_active == is_active)

    if category:
        query = query.filter(FAQ.category == category)
    if keyword:
        query = query.filter(FAQ.question.contains(keyword))

    total = query.count()
    items = query.order_by(FAQ.sort_order, FAQ.id).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return paginated_response(
        [f.to_dict() for f in items], total, page, page_size
    )


@router.post("/faqs")
def create_faq(
    req: FAQCreate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建 FAQ"""
    faq = FAQ(**req.model_dump())
    db.add(faq)
    db.commit()
    db.refresh(faq)

    # 新增FAQ后自动重建向量库
    rebuild_faiss_index()

    record_log_dict(db, admin.id, admin.username, "create_faq",
                    {"question": req.question[:50]},
                    request.client.host if request.client else "")

    return success_response(faq.to_dict(), "FAQ 创建成功")


@router.put("/faqs/{faq_id}")
def update_faq(
    faq_id: int, req: FAQUpdate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新 FAQ，可恢复已删除FAQ（修改is_active=True）"""
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        return error_response(404, "FAQ 不存在")

    update_data = req.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(faq, key, value)
    db.commit()
    db.refresh(faq)

    # 修改FAQ后自动重建向量库
    rebuild_faiss_index()

    record_log_dict(db, admin.id, admin.username, "update_faq",
                    {"id": faq_id, "changes": update_data},
                    request.client.host if request.client else "")

    return success_response(faq.to_dict(), "FAQ 更新成功")


@router.delete("/faqs/{faq_id}")
def delete_faq(
    faq_id: int, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """软删除 FAQ：仅标记is_active=False，不会物理删除数据"""
    # 增加校验：只允许删除正常启用的FAQ，防止重复删除
    faq = db.query(FAQ).filter(FAQ.id == faq_id, FAQ.is_active == True).first()
    if not faq:
        return error_response(404, "FAQ 不存在或已删除")

    faq.is_active = False
    db.commit()

    # 删除FAQ后自动重建向量库
    rebuild_faiss_index()

    record_log_dict(db, admin.id, admin.username, "delete_faq",
                    {"id": faq_id},
                    request.client.host if request.client else "")

    return success_response(None, "FAQ 已删除")


# 新增：手动一键同步向量库接口
@router.post("/faqs/rebuild-index")
def manual_rebuild_faq_index(
    admin: AdminUser = Depends(get_current_admin)
):
    """手动触发全量FAQ向量库重建"""
    rebuild_faiss_index()
    return success_response(None, "向量知识库同步完成")