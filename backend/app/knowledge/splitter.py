from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.knowledge.loader import load_documents


def _strip_preamble(text: str) -> str:
    """去除知识库合并文档顶部的“说明”元信息段落。

    该段只出现在文档开头（形如“中国石油大学（华东）校园知识库（新生导览版）说明：
    …均以学校官方最新通知为准。”），其中包含“系统”“新生入学”等泛化词，会污染
    分类（把本属概况的块误判为 service/registration）。摘掉它对正文 chunk 无影响。
    """
    marker = "中国石油大学（华东）校园知识库"
    idx = text.find(marker)

    if idx != -1:
        end = text.find("为准。", idx)
        if end != -1:
            text = text[end + len("为准。"):].lstrip()

    return text


def classify_chunk(text: str) -> str:
    """按校园导览维度给 chunk 打标签。"""
    text = _strip_preamble(text)

    if any(keyword in text for keyword in [
        "诈骗", "安全", "消防", "防骗", "紧急", "报警", "推销", "传销",
        "电信诈骗", "校园贷", "防盗",
    ]):
        return "safety"

    if any(keyword in text for keyword in [
        "奖学金", "助学金", "助学贷款", "勤工", "绿色通道", "资助", "补助", "贷",
    ]):
        return "financial_aid"

    if any(keyword in text for keyword in [
        "宿舍", "公寓", "食堂", "餐厅", "餐饮", "水电", "空调", "洗衣", "洗浴",
        "快递", "驿站", "超市", "商超",
    ]):
        return "living"

    if any(keyword in text for keyword in [
        "报到", "录取", "军训", "体检", "缴费", "一卡通",
        "校园卡", "激活", "档案", "户口", "迎新",
    ]):
        return "registration"

    if any(keyword in text for keyword in [
        "课程", "选课", "学分", "教务", "图书馆", "教材", "考试", "培养方案",
        "学籍", "成绩", "转专业", "辅修",
    ]):
        return "academics"

    if any(keyword in text for keyword in [
        "社团", "活动", "体育", "讲座", "志愿", "心理", "校医院", "医疗",
        "医保", "就业", "招聘",
    ]):
        return "campus_life"

    if any(keyword in text for keyword in [
        "证明", "请假", "补办", "挂失", "报修", "校园网", "网络", "VPN",
        "邮箱", "系统", "认证", "统一身份",
    ]):
        return "service"

    # overview 放最后：学校/校区/中国石油大学 等词在手册中极常见，若提前会冲垮细分分类
    if any(keyword in text for keyword in [
        "学校", "校区", "校训", "历史", "石大", "概况", "简介", "地址",
        "中国石油大学", "双一流", "211",
    ]):
        return "overview"

    return "general"


def split_documents(
    documents: list[dict],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            "。",
            "！",
            "？",
            "；",
            "，",
            " ",
            "",
        ],
    )

    chunks = []

    for document in documents:
        parts = splitter.split_text(document["text"])

        is_landmark = document["source"].startswith("地标讲解")
        for index, part in enumerate(parts):
            category = classify_chunk(part)
            # 地标讲解词统一归入 overview（与 search_overview 工具“地标/主要建筑”语义对齐），
            # 否则会被打成 general，规划器按 overview 检索时被过滤，导致“南门在哪”类问题无结果。
            if is_landmark:
                category = "overview"
            chunks.append({
                "text": part,
                "source": document["source"],
                "chunk_index": index,
                "category": category,
            })

    return chunks


if __name__ == "__main__":
    docs_dir = Path(__file__).resolve().parent.parent.parent / "knowledge_docs"
    documents = load_documents(docs_dir)
    result = split_documents(documents)

    for chunk in result[:20]:
        print(chunk["category"], "|", chunk["text"][:50])