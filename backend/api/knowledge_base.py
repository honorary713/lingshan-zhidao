"""
★ 知识库重建 API（最核心集成点）
"""
import os
from pathlib import Path
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from models.admin import AdminUser
from middleware.auth_middleware import get_current_admin
from services.knowledge_service import rebuild_faiss_index
from services.operation_log_service import record_log_dict
from config import FAISS_INDEX_PATH
from utils.response import success_response, error_response

router = APIRouter()


@router.post("/knowledge-base/rebuild")
def rebuild_knowledge_base(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    从数据库重建 FAISS 知识库索引。
    数据来源：启用的景区 + 景点 + FAQ。
    保存到现有项目的 faiss_scenic_index/ 目录，CLI 程序立即可用。
    """
    try:
        result = rebuild_faiss_index(db)
    except Exception as e:
        return error_response(500, f"知识库重建失败：{str(e)}")

    # 记录操作日志
    record_log_dict(db, admin.id, admin.username, "rebuild_knowledge_base",
                    {"chunk_count": result.get("chunk_count", 0),
                     "source_count": result.get("source_count", 0)},
                    request.client.host if request.client else "")

    if result.get("success"):
        return success_response(result, result.get("message", "知识库重建成功"))
    else:
        return error_response(400, result.get("message", "知识库重建失败"), result)


@router.get("/knowledge-base/status")
def get_kb_status(
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取知识库索引状态信息"""
    status = {
        "index_path": str(FAISS_INDEX_PATH),
        "exists": FAISS_INDEX_PATH.exists(),
    }
    if FAISS_INDEX_PATH.exists():
        faiss_file = FAISS_INDEX_PATH / "index.faiss"
        pkl_file = FAISS_INDEX_PATH / "index.pkl"
        if faiss_file.exists():
            status["faiss_size"] = faiss_file.stat().st_size
            status["faiss_updated"] = Path(faiss_file).stat().st_mtime
        if pkl_file.exists():
            status["pkl_size"] = pkl_file.stat().st_size
    return success_response(status)
