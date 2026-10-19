"""
知识库问答服务：FAISS 搜索 + LLM 生成 + 多轮对话记忆
"""
import time
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from config import FAISS_INDEX_PATH, DB_DIR
from logging_config import llm_logger, app_logger

# 嵌入模型实例（懒加载）
_embeddings = None

# FAQ独立向量库路径（根目录）
FAQ_INDEX_BIN = Path("./faq_index.bin")
FAQ_ID_MAP_NPY = Path("./faq_id_map.npy")
# L2距离相似度阈值（余弦），越大越严格。0.70 的经验依据：
# 同一 FAQ 的口语改写约 0.69~1.0，而纯知识库问题与此 FAQ 的余弦<=0.56，
# 留足余量避免“截胡”知识库问题。FAQ 仅承载非知识库内容，跨主题重合低。
FAQ_SIM_THRESHOLD = 0.70


# ========== 修复：门票固定回答文本（最高优先级）==========
FIXED_TICKET_ANSWER = """成人票：210元，适用18周岁及以上成年人
半价票：105元，适用6-18周岁未成年人、全日制本科及以下学生、60-69周岁老人
免票：0元，适用6周岁以下或1.4米以下儿童、70周岁及以上老人、现役军人、残疾人
网购联票：225元，含门票+观光车，观光车可无限次乘坐，性价比更高
观光车单独票：40元/人，景区内交通，适合体力不足的游客。"""


# ========== 系统提示词（口语化导游风格）==========
# 从 system_configs 表读取全局参数
def _get_system_config(db: Session, key: str, default: str = None) -> str | None:
    """读取系统配置项，不存在时返回默认值"""
    from models.system import SystemConfig
    cfg = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    return cfg.config_value if cfg else default


DEFAULT_SYSTEM_PROMPT = """你是中国石油大学（华东）面向新生的 AI 校园导览助手，负责回答新生关于校园生活、报到注册、学习教务、奖助学金等方面的问题。

你说话应该自然亲切，不用序号罗列，不用箭头符号，不用 markdown 格式。

回答时只依靠提供的校园资料，资料里没提到的东西不要自己编。如果确实不清楚，就诚实告诉新生"这个问题我需要再确认一下，您可以咨询辅导员或学校相关部门"。

回答要简洁直接，一般控制在两三句话以内，不要啰嗦。给新生推荐流程或路线的时候用"您可以先...然后..."这样的自然表达。

始终保持礼貌和热情，让新生感受到学校的温暖。"""


def _get_embeddings():
    """懒加载真实 embedding，维度与 faq_index.bin 生成代码统一"""
    global _embeddings
    if _embeddings is None:
        from services.embedding_service import get_embedding
        import numpy as np

        class RealEmbeddingWrapper:
            def embed_query(self, text):
                vec = get_embedding(text)
                if isinstance(vec, np.ndarray):
                    return vec.tolist()
                return vec

            def embed_documents(self, texts):
                results = []
                for t in texts:
                    vec = get_embedding(t)
                    results.append(vec.tolist() if isinstance(vec, np.ndarray) else vec)
                return results
        _embeddings = RealEmbeddingWrapper()
    return _embeddings


def _get_llm_client(db: Session):
    """从数据库读取 API 密钥，动态创建 OpenAI 客户端。
    优先使用 DeepSeek，fallback 到 SiliconFlow。"""
    from openai import OpenAI
    from models.system import ApiKey
    for provider in ["deepseek", "siliconflow"]:
        key_record = db.query(ApiKey).filter(
            ApiKey.provider == provider,
            ApiKey.is_active == True
        ).first()
        if key_record:
            return OpenAI(
                api_key=key_record.api_key,
                base_url=key_record.base_url or "https://api.deepseek.com/v1",
                timeout=30
            )
    raise ValueError("未配置有效的 LLM API 密钥（deepseek 或 siliconflow），请在系统配置中添加")


# ===== 多轮对话记忆管理 =====
# 会话历史：{ session_id: [ {"role": "user/assistant", "content": "..."}, ... ] }
_session_history: dict[str, list[dict]] = defaultdict(list)
_SESSION_MAX_TURNS = 10   # 每会话最多保留 10 轮（20 条消息）
_SESSION_TTL_SECONDS = 1800  # 30 分钟无活动自动清理

_last_activity: dict[str, float] = {}


def _get_or_create_session(session_id: str) -> list[dict]:
    """获取或创建会话历史"""
    now = time.time()
    _last_activity[session_id] = now
    return _session_history[session_id]


def _cleanup_stale_sessions():
    """清理过期会话"""
    now = time.time()
    stale = [sid for sid, t in _last_activity.items() if now - t > _SESSION_TTL_SECONDS]
    for sid in stale:
        _session_history.pop(sid, None)
        _last_activity.pop(sid, None)
    if stale:
        app_logger.debug(f"清理了 {len(stale)} 个过期会话")


def add_message_to_session(session_id: str, role: str, content: str):
    """向会话历史追加一条消息"""
    if not session_id or not content:
        return
    history = _get_or_create_session(session_id)
    # 截断过长内容
    content_trimmed = content[:500] if len(content) > 500 else content
    history.append({"role": role, "content": content_trimmed})
    # 保留最近 N 轮
    while len(history) > _SESSION_MAX_TURNS * 2:
        history.pop(0)
    _cleanup_stale_sessions()


def get_session_context(session_id: str, max_messages: int = 6) -> str:
    """将会话历史格式化为 Prompt 上下文"""
    if not session_id:
        return ""
    history = _get_or_create_session(session_id)
    if not history:
        return ""
    recent = history[-max_messages:]
    lines = []
    for msg in recent:
        prefix = "游客" if msg["role"] == "user" else "导游"
        content = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
        lines.append(f"{prefix}：{content}")
    return "\n".join(lines)


def _get_ai_config(db: Session) -> dict:
    """从数据库读取 AI 配置参数"""
    from models.digital_human import DigitalHumanConfig
    config = db.query(DigitalHumanConfig).first()
    if not config:
        return {}
    return {
        "ai_model": config.ai_model or "deepseek-chat",
        "ai_temperature": config.ai_temperature if config.ai_temperature is not None else 0.01,
        "ai_max_tokens": config.ai_max_tokens or 512,
        "ai_system_prompt": config.ai_system_prompt or "",
        "ai_response_style": config.ai_response_style or "",
    }


def check_faq_exact_match(question: str, db: Session):
    """检查数据库 FAQ 是否有精确匹配（完全匹配或包含匹配）"""
    from models.faq import FAQ
    # 精确匹配
    faq = db.query(FAQ).filter(
        FAQ.is_active == True,
        FAQ.question == question
    ).first()
    if faq:
        return faq
    # 包含匹配：问题包含FAQ中的问题文本
    faqs = db.query(FAQ).filter(FAQ.is_active == True).all()
    for f in faqs:
        if f.question in question or question in f.question:
            return f
    return None


def search_faq_vector(question: str, db: Session):
    """
    独立 FAQ 向量语义检索（使用与校园知识库同一套 API embedding）。
    匹配成功返回 FAQ 对象，无匹配/异常返回 None。
    """
    import faiss
    import numpy as np
    from models.faq import FAQ
    # 校验向量文件是否存在
    if not (FAQ_INDEX_BIN.exists() and FAQ_ID_MAP_NPY.exists()):
        return None
    try:
        # 加载向量库
        index = faiss.read_index(str(FAQ_INDEX_BIN))
        id_mapping = np.load(str(FAQ_ID_MAP_NPY))
        if index.ntotal == 0:
            return None
        # 使用与校园知识库一致的 embedding
        from app.knowledge.embedder import embed_query
        query_vec = np.array([embed_query(question)], dtype=np.float32)
        # 归一化后做余弦相似度检索（与 retriever.py 一致）
        faiss.normalize_L2(query_vec)
        dist_arr, idx_arr = index.search(query_vec, k=1)
        min_dist = float(dist_arr[0][0])
        match_faq_id = int(id_mapping[idx_arr[0][0]])
        # 归一化向量下 L2 距离 d，余弦相似度 = 1 - d^2/2
        # 取 cos>=FAQ_SIM_THRESHOLD(0.70) 才算命中：既能召回口语改写，又对纯知识库
        # 问题留足余量，避免把知识库问题“截胡”到一条只沾边的 FAQ。
        cosine_sim = 1 - (min_dist ** 2) / 2
        if cosine_sim >= FAQ_SIM_THRESHOLD:
            target_faq = db.query(FAQ).filter(
                FAQ.id == match_faq_id,
                FAQ.is_active == True
            ).first()
            return target_faq
        return None
    except Exception as e:
        print(f"[FAQ向量检索失败] {str(e)}")
        return None


def search_knowledge(question: str, k: int = 10) -> tuple[str, list[str]]:
    """
    从 FAISS 索引检索景区文档资料。
    返回 (context_text, list_of_source_snippets)
    """
    from langchain_community.vectorstores import FAISS
    import retry as _retry_inner
    # 内联重试，避免外部依赖

    if not FAISS_INDEX_PATH.exists():
        return "", []

    last_err = None
    for attempt in range(3):
        try:
            db = FAISS.load_local(
                str(FAISS_INDEX_PATH),
                _get_embeddings(),
                allow_dangerous_deserialization=True
            )
            docs = db.similarity_search(question, k=k)
            if not docs:
                return "", []
            context = "\n".join([d.page_content for d in docs])
            sources = [d.page_content[:200] for d in docs]
            return context, sources
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(0.5)
    app_logger.warning(f"FAISS 加载失败(重试3次): {last_err}")
    return "", []


_embedding_available = None  # None=未检查, True=可用, False=不可用


def has_embedding() -> bool:
    """检查 Embedding 服务是否可用（带缓存，不重复检测）"""
    global _embedding_available
    if _embedding_available is not None:
        return _embedding_available
    try:
        import numpy as np
        from services.embedding_service import get_embedding
        vec = get_embedding("test")
        _embedding_available = np.sum(np.abs(vec)) > 0
        return _embedding_available
    except Exception:
        _embedding_available = False
        return False


def ask_ai_without_context(question: str, db: Session, session_id: str = "") -> str:
    """无本地知识库时，直接用 LLM 自身知识回答（景区场景）"""
    ai_config = _get_ai_config(db)
    client = _get_llm_client(db)

    system_prompt = ai_config.get("ai_system_prompt", "").strip()
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    response_style = ai_config.get("ai_response_style", "").strip()
    if response_style:
        system_prompt += f"\n\n回答风格：{response_style}"

    messages = [{"role": "system", "content": system_prompt}]

    session_ctx = get_session_context(session_id, max_messages=6)
    if session_ctx:
        messages.append({
            "role": "system",
            "content": f"之前和游客的对话：\n{session_ctx}\n\n请在此基础上继续自然对话。"
        })

    messages.append({"role": "user", "content": question})

    try:
        response = client.chat.completions.create(
            model=ai_config.get("ai_model", "deepseek-chat"),
            messages=messages,
            temperature=ai_config.get("ai_temperature", 0.01),
            max_tokens=ai_config.get("ai_max_tokens", 512)
        )
        raw = response.choices[0].message.content.strip()
        return clean_answer(raw)
    except Exception as e:
        llm_logger.error(f"LLM 调用失败: {e}")
        return f"AI 服务调用失败：{str(e)}"


def clean_answer(text: str) -> str:
    """清洗AI回答，去除多余格式和符号"""
    # 去除 markdown 标题
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # 去除列表符号
    text = re.sub(r'^[\-\*•]\s*', '', text, flags=re.MULTILINE)
    # 去除箭头符号
    text = re.sub(r'[→←↑↓⇒⇐⇑⇓]', '', text)
    # 去除多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 去除首尾引号
    text = text.strip('"\'')
    # 去除首尾空白
    return text.strip()


def ask_ai_with_config(question: str, context: str, db: Session, session_id: str = "") -> str:
    """
    调用 LLM 生成回答（参数从数据库读取，支持多轮上下文）。
    """
    ai_config = _get_ai_config(db)
    client = _get_llm_client(db)

    system_prompt = ai_config.get("ai_system_prompt", "").strip()
    if not system_prompt:
        system_prompt = DEFAULT_SYSTEM_PROMPT

    response_style = ai_config.get("ai_response_style", "").strip()
    if response_style:
        system_prompt += f"\n\n回答风格：{response_style}"

    # 构建消息列表
    messages = [{"role": "system", "content": system_prompt}]

    # 如果有会话历史，注入上下文
    session_ctx = get_session_context(session_id, max_messages=6)
    if session_ctx:
        messages.append({
            "role": "system",
            "content": f"之前和游客的对话：\n{session_ctx}\n\n请在此基础上继续自然对话，不要重复之前已经说过的内容。"
        })

    user_content = f"参考资料：\n{context}\n\n游客问：{question}"
    messages.append({"role": "user", "content": user_content})

    try:
        response = client.chat.completions.create(
            model=ai_config.get("ai_model", "Qwen/Qwen2.5-7B-Instruct"),
            messages=messages,
            temperature=ai_config.get("ai_temperature", 0.01),
            max_tokens=ai_config.get("ai_max_tokens", 512)
        )
        raw_answer = response.choices[0].message.content.strip()
        llm_logger.info(f"问答完成 session={session_id[:8]}: {question[:30]}... -> {raw_answer[:50]}...")
        return clean_answer(raw_answer)
    except Exception as e:
        llm_logger.error(f"LLM 调用失败: {e}")
        return f"AI 服务调用失败：{str(e)}"


# ========== 修复核心：判断是否为门票/价格类问题 ==========
def is_ticket_question(question: str) -> bool:
    """
    判断用户问题是否与门票价格相关。
    覆盖尽可能多的问法，确保价格问题100%被拦截。
    """
    # 直接门票相关词
    direct_ticket = {"门票", "票价", "成人票", "半价票", "联票", "观光车", "免票"}
    # 价格相关词
    price_keywords = {"钱", "价格", "收费", "多少钱", "多少", "怎么收费", "费用"}
    # 购票相关词
    buy_keywords = {"怎么买", "购票", "买票", "订票", "预约", "购买"}

    q = question.lower()
    if any(k in q for k in direct_ticket):
        return True
    if any(k in q for k in price_keywords):
        return True
    if any(k in q for k in buy_keywords):
        return True
    return False


def answer_question(question: str, db: Session, session_id: str = "") -> dict:
    """
    完整问答流程（游客端 API 调用）。
    执行顺序：敏感过滤 → 门票拦截 → FAQ 精确匹配 → FAQ 向量检索 → 文档 FAISS → LLM 生成
    支持 session_id 多轮对话记忆。
    """
    from services.sensitive_filter import filter_text
    from models.faq import FAQ

    # Step 0：敏感词过滤
    question_blocked, filtered_question = filter_text(question, db)
    if question_blocked:
        return {
            "answer": "抱歉，您的问题包含不当内容，无法处理。",
            "sources": [],
            "from_faq": False,
            "is_sensitive_blocked": True
        }

    # Step 0.5：门票价格强制拦截
    if is_ticket_question(filtered_question):
        return {
            "answer": FIXED_TICKET_ANSWER,
            "sources": ["[固定门票信息]"],
            "from_faq": True,
            "is_sensitive_blocked": False
        }

    # Step 1：FAQ 精确匹配
    faq_exact = check_faq_exact_match(filtered_question, db)
    if faq_exact:
        add_message_to_session(session_id, "user", question)
        add_message_to_session(session_id, "assistant", faq_exact.answer)
        return {
            "answer": faq_exact.answer,
            "sources": [f"[FAQ] {faq_exact.question}"],
            "from_faq": True,
            "is_sensitive_blocked": False
        }

    # Step 2：FAQ 向量语义检索
    faq_vector = search_faq_vector(filtered_question, db)
    if faq_vector:
        add_message_to_session(session_id, "user", question)
        add_message_to_session(session_id, "assistant", faq_vector.answer)
        return {
            "answer": faq_vector.answer,
            "sources": [f"[FAQ语义] {faq_vector.question}"],
            "from_faq": True,
            "is_sensitive_blocked": False
        }

    # Step 3：FAISS 文档检索（如果 Embedding 可用）
    k_str = _get_system_config(db, "faiss_search_k", "10")
    try:
        k = int(k_str)
    except (ValueError, TypeError):
        k = 10
    context, sources = search_knowledge(filtered_question, k=k) if has_embedding() else ("", [])

    # Step 4：LLM 生成（带会话上下文）。即使知识库没有结果，也让 DeepSeek 用自有知识回答
    if context:
        answer = ask_ai_with_config(filtered_question, context, db, session_id)
    else:
        # 知识库无结果，让 LLM 用自有知识 + 景区背景回答
        answer = ask_ai_without_context(filtered_question, db, session_id)
        # 只有完全无法回答时才记录未解决
        if "不确定" in answer or "暂时" in answer:
            _record_unresolved(question, db)

    # 记录到会话历史
    add_message_to_session(session_id, "user", question)
    add_message_to_session(session_id, "assistant", answer)

    # Step 5：回答敏感词二次过滤
    is_blocked, filtered_answer = filter_text(answer, db)

    return {
        "answer": filtered_answer,
        "sources": sources,
        "from_faq": False,
        "is_sensitive_blocked": is_blocked
    }


# 记录未解决问题
def _record_unresolved(question: str, db: Session):
    """当知识库无法回答时，自动记录未解决问题供管理员处理"""
    from models.faq import UnresolvedQuestion
    existing = db.query(UnresolvedQuestion).filter(
        UnresolvedQuestion.question == question,
        UnresolvedQuestion.status == "pending"
    ).first()
    if existing:
        existing.ask_count = (existing.ask_count or 0) + 1
    else:
        db.add(UnresolvedQuestion(question=question, ask_count=1, status="pending"))
    db.commit()


def rebuild_faiss_index(db: Session) -> dict:
    """
    从数据库重建景区混合FAISS索引（faiss_scenic_index，景区/景点/FAQ合并文档向量）
    注意：此函数仅用于后台知识库全景重建，不影响前端独立FAQ向量库faq_index.bin
    """
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from models.scenic import ScenicArea, ScenicSpot
    from models.faq import FAQ

    texts = []
    metadatas = []

    # 收集景区数据
    areas = db.query(ScenicArea).filter(ScenicArea.is_active == True).all()
    for area in areas:
        parts = [f"【景区】{area.name}"]
        if area.description:
            parts.append(f"简介：{area.description}")
        if area.hours:
            parts.append(f"开放时间：{area.hours}")
        if area.ticket_info:
            parts.append(f"门票信息：{area.ticket_info}")
        if area.transport_info:
            parts.append(f"交通信息：{area.transport_info}")
        texts.append("\n".join(parts))
        metadatas.append({"source": f"景区-{area.name}", "type": "scenic_area"})

    # 收集景点数据
    spots = db.query(ScenicSpot).filter(ScenicSpot.is_active == True).all()
    for spot in spots:
        area_name = spot.area.name if spot.area else "未知景区"
        parts = [f"【景点】{spot.name}（属于{area_name}）"]
        if spot.description:
            parts.append(spot.description)
        texts.append("\n".join(parts))
        metadatas.append({"source": f"景点-{spot.name}", "type": "scenic_point"})

    # 收集 FAQ 数据（合并进全景文档库）
    faqs = db.query(FAQ).filter(FAQ.is_active == True).all()
    for faq in faqs:
        texts.append(f"【常见问题】\n问：{faq.question}\n答：{faq.answer}")
        metadatas.append({"source": f"FAQ-{faq.question[:30]}", "type": "faq"})

    if not texts:
        return {"success": False, "message": "知识库中没有可用数据，请先添加景区、景点或FAQ", "chunk_count": 0}

    # 文本分割
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_texts = []
    split_metadatas = []
    for text, meta in zip(texts, metadatas):
        chunks = text_splitter.split_text(text)
        split_texts.extend(chunks)
        split_metadatas.extend([meta] * len(chunks))

    # 构建全景混合索引
    faiss_db = FAISS.from_texts(split_texts, _get_embeddings(), metadatas=split_metadatas)
    faiss_db.save_local(str(FAISS_INDEX_PATH))

    return {
        "success": True,
        "message": f"全景知识库重建成功",
        "chunk_count": len(split_texts),
        "source_count": len(texts),
        "index_path": str(FAISS_INDEX_PATH)
    }
