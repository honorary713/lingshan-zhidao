"""
数字人配置 + 敏感词管理 API
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from models.digital_human import DigitalHumanConfig, SensitiveWord
from schemas.digital_human import DHConfigUpdate, SensitiveWordCreate, SensitiveWordUpdate, SensitiveWordBatch
from middleware.auth_middleware import get_current_admin
from services.operation_log_service import record_log_dict
from utils.response import success_response, error_response, paginated_response

router = APIRouter()


# ==================== 数字人配置 ====================

def _get_or_create_config(db: Session) -> DigitalHumanConfig:
    """获取配置单例，不存在则创建"""
    config = db.query(DigitalHumanConfig).first()
    if not config:
        config = DigitalHumanConfig(id=1)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("/digital-human/config")
def get_config(db: Session = Depends(get_db)):
    """获取数字人配置（游客端公开访问）"""
    config = _get_or_create_config(db)
    return success_response(config.to_dict())



@router.put("/digital-human/config")
def update_config(
    req: DHConfigUpdate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新数字人配置"""
    config = _get_or_create_config(db)
    update_data = req.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)

    record_log_dict(db, admin.id, admin.username, "update_dh_config",
                    update_data, request.client.host if request.client else "")

    return success_response(config.to_dict(), "数字人配置更新成功")


# ==================== 敏感词管理 ====================

@router.get("/sensitive-words")
def list_sensitive_words(
    page: int = 1, page_size: int = 50,
    category: str = "",
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取敏感词列表"""
    query = db.query(SensitiveWord)
    if category:
        query = query.filter(SensitiveWord.category == category)
    total = query.count()
    items = query.order_by(SensitiveWord.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return paginated_response(
        [w.to_dict() for w in items], total, page, page_size
    )


@router.post("/sensitive-words")
def add_sensitive_word(
    req: SensitiveWordCreate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """添加敏感词"""
    word = SensitiveWord(word=req.word, category=req.category)
    db.add(word)
    db.commit()
    db.refresh(word)

    record_log_dict(db, admin.id, admin.username, "add_sensitive_word",
                    {"word": req.word}, request.client.host if request.client else "")

    return success_response(word.to_dict(), "敏感词添加成功")


@router.put("/sensitive-words/{word_id}")
def update_sensitive_word(
    word_id: int, req: SensitiveWordUpdate, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新敏感词"""
    word = db.query(SensitiveWord).filter(SensitiveWord.id == word_id).first()
    if not word:
        return error_response(404, "敏感词不存在")

    update_data = req.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(word, key, value)
    db.commit()

    record_log_dict(db, admin.id, admin.username, "update_sensitive_word",
                    {"id": word_id, **update_data},
                    request.client.host if request.client else "")

    return success_response(word.to_dict(), "敏感词更新成功")


@router.delete("/sensitive-words/{word_id}")
def delete_sensitive_word(
    word_id: int, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除敏感词"""
    word = db.query(SensitiveWord).filter(SensitiveWord.id == word_id).first()
    if not word:
        return error_response(404, "敏感词不存在")

    db.delete(word)
    db.commit()

    record_log_dict(db, admin.id, admin.username, "delete_sensitive_word",
                    {"id": word_id}, request.client.host if request.client else "")

    return success_response(None, "敏感词已删除")


@router.post("/sensitive-words/batch")
def batch_import(
    req: SensitiveWordBatch, request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """批量导入敏感词（每行一个）"""
    lines = [line.strip() for line in req.words.split("\n") if line.strip()]
    added = 0
    for line in lines:
        existing = db.query(SensitiveWord).filter(SensitiveWord.word == line).first()
        if not existing:
            db.add(SensitiveWord(word=line, category=req.category))
            added += 1
    db.commit()

    record_log_dict(db, admin.id, admin.username, "batch_import_sensitive_words",
                    {"count": added}, request.client.host if request.client else "")

    return success_response({"added_count": added}, f"成功导入 {added} 个敏感词")
