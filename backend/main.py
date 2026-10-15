"""
AI 数字人景区导览系统 - FastAPI 主入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import CORS_ORIGINS
from database import init_db, SessionLocal
from models import admin, conversation, faq, scenic
from services.auth_service import hash_password
from logging_config import app_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的生命周期管理"""
    init_db()
    app_logger.info("数据库表已初始化")

    from app.config import missing_keys
    missing = missing_keys()
    if missing:
        app_logger.warning(
            "以下 API 配置尚未填写，相关功能将降级：%s", "、".join(missing)
        )
    else:
        app_logger.info("API 配置检查通过")

    db = SessionLocal()
    try:
        existing = db.query(admin.AdminUser).filter(admin.AdminUser.username == "admin").first()
        if not existing:
            default_admin = admin.AdminUser(
                username="admin",
                password_hash=hash_password("admin123"),
                nickname="超级管理员",
                role="super_admin",
                is_active=True
            )
            db.add(default_admin)
            db.commit()
            app_logger.info("默认超管账号已创建: admin / admin123")
        else:
            app_logger.info("超管账号已存在，跳过创建")
    finally:
        db.close()

    yield

    app_logger.info("服务已关闭")


app = FastAPI(
    title="校园智导 · AI 数字人新生校园导览",
    description="管理校园知识库、数字人配置、对话记录、数据统计等",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api import api_router
from api.health import router as health_router
app.include_router(api_router)
app.include_router(health_router)


@app.get("/")
def root():
    return {
        "name": "校园智导 · AI 数字人新生校园导览",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
