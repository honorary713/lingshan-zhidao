import json
import re

from app.agents.tool_schema import TOOLS
from app.agents.tools import TOOL_MAP
from app.services.llm import llm_service

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


def plan(user_input: str) -> dict:
    prompt = PLANNER_PROMPT.replace("{tools}", _build_tool_list())
    prompt += f"\n\n新生问题：{user_input}"

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

    tasks = _parse_tasks(data, user_input)

    return {
        "intent": data.get("intent", "general_chat"),
        "confidence": data.get("confidence", "medium"),
        "tasks": tasks,
    }
