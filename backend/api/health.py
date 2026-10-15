"""
健康检查端点：检查数据库、FAISS、LLM API 连通性
"""
import time
from fastapi import APIRouter
from sqlalchemy import text
from config import FAISS_INDEX_PATH
from database import SessionLocal

router = APIRouter()


@router.get("/health")
def health_check():
    check_results = {
        "status": "ok",
        "checks": {}
    }

    # 1. 数据库检查
    db_start = time.perf_counter()
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        check_results["checks"]["database"] = {
            "status": "ok",
            "latency_ms": round((time.perf_counter() - db_start) * 1000, 1)
        }
    except Exception as e:
        check_results["checks"]["database"] = {"status": "error", "message": str(e)[:100]}
        check_results["status"] = "degraded"

    # 2. FAISS 索引检查
    if FAISS_INDEX_PATH.exists():
        faiss_file = FAISS_INDEX_PATH / "index.faiss"
        if faiss_file.exists():
            check_results["checks"]["faiss_index"] = {
                "status": "ok",
                "size_kb": round(faiss_file.stat().st_size / 1024, 1),
                "path": str(FAISS_INDEX_PATH)
            }
        else:
            check_results["checks"]["faiss_index"] = {"status": "warning", "message": "index.faiss 文件不存在"}
            if check_results["status"] == "ok":
                check_results["status"] = "degraded"
    else:
        check_results["checks"]["faiss_index"] = {"status": "empty", "message": "尚未构建知识库索引"}

    # 3. SiliconFlow API 检查
    api_start = time.perf_counter()
    try:
        from services.embedding_service import _get_api_credentials
        api_key, _ = _get_api_credentials()
        if api_key:
            check_results["checks"]["llm_api"] = {
                "status": "ok",
                "latency_ms": round((time.perf_counter() - api_start) * 1000, 1)
            }
        else:
            check_results["checks"]["llm_api"] = {"status": "warning", "message": "API 密钥未配置"}
    except Exception as e:
        check_results["checks"]["llm_api"] = {"status": "error", "message": str(e)[:100]}
        check_results["status"] = "degraded"

    return check_results
