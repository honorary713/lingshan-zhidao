import logging

logger = logging.getLogger("app.agents.tools")
from app.knowledge.retriever import search as search_index


def _search_with_category(question: str, category: str, top_k: int = 3) -> dict:
    """按校园分类检索知识库并返回统一结构的工具结果。"""
    results = search_index(question, top_k=top_k, category=category)
    context = "\n\n".join(item["text"] for item in results)

    return {
        "tool": category,
        "content": context,
        "sources": results,
    }


def search_registration(question: str) -> dict:
    """新生报到入学：报到流程、必带材料、缴费、一卡通、军训、体检等。"""
    return _search_with_category(question, "registration")


def search_living(question: str) -> dict:
    """住宿与餐饮：宿舍、食堂、水电空调、快递、商超、洗浴等生活服务。"""
    return _search_with_category(question, "living")


def search_academics(question: str) -> dict:
    """学习与教务：课程、选课、学分、图书馆、教材、考试、学籍、培养方案。"""
    return _search_with_category(question, "academics")


def search_financial_aid(question: str) -> dict:
    """奖助贷：奖学金、助学金、助学贷款、勤工助学、绿色通道、资助政策。"""
    return _search_with_category(question, "financial_aid")


def search_campus_life(question: str) -> dict:
    """校园生活：社团、活动、体育、讲座、志愿、心理、校医院、就业等。"""
    return _search_with_category(question, "campus_life")


def search_service(question: str) -> dict:
    """办事服务与数字校园：证明开具、请假、补办、校园网、VPN、邮箱、统一认证。"""
    return _search_with_category(question, "service")


def search_safety(question: str) -> dict:
    """安全与防骗：电信诈骗、消防、紧急电话、防盗、防推销、校园贷风险。"""
    return _search_with_category(question, "safety")


def search_overview(question: str) -> dict:
    """学校概况与地标：校史、校区、校训、地址、双一流/211 属性、主要建筑。"""
    return _search_with_category(question, "overview")


def search_general(question: str) -> dict:
    """通用检索：不限定分类，在全量知识库中检索（兜底用）。"""
    results = search_index(question, top_k=3)
    context = "\n\n".join(item["text"] for item in results)

    return {
        "tool": "general",
        "content": context,
        "sources": results,
    }


TOOL_MAP = {
    "search_registration": search_registration,
    "search_living": search_living,
    "search_academics": search_academics,
    "search_financial_aid": search_financial_aid,
    "search_campus_life": search_campus_life,
    "search_service": search_service,
    "search_safety": search_safety,
    "search_overview": search_overview,
    "search_general": search_general,
}
