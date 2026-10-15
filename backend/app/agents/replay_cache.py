import json
import logging
import re
from pathlib import Path

logger = logging.getLogger("app.agents.replay_cache")

from app.config import LLM_API_KEY

CACHE_FILE = Path(__file__).resolve().parent.parent.parent / "replay_cache.json"

_PUNCT = re.compile(
    r"[\s。，、！？；：“”‘’（）()【】\[\]《》—\-…·.,!?;:\"'/\\]+"
)


def _normalize(text: str) -> str:
    """归一化问题：去空白与标点，便于离线精确匹配。"""
    if not text:
        return ""
    return _PUNCT.sub("", text).strip()


def is_offline() -> bool:
    """无 LLM 密钥时进入离线回放模式（裁判机 / 断网场景）。"""
    return not bool(LLM_API_KEY)


def _load() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.warning("回放缓存写入失败: %s", exc)


def save_turn(query: str, answer: str, sources: list[dict]) -> None:
    """在线模式下记录一轮问答（按归一化问题去重更新）。"""
    key = _normalize(query)
    if not key:
        return
    data = _load()
    data[key] = {
        "query": query,
        "answer": answer,
        "sources": [
            {
                "source": s.get("source", ""),
                "category": s.get("category", ""),
                "text": s.get("text", "")[:400],
            }
            for s in (sources or [])
        ],
    }
    _save(data)
    logger.info("回放缓存已记录 query=%s", query[:60])


def lookup(query: str) -> dict | None:
    """离线模式下按归一化问题查找缓存命中。"""
    key = _normalize(query)
    if not key:
        return None
    data = _load()
    hit = data.get(key)
    if hit:
        logger.info("回放缓存命中 query=%s", query[:60])
    return hit


def count() -> int:
    return len(_load())
