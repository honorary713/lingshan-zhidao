"""
汇总所有 API 路由
"""
from fastapi import APIRouter
from api.auth import router as auth_router
from api.admins import router as admins_router
from api.digital_human import router as digital_human_router
from api.scenic_areas import router as scenic_areas_router
from api.scenic_spots import router as scenic_spots_router
from api.faqs import router as faqs_router
from api.unresolved import router as unresolved_router
from api.knowledge_base import router as knowledge_base_router
from api.conversations import router as conversations_router
from api.blacklist import router as blacklist_router
from api.stats import router as stats_router
from api.system import router as system_router
from api.logs import router as logs_router
from api.qa import router as qa_router  # 游客问答API
from api.report import router as report_router

api_router = APIRouter(prefix="/api")

# 注册所有子路由
api_router.include_router(auth_router, tags=["认证"])
api_router.include_router(admins_router, tags=["管理员管理"])
api_router.include_router(digital_human_router, tags=["数字人配置"])
api_router.include_router(scenic_areas_router, tags=["景区管理"])
api_router.include_router(scenic_spots_router, tags=["景点管理"])
api_router.include_router(faqs_router, tags=["FAQ管理"])
api_router.include_router(unresolved_router, tags=["未解决问题"])
api_router.include_router(knowledge_base_router, tags=["知识库"])
api_router.include_router(conversations_router, tags=["对话记录"])
api_router.include_router(blacklist_router, tags=["黑名单"])
api_router.include_router(stats_router, tags=["数据统计"])
api_router.include_router(system_router, tags=["系统配置"])
api_router.include_router(logs_router, tags=["操作日志"])
api_router.include_router(qa_router, tags=["游客问答"])  # cbh添加: 无需认证的公开问答接口
api_router.include_router(report_router, tags=["感受度报告"])
