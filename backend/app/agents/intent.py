def detect_intent(message: str) -> str:
    if any(keyword in message for keyword in ["门票", "票价", "多少钱", "价格"]):
        return "ticket"

    if any(keyword in message for keyword in ["路线", "怎么玩", "推荐", "行程"]):
        return "route"

    if any(keyword in message for keyword in ["介绍", "景区", "景点", "历史", "文化"]):
        return "knowledge"

    return "unknown"