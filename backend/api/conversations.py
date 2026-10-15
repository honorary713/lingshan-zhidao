import os
import uuid
import asyncio
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 数据库导入
from database import SessionLocal, get_db
from models.faq import UnresolvedQuestion
from models.conversation import ConversationHistory
from models.admin import AdminUser
from middleware.auth_middleware import get_current_admin
from middleware.rate_limit import rate_limiter
from utils.response import success_response, error_response, paginated_response
from services.agent_service import answer_with_agent
from services.tts_service import text_to_speech_base64
from services.asr_service import recognize_audio_bytes

# 定义请求体模型
class ChatReq(BaseModel):
    question: str
    session_id: str = ""

class ScoreReq(BaseModel):
    log_id: int
    score: int

router = APIRouter()

# TTS 后台音频缓存（TTL 机制）
import time as _time

_AUDIO_CACHE_TTL = 120
_audio_cache: Dict[int, Tuple[str, float]] = {}


def _start_tts_background(log_id: int, text: str):
    """后台异步生成 TTS 音频，完成后写入 _audio_cache"""

    async def _tts_job():
        try:
            audio_b64 = await text_to_speech_base64(text)
            _audio_cache[log_id] = (audio_b64 or "", _time.time())
        except Exception as e:
            _audio_cache[log_id] = ("", _time.time())

    asyncio.create_task(_tts_job())

# ===================== 游客端接口 =====================
@router.post("/chat")
async def chat(req: ChatReq, request: Request):
    await rate_limiter(request)
    db = SessionLocal()
    user_question = req.question

    try:
        active_session_id = req.session_id or str(uuid.uuid4())
        result = answer_with_agent(user_question, db, active_session_id)
        ai_answer = result["answer"]
    except Exception as e:
        db.close()
        err_msg = f"问答处理出错: {str(e)}\n{traceback.format_exc()}"
        print(err_msg)
        raise HTTPException(status_code=500, detail=err_msg)

    # 写入对话记录
    new_session_id = active_session_id
    new_conv = ConversationHistory(
        session_id=new_session_id,
        user_identifier="frontend_visitor",
        question=user_question,
        answer=ai_answer,
        retrieved_docs=result.get("retrieved_docs", ""),
        is_sensitive_blocked=result.get("is_sensitive_blocked", False)
    )
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)

    log_id = new_conv.id
    answer = new_conv.answer
    db.close()

    # 文字立即返回，TTS 后台异步执行
    _start_tts_background(log_id, answer)

    return {
        "log_id": log_id,
        "answer": answer,
        "audio": "",
        "sources": result.get("sources", []),
    }

# ---------------------- 语音识别接口 POST /api/chat/asr ----------------------

@router.post("/chat/asr")
async def speech_to_text(file: UploadFile = File(...)):
    """接收前端录音，调用百度 ASR 返回识别文字"""
    audio_bytes = await file.read()
    if not audio_bytes or len(audio_bytes) < 800:
        raise HTTPException(status_code=400, detail="音频数据无效或太短")

    text = await recognize_audio_bytes(audio_bytes, format="wav")
    if not text:
        raise HTTPException(status_code=422, detail="未能识别出语音内容，请重试")

    return {"text": text}

# ---------------------- 音频获取接口 GET /api/chat/audio/{log_id} ----------------------
@router.get("/chat/audio/{log_id}")
async def get_audio(log_id: int):
    """前端轮询获取后台 TTS 生成的音频"""
    if log_id not in _audio_cache:
        return {"status": "pending", "audio": ""}

    entry = _audio_cache.pop(log_id, None)
    if entry is None:
        return {"status": "pending", "audio": ""}

    audio_b64, stored_at = entry
    # 检查是否过期
    if _time.time() - stored_at > _AUDIO_CACHE_TTL:
        return {"status": "failed", "audio": ""}

    if not audio_b64:
        return {"status": "failed", "audio": ""}
    return {"status": "ready", "audio": audio_b64}


# 定期清理过期缓存
def _purge_stale_audio():
    now = _time.time()
    stale = [k for k, (_, t) in _audio_cache.items() if now - t > _AUDIO_CACHE_TTL]
    for k in stale:
        _audio_cache.pop(k, None)


# ---------------------- 游客打分接口 POST /api/chat/score ----------------------
@router.post("/chat/score")
async def submit_score(req: ScoreReq):
    db = SessionLocal()
    target_conv = db.query(ConversationHistory).filter(ConversationHistory.id == req.log_id).first()
    if not target_conv:
        db.close()
        return error_response(404, "对话记录不存在")
    target_conv.rating = req.score
    db.commit()
    db.close()
    return success_response(None, "评分提交成功")

# ===================== 管理员对话查询接口 =====================
@router.get("/conversations")
def list_conversations(
    page: int = 1, page_size: int = 20,
    date_from: str = "", date_to: str = "",
    keyword: str = "",
    rating_min: int = None, rating_max: int = None,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取对话历史列表（支持多条件筛选）"""
    query = db.query(ConversationHistory)

    # 日期筛选
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(ConversationHistory.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(ConversationHistory.created_at < dt_to)
        except ValueError:
            pass

    # 关键词搜索（搜索问题文本）
    if keyword:
        query = query.filter(ConversationHistory.question.contains(keyword))

    # 评分筛选
    if rating_min is not None:
        query = query.filter(ConversationHistory.rating >= rating_min)
    if rating_max is not None:
        query = query.filter(ConversationHistory.rating <= rating_max)

    total = query.count()
    items = query.order_by(ConversationHistory.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return paginated_response(
        [c.to_dict() for c in items], total, page, page_size
    )

@router.get("/conversations/{conv_id}")
def get_conversation(
    conv_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取单条对话详情"""
    conv = db.query(ConversationHistory).filter(ConversationHistory.id == conv_id).first()
    if not conv:
        return error_response(404, "对话记录不存在")
    return success_response(conv.to_dict())

# ===================== 新增管理员：移入处理接口（低分对话一键转入待解决问题） =====================
@router.post("/conversations/move-pending/{conv_id}")
def move_to_pending(
    conv_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """将低分对话移入待解决问题列表"""
    # 1. 查询对话
    conv = db.query(ConversationHistory).filter(ConversationHistory.id == conv_id).first()
    if not conv:
        return error_response(404, "对话记录不存在")
    # 2. 判断是否已迁移过，防止重复提交
    if conv.moved_to_pending is True:
        return error_response(400, "该对话问题已移入待解决列表，无需重复操作")

    question_text = conv.question.strip()
    if not question_text:
        return error_response(400, "提问内容为空，无法移入")

    # 3. 查询是否已存在同一条待处理问题（pending）
    exist_item = db.query(UnresolvedQuestion).filter(
        UnresolvedQuestion.question == question_text,
        UnresolvedQuestion.status == "pending"
    ).first()

    if exist_item:
        # 已有相同待解决问题，仅累加提问次数，绑定关联
        exist_item.ask_count += 1
        conv.unresolved_id = exist_item.id
        conv.moved_to_pending = True
        db.commit()
        return success_response(exist_item.to_dict(), "已关联至现有待解决问题")
    else:
        # 4. 新建一条待解决问题
        new_pending = UnresolvedQuestion(
            question=question_text,
            ask_count=1,
            status="pending"
        )
        db.add(new_pending)
        db.flush() # 获取自增ID

        # 标记对话已迁移，绑定外键
        conv.unresolved_id = new_pending.id
        conv.moved_to_pending = True
        db.commit()
        return success_response(new_pending.to_dict(), "成功移入待解决问题列表")
