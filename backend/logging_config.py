"""
日志系统：替代所有 print()，支持控制台 + 按天切割文件
"""
import logging
import os
from pathlib import Path
from datetime import datetime

# 日志目录
LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 今天的日志文件
_today_log_file = LOG_DIR / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"

# 格式
_FORMAT = logging.Formatter(
    "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 文件 handler
_file_handler = logging.FileHandler(str(_today_log_file), encoding="utf-8")
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(_FORMAT)

# 控制台 handler
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """获取命名 logger，同时输出到控制台和文件"""
    logger = logging.getLogger(name)
    # 避免重复添加 handler
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(_file_handler)
        logger.addHandler(_console_handler)
        logger.propagate = False
    return logger

# 预定义常用 logger
app_logger = get_logger("lingshan.app")
db_logger = get_logger("lingshan.db")
api_logger = get_logger("lingshan.api")
llm_logger = get_logger("lingshan.llm")
embedding_logger = get_logger("lingshan.embedding")
asr_logger = get_logger("lingshan.asr")
tts_logger = get_logger("lingshan.tts")
