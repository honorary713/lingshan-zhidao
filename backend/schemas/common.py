"""
通用 Pydantic 模型：分页、响应
"""
from typing import Optional
from pydantic import BaseModel


class PaginationParams(BaseModel):
    """分页请求参数"""
    page: int = 1
    page_size: int = 20


class BaseFilter(PaginationParams):
    """带搜索的基础筛选"""
    keyword: Optional[str] = None
