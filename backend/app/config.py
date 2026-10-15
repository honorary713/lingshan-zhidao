import os


from pathlib import Path

from dotenv import load_dotenv

# 依次加载：项目根 .env → backend/.env（后加载的优先级更高，可覆盖前者）
_BACKEND_DIR = Path(__file__).resolve().parent.parent      # backend/
_PROJECT_ROOT = _BACKEND_DIR.parent                        # 项目根目录

for _env_path in (_PROJECT_ROOT / ".env", _BACKEND_DIR / ".env"):
    if _env_path.exists():
        load_dotenv(_env_path, override=True)


def _env(key: str, default: str = "") -> str:
    """读取环境变量，并把 .env.example 里的占位值（your_xxx）视为“未配置”"""
    value = os.getenv(key, default).strip()
    if value.startswith("your_"):
        return ""
    return value


LLM_API_KEY = _env("LLM_API_KEY")
LLM_BASE_URL = _env("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_MODEL = _env("LLM_MODEL", "deepseek-chat")

ADMIN_USERNAME = _env("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = _env("ADMIN_PASSWORD", "admin123")

# Embedding 与 DashScope 共用同一个阿里云百炼 Key，只填一个即可
_EMBEDDING_KEY = _env("EMBEDDING_API_KEY")
_DASHSCOPE_KEY = _env("DASHSCOPE_API_KEY")
EMBEDDING_API_KEY = _EMBEDDING_KEY or _DASHSCOPE_KEY
EMBEDDING_BASE_URL = _env(
    "EMBEDDING_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
EMBEDDING_MODEL = _env("EMBEDDING_MODEL", "text-embedding-v4")

DASHSCOPE_API_KEY = _DASHSCOPE_KEY or _EMBEDDING_KEY
DASHSCOPE_BASE_URL = _env("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com")

# 语音合成（CosyVoice）
TTS_MODEL = _env("TTS_MODEL", "cosyvoice-v1")
TTS_VOICE = _env("TTS_VOICE", "longxiaochun")

# 视觉多模态大模型（Qwen-VL），用于"游客传图 -> 数字人识别讲解"
VL_MODEL = _env("VL_MODEL", "qwen-vl-max")


def missing_keys() -> list[str]:
    """返回尚未配置的必需/可选 API 配置项，供启动自检打印"""
    required = {
        "LLM_API_KEY": LLM_API_KEY,
        "EMBEDDING_API_KEY": EMBEDDING_API_KEY,
    }
    optional = {
        "DASHSCOPE_API_KEY": DASHSCOPE_API_KEY,
        "BAIDU_ASR_API_KEY": _env("BAIDU_ASR_API_KEY"),
        "BAIDU_ASR_SECRET_KEY": _env("BAIDU_ASR_SECRET_KEY"),
        "ALI_TTS_APPKEY": _env("ALI_TTS_APPKEY"),
    }
    missing = [f"[必需] {k}" for k, v in required.items() if not v]
    missing += [f"[可选] {k}" for k, v in optional.items() if not v]
    return missing
