"""
统一导入所有模型，确保 Base.metadata.create_all() 能创建所有表
"""
from models.admin import AdminUser
from models.digital_human import DigitalHumanConfig, SensitiveWord
from models.scenic import ScenicArea, ScenicSpot
from models.faq import FAQ, UnresolvedQuestion
from models.conversation import ConversationHistory
from models.blacklist import Blacklist
from models.system import ApiKey, SystemConfig
from models.operation_log import OperationLog
from models.visitor import VisitorRecord


# 所有模型列表，供 init_db 使用
all_models = [
    AdminUser, DigitalHumanConfig, SensitiveWord,
    ScenicArea, ScenicSpot, FAQ, UnresolvedQuestion,
    ConversationHistory, Blacklist, ApiKey, SystemConfig,
    OperationLog
]
