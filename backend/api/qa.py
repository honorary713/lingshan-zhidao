"""
游客端问答 API（无需认证，供 CLI 程序或前端游客端调用）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from database import get_db
from services.agent_service import answer_with_agent
from services.sensitive_filter import filter_text
from utils.response import success_response, error_response

router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="游客问题")
    session_id: str = Field(default="", max_length=64, description="会话ID")
    user_identifier: str = Field(default="", max_length=128, description="游客标识")


@router.post("/public/ask")
def ask_question(req: AskRequest, db: Session = Depends(get_db)):
    """
    游客问答接口，无需登录认证。
    流程：FAQ精确匹配 → FAQ向量检索 → FAISS文档搜索 → LLM生成 → 敏感词过滤。
    同时自动记录对话历史，知识库无法回答时自动加入待解决问题列表。
    """
    if not req.question.strip():
        return error_response(400, "问题不能为空")

    try:
        result = answer_with_agent(req.question.strip(), db, req.session_id or "api")
    except Exception as e:
        return error_response(500, f"问答服务异常：{str(e)}")

    # 自动保存对话记录
    try:
        from models.conversation import ConversationHistory
        import json
        conv = ConversationHistory(
            session_id=req.session_id or "api",
            user_identifier=req.user_identifier,
            question=req.question.strip(),
            answer=result["answer"],
            retrieved_docs=json.dumps(result.get("sources", []), ensure_ascii=False),
            is_sensitive_blocked=result.get("is_sensitive_blocked", False)
        )
        db.add(conv)
        db.commit()
    except Exception:
        pass

    return success_response({
        "answer": result["answer"],
        "sources": result.get("sources", []),
        "from_faq": result.get("from_faq", False),
        "from_agent": result.get("from_agent", False),
        "is_sensitive_blocked": result.get("is_sensitive_blocked", False)
    })
