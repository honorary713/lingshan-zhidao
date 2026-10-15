"""
Admin Portal Configuration
所有配置项集中管理
"""
import os
import sys
from pathlib import Path

# ============ 路径配置 ============
# admin_portal/backend/ 目录
BACKEND_ROOT = Path(__file__).resolve().parent
# admin_portal/ 目录
ADMIN_PORTAL_ROOT = BACKEND_ROOT.parent
# 现有项目根目录 (admin_portal 的父目录)
EXISTING_PROJECT_ROOT = BACKEND_ROOT.parent.parent

# 将现有项目路径加入 sys.path，用于未来扩展
if str(EXISTING_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXISTING_PROJECT_ROOT))

# FAISS 索引路径（现有项目中的 faiss_scenic_index 目录）
FAISS_INDEX_PATH = BACKEND_ROOT / "faiss_scenic_index"

# 数据库文件路径
DB_DIR = BACKEND_ROOT / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_DIR / 'admin_portal.db'}"

# ============ JWT 认证配置 ============
# 生产环境请更换为复杂随机字符串
SECRET_KEY = "admin-portal-scenic-ai-2024-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8小时过期

# ============ 默认超管账号 ============
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_NICKNAME = "超级管理员"

# ============ CORS 配置 ============
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ============ 分页配置 ============
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ============ 上传文件配置 ============
UPLOAD_DIR = BACKEND_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
