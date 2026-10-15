"""
统一 API 响应格式
所有接口返回的 JSON 都遵循此格式:
  { "code": 200, "message": "success", "data": {...} }
"""
from typing import Any, Optional


def success_response(data: Any = None, message: str = "success") -> dict:
    """成功响应"""
    return {
        "code": 200,
        "message": message,
        "data": data
    }


def error_response(code: int, message: str, data: Any = None) -> dict:
    """错误响应"""
    return {
        "code": code,
        "message": message,
        "data": data
    }


def paginated_response(
    items: list,
    total: int,
    page: int,
    page_size: int
) -> dict:
    """分页响应"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    }
