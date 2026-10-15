"""
操作日志服务
"""
import json
from sqlalchemy.orm import Session
from models.operation_log import OperationLog


def record_log(
    db: Session,
    admin_id: int | None,
    admin_name: str,
    action: str,
    detail: str = "",
    ip_address: str = ""
) -> OperationLog:
    """
    记录一条操作日志。
    admin_id 为 None 表示系统自动操作。
    """
    log = OperationLog(
        admin_id=admin_id,
        admin_name=admin_name,
        action=action,
        detail=detail,
        ip_address=ip_address
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def record_log_dict(db: Session, admin_id: int | None, admin_name: str,
                    action: str, detail_dict: dict, ip_address: str = ""):
    """以 dict 形式记录详情（自动转 JSON 字符串）"""
    return record_log(
        db, admin_id, admin_name, action,
        json.dumps(detail_dict, ensure_ascii=False),
        ip_address
    )
