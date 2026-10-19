import logging
import time

logger = logging.getLogger("app.agents.agent")
from app.agents.memory import conversation_memory
from app.agents.planner import plan
from app.agents.tools import TOOL_MAP
from app.agents.replay_cache import is_offline, lookup, save_turn
from app.services.llm import llm_service

# 记录每个会话上一轮实际使用的工具，用于多轮“纯补充句”时强制沿用上一轮话题，
# 避免规划器被孤立的“身份/校区名词”带偏到新话题（如 T023「研究生唐岛湾」被误路由到图书馆）。
_session_last_tool: dict[str, str] = {}

# FAQ 分类 -> 检索工具 的映射，用于在 FAQ 快车道命中时也回填“上一轮工具”，
# 否则下一轮补充句无法触发沿用逻辑（会使多轮话题漂移）。
FAQ_CATEGORY_TO_TOOL = {
    "overview": "search_overview",
    "registration": "search_registration",
    "living": "search_living",
    "academics": "search_academics",
    "financial_aid": "search_financial_aid",
    "service": "search_service",
    "safety": "search_safety",
}

SYSTEM_PROMPT = (
    "你是中国石油大学（华东）面向新生的 AI 校园导览助手。"
    "请根据参考资料，用自然、简洁、口语化的中文回答新生问题。\n\n"
    "【校名规范（必须严格遵守）】\n"
    "1. 本校完整名称是「中国石油大学（华东）」，回答中凡提及本校，必须完整写全这九个字，"
    "不得省略「（华东）」三个字，也不得将校名拆开或漏字。\n"
    "2. 可以简称「中石大」「石大」，但首次出现或作为正式名称时一律用全称"
    "「中国石油大学（华东）」；绝不允许出现「中国石油大学（」这种残缺写法。\n\n"
    "【输出格式要求】\n"
    "1. 当用户提出具体的信息咨询（如报到、住宿、学习、资助、校园生活、办事服务、"
    "安全、学校概况等），回答必须结构清晰、层次分明：\n"
    "   - 先用一句简短的话直接回应问题；\n"
    "   - 核心内容用【一级标题】+ 序号或项目符号分点列出，每条信息独立、不混在段落里；\n"
    "   - 时间、地点、流程、注意事项等关键信息单独成段或单独列点；\n"
    "   - 结尾用一句话简要总结或给出行动建议（去哪里、联系谁）。\n"
    "2. 全文严禁使用任何 Markdown 语法，特别是 \'*\' 和 \'**\' 星号；"
    "回答中不得出现 \'*\' 或 \'**\' 这两个字符；"
    "强调文字时只能用中文书名号「」包裹，或直接用文字描述，不要输出 \'**内容**\' 或 \'*内容*\'；"
    "列表仅用 \'1.\'、\'•\' 或 \'- \' 等纯文本符号。\n"
    "3. 当问题只是打招呼、寒暄、或无明确咨询意图时，用一两句自然友好的话回应即可，"
    "不要套用资料结构；可简短引导用户提出具体问题（例如列出几个可咨询的方向）。\n"
    "4. 如果参考资料与问题明显不相关，或资料里没有相关信息，如实说明查不到，"
    "并建议咨询辅导员或相关职能部门，不要编造，也不要把无关内容硬凑成答案。\n\n"
    "【格式示例】\n"
    "中国石油大学（华东）是教育部直属的全国重点高校，也是国家 211 工程、双一流建设高校。\n\n"
    "【基本信息】\n"
    "• 英文名称：China University of Petroleum (East China)，简称 UPC\n"
    "• 校训：惟真惟实\n"
    "• 别称：中石大、石大\n\n"
    "【主要校区】\n"
    "1. 唐岛湾校区（主校区）：青岛市黄岛区长江西路 66 号，本科生主要就读校区\n"
    "2. 古镇口校区：青岛市黄岛区海军路 6 号\n"
    "3. 东营科教园区：山东省东营市东营区北一路 739 号\n\n"
    "如需了解具体专业的就读校区，建议查看录取通知书或咨询辅导员。"
)


def run(message: str, session_id: str = "default") -> dict:
    tool_sources = []
    start = time.perf_counter()

    logger.info(
        "Agent 开始 session_id=%s message=%s",
        session_id,
        message[:120],
    )

    # 离线回放模式：无密钥环境下返回预存真实内容，避免露出 Mock 假文本
    if is_offline():
        hit = lookup(message)
        if hit:
            conversation_memory.add(session_id, "user", message)
            conversation_memory.add(session_id, "assistant", hit["answer"])
            return {
                "answer": hit["answer"],
                "sources": hit.get("sources", []),
            }
        return {
            "answer": (
                "（离线演示模式）当前环境未配置大模型密钥，无法实时生成回答。"
                "本系统已内置常见问题回放库，可尝试询问“新生报到要带什么”“宿舍怎么充电”"
                "“怎么申请助学金”“学校有几个校区”等常见问题；完整实时功能需在配置密钥的环境"
                "或答辩现场演示中体验。"
            ),
            "sources": [],
        }

    history = conversation_memory.get(session_id)

    plan_result = plan(message, history)
    logger.info(
        "规划结果 session_id=%s intent=%s tasks=%s",
        session_id,
        plan_result.get("intent"),
        plan_result.get("tasks"),
    )
    tasks = plan_result["tasks"]

    # 多轮“纯补充句”修复：若本轮只是对上一轮的身份/年级/校区补充（如“研究生唐岛湾”），
    # 强制沿用上一轮使用的工具与话题，防止被孤立名词误路由到新主题（如图书馆借阅）。
    if plan_result.get("is_supplement") and session_id in _session_last_tool:
        prev_tool = _session_last_tool[session_id]
        if prev_tool in TOOL_MAP:
            # 检索用上一轮“本主题问题”（干净、不被补充实体污染），
            # 补充实体仅作为上下文留在对话历史中供生成 LLM 参考。
            retrieval_q = plan_result.get("previous_question") or message
            tasks = [{"tool": prev_tool, "question": retrieval_q}]
            logger.info("多轮补充句：沿用上一轮工具=%s 检索问题=%s", prev_tool, retrieval_q)

    results = []

    for task in tasks:
        logger.info(
            "调用工具 session_id=%s tool=%s question=%s",
            session_id,
            task["tool"],
            task["question"][:120],
        )
        tool = TOOL_MAP.get(task["tool"])

        if tool is None:
            continue

        result = tool(task["question"])

        content = result.get("content", "")
        sources = result.get("sources", [])

        logger.info(
            "工具结果 session_id=%s tool=%s content_len=%d source_count=%d",
            session_id,
            task["tool"],
            len(content),
            len(sources),
        )

        # 仅当工具返回了有效内容才计入；空结果（分类过滤未命中）交给下方全量兜底
        if content:
            results.append(content)
            tool_sources.extend(sources)

    # 兜底：若所有工具均无返回（如规划器判为闲聊），做一次全量检索，确保回答有依据
    if not results:
        fallback = TOOL_MAP.get("search_general")
        if fallback:
            fb = fallback(message)
            if fb.get("content"):
                results.append(fb["content"])
                tool_sources.extend(fb.get("sources", []))

    if results:
        context = "\n\n".join(results)

        # 多轮“纯补充句”处理：把“游客问题”锚定为上一轮的“本主题问题”，
        # 补充的身份/校区名词仅作为背景修饰，且不在 prompt 中原样回显为待答项，
        # 避免 LLM 被孤立名词（如“唐岛湾”）联想跳转到其他主题（如图书馆/借阅）。
        supplement_guard = ""
        if plan_result.get("is_supplement"):
            prev_q = plan_result.get("previous_question") or message
            supplement_guard = (
                f"\n\n【多轮对话提示】本轮仍是在回答上一轮话题「{prev_q}」，"
                f"用户补充的只是其身份或所在校区等背景信息，并非新问题，"
                f"请严格围绕「{prev_q}」作答，不得跳转到图书馆、借阅、导师、地标等其他主题。"
                f"若资料中相关内容未区分校区或学历，直接给出通用答案即可。"
            )
            user_question = prev_q
        else:
            user_question = message

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {
                "role": "user",
                "content": (
                    f"参考资料：\n{context}\n\n"
                    f"游客问题：{user_question}\n\n"
                    f"请根据参考资料回答。{supplement_guard}"
                ),
            },
        ]
    else:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": message},
        ]

    answer = llm_service.chat(messages)

    # 强制后处理：无论 LLM 是否遵守 prompt，都移除 Markdown 星号，确保前端不显示 **
    answer = answer.replace("**", "").replace("*", "").strip()

    # 在线模式：记录问答到回放缓存，供离线/断网环境复现真实内容
    save_turn(message, answer, tool_sources)

    conversation_memory.add(session_id, "user", message)
    conversation_memory.add(session_id, "assistant", answer)

    # 记录本轮实际使用的工具，供下一轮“纯补充句”强制沿用话题
    if tasks:
        _session_last_tool[session_id] = tasks[0].get("tool")

    elapsed = time.perf_counter() - start
    logger.info(
        "Agent 完成 session_id=%s elapsed=%.3fs",
        session_id,
        elapsed,
    )
    return {
        "answer": answer,
        "sources": tool_sources,
    }