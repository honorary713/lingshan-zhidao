"""
TTS 语音合成服务
优先级：阿里云 NLS（可选）→ 百度语音合成（主，精品/臻品音库）→ edge-tts（免费兜底）
"""
import asyncio
import base64
import os
import time
import hashlib
import hmac
import uuid
import logging
from urllib.parse import quote, urlencode
import aiohttp

tts_logger = logging.getLogger("lingshan.tts")

# ===== 阿里云 TTS 配置 =====
# AppKey 从环境变量/配置文件读取（可选）；未配置时自动降级到免费的 edge-tts
ALI_TTS_APPKEY = os.environ.get("ALI_TTS_APPKEY", "")
ALI_TTS_VOICE = "zhixiaomei"  # 知小妹（直播数字人）

# ===== 百度语音合成（主通道，复用百度应用的 API Key / Secret Key）=====
BAIDU_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
BAIDU_TTS_URL = "https://tsn.baidu.com/text2audio"
BAIDU_DEFAULT_PER = "0"  # 度小美（百度基础音库，免费）

# 旧音色名（阿里云 NLS / 通用名）→ 百度 per 编号，避免历史配置失效
BAIDU_LEGACY_VOICE_MAP = {
    "zhixiaomei": "0", "zhixiaoyun": "0", "zhixiaoyue": "5118",
    "zhixiaowei": "4105", "zhixiaoxue": "4100",
    "xiaomei": "111", "xiaoyun": "5118", "ruoxi": "4105", "sijia": "4100",
    "xiaogang": "106", "aishuo": "5003",
}

_baidu_token_cache = {"token": "", "expire": 0}

# ===== 阿里云 Token 获取地址 =====
TOKEN_URL = "https://nls-meta.cn-shanghai.aliyuncs.com/pop/2018-05-18/tokens"
# TTS REST API 地址
TTS_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/tts"

# Token 缓存
_cached_ali_token = None
_cached_ali_token_expire = 0


def _get_ali_credentials():
    """获取阿里云 AccessKey 密钥对"""
    ak_id = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
    ak_secret = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")
    if not ak_id:
        try:
            from database import SessionLocal
            from models.system import ApiKey
            db = SessionLocal()
            try:
                key = db.query(ApiKey).filter(
                    ApiKey.provider == "aliyun_tts",
                    ApiKey.is_active == True
                ).first()
                if key:
                    ak_id = key.api_key
                    ak_secret = key.api_secret or ""
            finally:
                db.close()
        except Exception:
            pass
    return ak_id, ak_secret


async def _get_ali_token() -> str:
    """获取阿里云 TTS 的 AccessToken（带缓存）"""
    global _cached_ali_token, _cached_ali_token_expire
    now = time.time()
    if _cached_ali_token and now < _cached_ali_token_expire - 300:
        return _cached_ali_token

    ak_id, ak_secret = _get_ali_credentials()
    if not ak_id or not ak_secret:
        raise RuntimeError("未配置阿里云 TTS AccessKey")

    params = {
        "AccessKeyId": ak_id,
        "Action": "CreateToken",
        "Version": "2019-02-28",
        "Format": "JSON",
        "RegionId": "cn-shanghai",
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "SignatureMethod": "HMAC-SHA1",
        "SignatureVersion": "1.0",
        "SignatureNonce": str(uuid.uuid4()),
    }
    sorted_params = sorted(params.items())
    query_string = urlencode(sorted_params)
    string_to_sign = "GET&%2F&" + quote(query_string, safe="")
    signature = hmac.new(
        (ak_secret + "&").encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1
    ).digest()
    params["Signature"] = base64.b64encode(signature).decode("utf-8")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(TOKEN_URL, params=params, timeout=10) as resp:
                data = await resp.json()
                token_info = data.get("Token", {})
                _cached_ali_token = token_info.get("Id", "")
                expire_time = token_info.get("ExpireTime", int(now) + 86400)
                if isinstance(expire_time, str):
                    from datetime import datetime as dt
                    expire_time = dt.fromisoformat(expire_time.replace("Z", "+00:00")).timestamp()
                _cached_ali_token_expire = expire_time
                tts_logger.info("阿里云 TTS Token 获取成功")
                return _cached_ali_token
    except Exception as e:
        tts_logger.warning(f"阿里云 Token 获取失败: {e}")
        raise


async def aliyun_tts(text: str, appkey: str = "", voice: str = "",
                    speech_rate: int = 0, pitch_rate: int = 0) -> bytes:
    """调用阿里云语音合成 REST API，返回 PCM 音频字节"""
    appkey = appkey or ALI_TTS_APPKEY
    voice = voice or ALI_TTS_VOICE
    if not appkey:
        raise RuntimeError("未配置 ALI_TTS_APPKEY，跳过阿里云 TTS")
    token = await _get_ali_token()

    body = {
        "appkey": appkey,
        "token": token,
        "text": text,
        "format": "wav",
        "sample_rate": 16000,
        "voice": voice,
        "volume": 50,
        "speech_rate": speech_rate,
        "pitch_rate": pitch_rate,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(TTS_URL, json=body, timeout=30) as resp:
                if resp.status == 200:
                    audio_bytes = await resp.read()
                    content_type = resp.headers.get("Content-Type", "")
                    if "audio" in content_type or "octet-stream" in content_type or len(audio_bytes) > 200:
                        tts_logger.info(f"阿里云 TTS 合成成功: {text[:30]}... ({len(audio_bytes)} bytes)")
                        return audio_bytes
                    else:
                        error_text = audio_bytes.decode("utf-8", errors="ignore")[:200]
                        tts_logger.warning(f"阿里云 TTS 返回非音频: {error_text}")
                        raise RuntimeError(f"TTS 服务返回异常: {error_text}")
                else:
                    error_text = await resp.text()
                    tts_logger.warning(f"阿里云 TTS HTTP {resp.status}: {error_text[:200]}")
                    raise RuntimeError(f"TTS 请求失败 HTTP {resp.status}")
    except Exception:
        raise


def normalize_baidu_voice(voice_name: str) -> str:
    """把后台音色值统一成百度 per 编号；无法识别时回落到默认音色"""
    if not voice_name:
        return BAIDU_DEFAULT_PER
    name = str(voice_name).strip()
    if name.isdigit():
        return name
    return BAIDU_LEGACY_VOICE_MAP.get(name, BAIDU_DEFAULT_PER)


def to_baidu_params(speed: float, intonation: float) -> tuple[int, int]:
    """后台语速/语调 0.5~3.0 → 百度 spd/pit 0~15"""
    spd = int(round(max(0.5, min(3.0, speed)) * 5))
    pit = int(round(max(0.5, min(3.0, intonation)) * 5))
    return max(0, min(15, spd)), max(0, min(15, pit))


async def _get_baidu_token() -> str:
    """获取百度 access_token（带缓存，与 ASR 共用同一组 Key）"""
    from app.config import _env

    api_key = _env("BAIDU_ASR_API_KEY")
    secret_key = _env("BAIDU_ASR_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError("未配置百度 API Key / Secret Key，跳过百度 TTS")

    now = time.time()
    if _baidu_token_cache["token"] and now < _baidu_token_cache["expire"] - 86400:
        return _baidu_token_cache["token"]

    payload = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(BAIDU_TOKEN_URL, data=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            data = await resp.json(content_type=None)

    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"百度 access_token 获取失败: {str(data)[:200]}")

    _baidu_token_cache["token"] = token
    _baidu_token_cache["expire"] = now + int(data.get("expires_in", 2592000))
    return token


async def baidu_tts(text: str, per: str = None, spd: int = 5, pit: int = 5, vol: int = 8) -> bytes:
    """调用百度短文本在线合成，返回 MP3 字节流"""
    token = await _get_baidu_token()
    payload = {
        "tex": text[:1000],
        "tok": token,
        "cuid": "lingshan-guide",
        "ctp": "1",
        "lan": "zh",
        "per": per or BAIDU_DEFAULT_PER,
        "spd": str(spd),
        "pit": str(pit),
        "vol": str(vol),
        "aue": "3",  # mp3
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(BAIDU_TTS_URL, data=payload, timeout=aiohttp.ClientTimeout(total=20)) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if not content_type.startswith("audio"):
                err = await resp.text()
                raise RuntimeError(f"百度 TTS 返回异常: {err[:200]}")
            return await resp.read()


async def _edge_tts_fallback(text: str) -> bytes:
    """edge-tts 兜底"""
    import edge_tts
    communicate = edge_tts.Communicate(text, "zh-CN-XiaohanNeural")
    mp3_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_bytes += chunk["data"]
    return mp3_bytes


# ===== 对外接口 =====

async def text_to_speech_bytes(text: str) -> bytes:
    """
    文字转语音字节流，优先阿里云 TTS，失败 fallback edge-tts.
    返回 WAV(PCM) 或 MP3 音频的原始 bytes.
    自动从数据库读取数字人音色/语速/语调配置。
    """
    if not text or not text.strip():
        return b""

    # 从数据库读取音色配置
    voice_name = ALI_TTS_VOICE
    speech_rate = 0
    pitch_rate = 0
    voice_speed = 1.0
    voice_intonation = 1.0
    try:
        from database import SessionLocal
        from models.digital_human import DigitalHumanConfig
        db = SessionLocal()
        try:
            config = db.query(DigitalHumanConfig).first()
            if config:
                voice_name = config.voice_timbre or ALI_TTS_VOICE
                # voice_speed 0.5~3.0 → speech_rate -500~500
                voice_speed = float(config.voice_speed or 1.0)
                speed = max(0.5, min(3.0, voice_speed))
                speech_rate = int((speed - 1.0) * 500)
                # voice_intonation 0.5~3.0 → pitch_rate -500~500
                voice_intonation = float(config.voice_intonation or 1.0)
                into = max(0.5, min(3.0, voice_intonation))
                pitch_rate = int((into - 1.0) * 500)
        finally:
            db.close()
    except Exception as e:
        tts_logger.warning(f"读取数字人音色配置失败，使用默认值: {e}")

    tts_logger.info(f"TTS 参数: voice={voice_name}, speed={speech_rate}, pitch={pitch_rate}")

    # 尝试百度 TTS（精品/臻品音库）
    try:
        per = normalize_baidu_voice(voice_name)
        spd, pit = to_baidu_params(voice_speed, voice_intonation)
        result = await baidu_tts(text, per=per, spd=spd, pit=pit)
        if result:
            tts_logger.info(f"百度 TTS 合成成功: per={per}, {len(result)} bytes")
            return result
        raise RuntimeError("百度 TTS 返回空音频")
    except Exception as e:
        tts_logger.error(f"百度 TTS 失败: {e}")

    # 尝试阿里云 TTS
    try:
        result = await aliyun_tts(text, voice=voice_name,
                                  speech_rate=speech_rate, pitch_rate=pitch_rate)
        tts_logger.info(f"阿里云 TTS 合成成功: {len(result)} bytes")
        return result
    except Exception as e:
        tts_logger.error(f"阿里云 TTS 失败: {e}")

    # edge-tts 兜底
    try:
        tts_logger.info("降级到 edge-tts")
        return await _edge_tts_fallback(text)
    except Exception as e2:
        tts_logger.error(f"TTS 全部失败: {e2}")
        return b""


async def text_to_speech_base64(text: str, voice: str = None, rate: str = None, pitch: str = None) -> str:
    """文字转 base64 编码的音频（前端直接播放）。voice/rate/pitch 参数保留兼容，实际由内部决定。"""
    audio_bytes = await text_to_speech_bytes(text)
    if not audio_bytes:
        return ""
    return base64.b64encode(audio_bytes).decode("utf-8")


# 保留兼容旧接口的配音配置
TIMBRE_MAP: dict[str, str] = {}
DEFAULT_VOICE = "zhixiaomei"


def get_voice_config(db_session) -> tuple[str, str, str]:
    """从数据库读取数字人语音配置（兼容旧接口）"""
    try:
        from models.digital_human import DigitalHumanConfig
        config = db_session.query(DigitalHumanConfig).first()
        if config:
            voice_name = config.voice_timbre or DEFAULT_VOICE
            speed = float(config.voice_speed or 1.0)
            speed = max(0.5, min(2.0, speed))
            rate = f"{int((speed - 1) * 100):+d}%"
            into = float(config.voice_intonation or 1.0)
            into = max(0.5, min(2.0, into))
            pitch_hz = int((into - 1) * 50)
            pitch = f"{pitch_hz:+d}Hz"
            return voice_name, rate, pitch
    except Exception:
        pass
    return DEFAULT_VOICE, "+0%", "+0Hz"
