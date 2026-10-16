import logging
import time

logger = logging.getLogger("app.agents.agent")
from app.agents.memory import conversation_memory
from app.agents.planner import plan
from app.agents.tools import TOOL_MAP
from app.agents.replay_cache import is_offline, lookup, save_turn
from app.services.llm import llm_service

SYSTEM_PROMPT = (
    "你是中国石油大学（华东）面向新生的 AI 校园导览助手。"
    "请根据参考资料，用自然、简洁、口语化的中文回答新生问题。\n\n"
    "【输出格式要求】\n"
    "1. 当用户提出具体的信息咨询（如报到、住宿、学习、资助、校园生活、办事服务、"
    "安全、学校概况等），回答必须结构清晰、层次分明：\n"
    "   - 先用一句简短的话直接回应问题；\n"
    "   - 核心内容用【一级标题】+ 序号或项目符号分点列出，每条信息独立、不混在段落里；\n"
    "   - 时间、地点、流程、注意事项等关键信息单独成段或单独列点；\n"
    "   - 结尾用一句话简要总结或给出行动建议（去哪里、联系谁）。\n"
    "2. 当问题只是打招呼、寒暄、或无明确咨询意图时，用一两句自然友好的话回应即可，"
    "不要套用资料结构；可简短引导用户提出具体问题（例如列出几个可咨询的方向）。\n"
    "3. 如果参考资料与问题明显不相关，或资料里没有相关信息，如实说明查不到，"
    "并建议咨询辅导员或相关职能部门，不要编造，也不要把无关内容硬凑成答案。\n\n"
    "【格式示例】\n"
    "新生报到需要带齐这些材料：\n\n"
    "【必带材料】\n"
    "1. 录取通知书\n"
    "2. 身份证\n"
    "3. ...\n\n"
    "【建议额外准备】\n"
    "• 身份证复印件 X 份\n"
    "• 一寸/两寸免冠照片及电子版\n"
    "• ...\n\n"
    "【报到当天提醒】\n"
    "• ...\n\n"
    "如有疑问，可咨询辅导员或学校相关部门。"
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

    plan_result = plan(message)
    logger.info(
        "规划结果 session_id=%s intent=%s tasks=%s",
        session_id,
        plan_result.get("intent"),
        plan_result.get("tasks"),
    )
    tasks = plan_result["tasks"]

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

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {
                "role": "user",
                "content": (
                    f"参考资料：\n{context}\n\n"
                    f"游客问题：{message}\n\n"
                    f"请根据参考资料回答。"
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

    # 在线模式：记录问答到回放缓存，供离线/断网环境复现真实内容
    save_turn(message, answer, tool_sources)

    conversation_memory.add(session_id, "user", message)
    conversation_memory.add(session_id, "assistant", answer)
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