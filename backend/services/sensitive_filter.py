"""
敏感词过滤服务
"""
from sqlalchemy.orm import Session
from models.digital_human import SensitiveWord


def get_active_sensitive_words(db: Session) -> list[str]:
    """获取所有启用的敏感词列表"""
    words = db.query(SensitiveWord.word).filter(
        SensitiveWord.is_active == True
    ).all()
    return [w[0] for w in words]


def check_sensitive(text: str, sensitive_words: list[str]) -> tuple[bool, str]:
    """
    检查文本是否包含敏感词。
    Returns:
        (is_blocked: bool, filtered_text: str)
        如果包含敏感词，filtered_text 会将敏感词替换为 ***
    """
    filtered = text
    has_sensitive = False
    for word in sensitive_words:
        if word and word in filtered:
            has_sensitive = True
            filtered = filtered.replace(word, "***")
    return has_sensitive, filtered


def filter_text(text: str, db: Session) -> tuple[bool, str]:
    """
    对文本进行敏感词过滤（从数据库加载敏感词）。
    Returns (is_blocked, filtered_text)
    """
    words = get_active_sensitive_words(db)
    return check_sensitive(text, words)
