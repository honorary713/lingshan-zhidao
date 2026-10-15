import json
import os
from typing import Any

from sqlalchemy.orm import Session


def _active_api_key(db: Session, providers: list[str]):
    from models.system import ApiKey

    for provider in providers:
        record = db.query(ApiKey).filter(
            ApiKey.provider == provider,
            ApiKey.is_active == True,
        ).first()
        if record:
            return record
    return None


def _configure_agent_env(db: Session) -> None:
    llm_key = _active_api_key(db, ["deepseek", "siliconflow"])
    if llm_key:
        os.environ["LLM_API_KEY"] = llm_key.api_key
        os.environ["LLM_BASE_URL"] = llm_key.base_url or "https://api.deepseek.com/v1"

    embedding_key = _active_api_key(
        db,
        ["dashscope", "aliyun_embedding", "qwen_embedding", "siliconflow"],
    )
    if embedding_key:
        os.environ["EMBEDDING_API_KEY"] = embedding_key.api_key
        os.environ["EMBEDDING_BASE_URL"] = (
            embedding_key.base_url
            or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )


def _json_sources(sources: Any) -> str:
    try:
        return json.dumps(sources or [], ensure_ascii=False)
    except TypeError:
        return json.dumps([str(item) for item in sources or []], ensure_ascii=False)


def answer_with_agent(question: str, db: Session, session_id: str = "") -> dict:
    from services.sensitive_filter import filter_text

    blocked, filtered_question = filter_text(question, db)
    if blocked:
        return {
            "answer": "抱歉，您的问题包含不适合处理的内容。",
            "sources": [],
            "retrieved_docs": "[]",
            "from_agent": True,
            "is_sensitive_blocked": True,
        }

    _configure_agent_env(db)

    from app.agents.agent import run as agent_run

    result = agent_run(filtered_question, session_id or "default")
    answer = result.get("answer", "")
    sources = result.get("sources", [])

    answer_blocked, filtered_answer = filter_text(answer, db)

    return {
        "answer": filtered_answer,
        "sources": sources,
        "retrieved_docs": _json_sources(sources),
        "from_agent": True,
        "is_sensitive_blocked": answer_blocked,
    }
