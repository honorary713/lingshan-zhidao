import json
import re

from app.agents.tool_schema import TOOLS
from app.agents.tools import TOOL_MAP
from app.services.llm import llm_service

# 纯身份/年级/校区补充词：当一句话只含这些词且无疑问词时，视为对上一轮的“延续补充”，
# 而非新问题。典型例：2024级本科 / 研究生唐岛湾 / 本科生 / 男生宿舍。
ENTITY_SUPPLEMENT_RE = re.compile(
    r"(本科|研究生|硕士|博士|大一|大二|大三|大四|新生|20\d\d级|"
    r"唐岛湾|古镇口|东营|校区|宿舍|寝室|男生|女生|本部|南门|北门)"
)
# 疑问/动作词：出现则不算“纯补充”
QUESTION_RE = re.compile(
    r"[?？]|什么|怎么|如何|哪[里个]?|多少|几|吗|呢|为什么|是否|可以|需要|能|是|申请|办理|查|找|报|交|退|换|改|补|预约|几点|在哪"
)


def _last_user_turn(history):
    if not history:
        return None
    for msg in reversed(history):
        if msg.get("role") == "user":
            return msg.get("content", "")
    return None


def _is_pure_supplement(text: str, last_user: str | None) -> bool:
    if not last_user:
        return False
    t = (text or "").strip()
    if not t or len(t) > 24:
        return False
    if QUESTION_RE.search(t):
        return False
    return bool(ENTITY_SUPPLEMENT_RE.search(t))

# 中文别名 -> 校园工具名
TOOL_ALIASES = {
    "search_registration": "search_registration",
    "报到查询": "search_registration",
    "入学查询": "search_registration",
    "材料查询": "search_registration",

    "search_living": "search_living",
    "住宿查询": "search_living",
    "餐饮查询": "search_living",
    "宿舍查询": "search_living",
    "生活查询": "search_living",

    "search_academics": "search_academics",
    "学习查询": "search_academics",
    "教务查询": "search_academics",
    "选课查询": "search_academics",
    "图书馆查询": "search_academics",

    "search_financial_aid": "search_financial_aid",
    "奖助查询": "search_financial_aid",
    "助学金查询": "search_financial_aid",
    "贷款查询": "search_financial_aid",

    "search_campus_life": "search_campus_life",
    "社团查询": "search_campus_life",
    "活动查询": "search_campus_life",
    "校园生活查询": "search_campus_life",

    "search_service": "search_service",
    "办事查询": "search_service",
    "证明查询": "search_service",
    "网络查询": "search_service",
    "一卡通查询": "search_service",

    "search_safety": "search_safety",
    "安全查询": "search_safety",
    "防骗查询": "search_safety",
    "紧急查询": "search_safety",

    "search_overview": "search_overview",
    "概况查询": "search_overview",
    "学校查询": "search_overview",
    "地标查询": "search_overview",

    "search_general": "search_general",
    "通用查询": "search_general",
}

# 校园地标（用于“提到已知地标则优先查概况/地图”的强制路由）
# 注意：只放真正有「地标讲解」文档的建筑，不要把餐厅（玉兰/学苑/唐岛湾）、
# 校医院、大学生活动中心等生活/服务设施混进来——它们没有概况文档，强制查 overview
# 只会捞回无关 chunk 污染上下文（如“校医院”被路由到荟萃广场）。
CAMPUS_LANDMARKS = [
    "南门", "图书馆", "荟萃广场", "行政楼", "体育馆", "就业中心",
    "报告厅", "南教楼", "校史馆",
]


INTENT_TO_TOOL = {
    "registration": "search_registration",
    "living": "search_living",
    "academics": "search_academics",
    "financial_aid": "search_financial_aid",
    "campus_life": "search_campus_life",
    "service": "search_service",
    "safety": "search_safety",
    "overview": "search_overview",
    "general": "search_general",
    "general_chat": "search_general",
}


def _find_known_landmark(text: str) -> str:
    for landmark in CAMPUS_LANDMARKS:
        if landmark in text:
            return landmark
    return ""


def _build_tool_list() -> str:
    lines = []

    for tool in TOOLS:
        function = tool["function"]
        lines.append(
            f"- {function['name']}: {function['description']}"
        )

    return "\n".join(lines)


PLANNER_PROMPT = f"""你是中国石油大学（华东）新生校园导览助手的“任务规划器”。

根据新生问题，输出一个 JSON 对象，不要输出任何解释。

## 可用工具
{{tools}}

## 输出格式
{{
  "intent": "registration/living/academics/financial_aid/campus_life/service/safety/overview/general",
  "tasks": [
    {{
      "tool": "工具名",
      "question": "传给工具的问题"
    }}
  ]
}}

## 规则
1. tasks 里的 tool 必须来自可用工具。
2. 简单问题只生成 1 个 task。
3. 复杂问题可以生成多个 task（例如既问住宿又问报到）。
4. 如果问题与校园导览、新生入学、在校生活完全无关（如闲聊、其他学校），intent 返回 general_chat，tasks 返回 []。
5. 只输出 JSON，不要输出 markdown 代码块。

## 多轮对话处理（非常重要）
- 下面会给出“上一轮对话上下文”。如果用户当前输入只是一句简短的身份/年级/校区补充（例如“2024级本科”“研究生唐岛湾”“本科生”“男生宿舍”），
  它**不是新问题**，而是对上一轮话题的延续补充。此时必须：沿用上一轮的话题领域与工具，把补充信息并入检索问题，
  例如上一轮问“第二课堂要修几分”、本轮补“2024级本科”，则应按“2024级本科 第二课堂要修几分”去检索，
  **绝不能**把它当成“报到引导/校区介绍”等新话题去路由。
- 只有当用户提出明确的新问题（含疑问词或新动作）时，才视为新话题、重新路由。
"""


def _extract_json(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        return None

    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def _parse_tasks(data: dict, user_input: str) -> list[dict]:
    intent = data.get("intent", "")
    tasks = []

    for item in data.get("tasks", []):
        tool_name = TOOL_ALIASES.get(
            item.get("tool", ""),
            item.get("tool", ""),
        )

        if tool_name not in TOOL_MAP:
            continue

        args = item.get("args") or {}
        question = (
            item.get("question")
            or args.get("question")
            or args.get("name")
            or args.get("keyword")
            or user_input
        )

        tasks.append({
            "tool": tool_name,
            "question": question,
        })

    # 只要用户问题里出现已知校园地标，强制先查学校概况/地图
    known_landmark = _find_known_landmark(user_input)

    if known_landmark:
        overview_task = {
            "tool": "search_overview",
            "question": known_landmark,
        }

        if not any(task["tool"] == "search_overview" for task in tasks):
            tasks.insert(0, overview_task)

    # 如果 LLM 没生成 tasks，按 intent 自动补
    if not tasks:
        tool_name = INTENT_TO_TOOL.get(intent)

        if tool_name and tool_name in TOOL_MAP:
            question = user_input

            if tool_name == "search_overview":
                known_landmark = _find_known_landmark(user_input)
                if known_landmark:
                    question = known_landmark

            tasks.append({
                "tool": tool_name,
                "question": question,
            })

    return tasks


def plan(user_input: str, history: list[dict] | None = None) -> dict:
    last_user = _last_user_turn(history)
    is_supplement = _is_pure_supplement(user_input, last_user)

    # 纯补充句：把上一轮问题作为检索主体，把补充信息并入，保持话题不漂移
    if is_supplement and last_user:
        effective_input = f"{last_user}（补充信息：{user_input.strip()}）"
        previous_question = last_user
    else:
        effective_input = user_input
        previous_question = user_input

    prompt = PLANNER_PROMPT.replace("{tools}", _build_tool_list())

    # 注入多轮上下文，帮助规划器判断是否为延续
    if last_user:
        ctx_lines = ["## 上一轮对话上下文"]
        for msg in history[-4:]:
            role = "新生" if msg.get("role") == "user" else "助手"
            ctx_lines.append(f"{role}：{(msg.get('content') or '')[:120]}")
        prompt += "\n\n" + "\n".join(ctx_lines)

    prompt += f"\n\n新生问题：{effective_input}"

    response = llm_service.chat([
        {"role": "user", "content": prompt},
    ])

    data = _extract_json(response)

    if not data:
        return {
            "intent": "general_chat",
            "confidence": "low",
            "tasks": [],
        }

    tasks = _parse_tasks(data, effective_input)

    return {
        "intent": data.get("intent", "general_chat"),
        "confidence": data.get("confidence", "medium"),
        "tasks": tasks,
        "is_supplement": is_supplement,
        "effective_input": effective_input,
        "previous_question": previous_question,
    }
