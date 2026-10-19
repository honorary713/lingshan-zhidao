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


def _try_faq_answer(question: str, db: Session) -> dict | None:
    """FAQ 快车道：仅对“知识库没有、由师生补充录入”的 FAQ 生效。

    匹配顺序：精确匹配 → 包含匹配 → 向量语义匹配（阈值见 search_faq_vector）。
    FAQ 库为空或未命中时返回 None，问题继续交给 RAG Agent 检索知识库作答。
    注意：FAQ 不应存放知识库已有内容，否则会与 RAG 重复并可能误拦截。
    """
    from models.faq import FAQ
    # 1) 精确匹配
    faq = db.query(FAQ).filter(FAQ.is_active == True, FAQ.question == question).first()
    # 2) 包含匹配：用户问题包含 / 被包含于某条 FAQ 问法
    if not faq:
        for f in db.query(FAQ).filter(FAQ.is_active == True).all():
            if f.question and (f.question in question or question in f.question):
                faq = f
                break
    # 3) 向量语义匹配：师生补充的问法多样，口语改写也要能命中
    if not faq:
        try:
            from services.knowledge_service import search_faq_vector
            faq = search_faq_vector(question, db)
        except Exception:
            faq = None
    if faq:
        return {
            "answer": faq.answer,
            "sources": [f"[FAQ] {faq.question}"],
            "retrieved_docs": _json_sources([{"source": f"FAQ-{faq.id}", "question": faq.question}]),
            "from_agent": False,
            "from_faq": True,
            "category": faq.category,
            "is_sensitive_blocked": False,
        }
    return None


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

    # FAQ 快车道：常见问题直接返回标准答案，降低大模型负担、保证口径一致
    faq_result = _try_faq_answer(filtered_question, db)
    if faq_result:
        # 回填“上一轮工具”，保证后续多轮“纯补充句”能沿用本轮话题
        try:
            from app.agents.agent import _session_last_tool, FAQ_CATEGORY_TO_TOOL
            from app.agents.memory import conversation_memory
            tool = FAQ_CATEGORY_TO_TOOL.get(faq_result.get("category") or "")
            if tool:
                _session_last_tool[session_id or "default"] = tool
            # 写入对话历史，保证后续多轮上下文（否则补充句检测会失效）
            conversation_memory.add(session_id or "default", "user", filtered_question)
            conversation_memory.add(session_id or "default", "assistant", faq_result["answer"])
        except Exception:
            pass
        return faq_result

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
        "from_faq": False,
        "is_sensitive_blocked": answer_blocked,
    }
