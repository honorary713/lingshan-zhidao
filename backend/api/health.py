"""
健康检查端点：检查数据库、FAISS、LLM API 连通性
"""
import time
from pathlib import Path

from fastapi import APIRouter
from sqlalchemy import text
from database import SessionLocal

# Agent 实际使用的知识库索引位置（app/knowledge/indexer.py 产出 lingshan.index + chunks.json），
# 与旧版 admin_portal 的 faiss_scenic_index 不同，health 必须查这个路径才准确。
INDEX_DIR = Path(__file__).resolve().parent.parent / "indexes"
INDEX_FILE = INDEX_DIR / "lingshan.index"
CHUNKS_FILE = INDEX_DIR / "chunks.json"

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

    # 2. FAISS 索引检查（Agent 实际使用的 indexes/lingshan.index + chunks.json）
    if INDEX_FILE.exists() and CHUNKS_FILE.exists():
        check_results["checks"]["faiss_index"] = {
            "status": "ok",
            "size_kb": round(INDEX_FILE.stat().st_size / 1024, 1),
            "path": str(INDEX_DIR),
        }
    elif INDEX_DIR.exists():
        check_results["checks"]["faiss_index"] = {
            "status": "warning",
            "message": "索引文件不完整（缺少 lingshan.index 或 chunks.json）",
        }
        if check_results["status"] == "ok":
            check_results["status"] = "degraded"
    else:
        check_results["checks"]["faiss_index"] = {"status": "empty", "message": "尚未构建知识库索引"}

    # 3. LLM API 密钥检查（校验 app.config.LLM_API_KEY 是否配置）
    api_start = time.perf_counter()
    try:
        from app.config import LLM_API_KEY
        if LLM_API_KEY:
            check_results["checks"]["llm_api"] = {
                "status": "ok",
                "latency_ms": round((time.perf_counter() - api_start) * 1000, 1),
            }
        else:
            check_results["checks"]["llm_api"] = {"status": "warning", "message": "LLM_API_KEY 未配置（将降级为 Mock 模式）"}
    except Exception as e:
        check_results["checks"]["llm_api"] = {"status": "error", "message": str(e)[:100]}
        check_results["status"] = "degraded"

    return check_results
