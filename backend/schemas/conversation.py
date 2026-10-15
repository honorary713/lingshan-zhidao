"""
对话记录 Pydantic 模型
"""
from typing import Optional
from pydantic import BaseModel


class ConversationFilter(BaseModel):
    """对话筛选参数"""
    page: int = 1
    page_size: int = 20
    date_from: Optional[str] = None    # YYYY-MM-DD
    date_to: Optional[str] = None      # YYYY-MM-DD
    keyword: Optional[str] = None      # 搜索问题文本
    rating_min: Optional[int] = None   # 最低评分
    rating_max: Optional[int] = None   # 最高评分
