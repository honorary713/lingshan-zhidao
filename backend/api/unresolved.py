"""
待解决问题管理 API
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from models.faq import FAQ

from models.faq import FAQ, UnresolvedQuestion
from schemas.faq import UnresolvedResolve
from middleware.auth_middleware import get_current_admin
from services.operation_log_service import record_log_dict
from utils.response import success_response, error_response, paginated_response

router = APIRouter()


@router.get("/unresolved-questions")
def list_unresolved(
    page: int = 1, page_size: int = 50,
    status: str = "",
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取待解决问题列表"""
    query = db.query(UnresolvedQuestion)
    if status:
        query = query.filter(UnresolvedQuestion.status == status)
    total = query.count()
    items = query.order_by(UnresolvedQuestion.ask_count.desc(), UnresolvedQuestion.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return paginated_response(
        [u.to_dict() for u in items], total, page, page_size
    )


@router.put("/unresolved-questions/{q_id}/resolve")
def resolve_question(
    q_id: int, req: UnresolvedResolve, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """将待解决问题转为 FAQ"""
    unresolved = db.query(UnresolvedQuestion).filter(UnresolvedQuestion.id == q_id).first()
    if not unresolved:
        return error_response(404, "待解决问题不存在")

    # 创建 FAQ
    faq = FAQ(
        question=unresolved.question,
        answer=req.answer,
        category=req.category
    )
    db.add(faq)
    db.flush()  # 获取 faq.id

    # 更新待解决问题状态
    unresolved.status = "resolved"
    unresolved.faq_id = faq.id
    db.commit()

    record_log_dict(db, admin.id, admin.username, "resolve_unresolved_question",
                    {"id": q_id, "question": unresolved.question[:50], "faq_id": faq.id},
                    request.client.host if request.client else "")

    return success_response({
        "unresolved": unresolved.to_dict(),
        "faq": faq.to_dict()
    }, "已转为 FAQ")


@router.put("/unresolved-questions/{q_id}/ignore")
def ignore_question(
    q_id: int, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """忽略待解决问题"""
    unresolved = db.query(UnresolvedQuestion).filter(UnresolvedQuestion.id == q_id).first()
    if not unresolved:
        return error_response(404, "待解决问题不存在")

    unresolved.status = "ignored"
    db.commit()

    record_log_dict(db, admin.id, admin.username, "ignore_unresolved_question",
                    {"id": q_id},
                    request.client.host if request.client else "")

    return success_response(unresolved.to_dict(), "已忽略该问题")


@router.delete("/unresolved-questions/{q_id}")
def delete_question(
    q_id: int, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除待解决问题"""
    unresolved = db.query(UnresolvedQuestion).filter(UnresolvedQuestion.id == q_id).first()
    if not unresolved:
        return error_response(404, "待解决问题不存在")

    db.delete(unresolved)
    db.commit()

    record_log_dict(db, admin.id, admin.username, "delete_unresolved_question",
                    {"id": q_id},
                    request.client.host if request.client else "")

    return success_response(None, "已删除")