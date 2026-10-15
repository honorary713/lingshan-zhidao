"""
ASR 语音识别服务（百度语音识别 API）
"""
import os
import time
import requests

def _env(key: str) -> str:
    """读取环境变量，占位值（your_xxx）视为未配置"""
    value = os.environ.get(key, "").strip()
    return "" if value.startswith("your_") else value


# 百度 ASR 密钥：未配置时语音识别不可用，前端麦克风按钮会提示识别失败
_API_KEY_ASR = _env("BAIDU_ASR_API_KEY")
_SECRET_KEY_ASR = _env("BAIDU_ASR_SECRET_KEY")

# token 缓存
_cached_token = None
_token_expires_at = 0


def _get_baidu_token():
    """获取百度 OAuth2 access_token（带缓存）"""
    global _cached_token, _token_expires_at

    if _cached_token and time.time() < _token_expires_at - 60:
        return _cached_token

    if not _API_KEY_ASR or not _SECRET_KEY_ASR:
        raise RuntimeError("未配置百度 ASR 密钥，请设置环境变量 BAIDU_ASR_API_KEY 和 BAIDU_ASR_SECRET_KEY")

    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": _API_KEY_ASR,
        "client_secret": _SECRET_KEY_ASR
    }
    try:
        resp = requests.post(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        _cached_token = data.get("access_token")
        _token_expires_at = time.time() + 25 * 24 * 3600
        return _cached_token
    except Exception as e:
        print(f"[ASR] 获取百度 token 失败: {e}")
        raise RuntimeError(f"语音服务连接失败: {e}")


async def recognize_audio_bytes(audio_bytes: bytes, format: str = "wav") -> str:
    """
    调用百度语音识别 API 将音频转为文字
    """
    if not audio_bytes or len(audio_bytes) < 800:
        return ""

    token = _get_baidu_token()
    url = f"https://vop.baidu.com/server_api?dev_pid=1537&cuid=web_visitor&token={token}"
    headers = {"Content-Type": f"audio/{format}; rate=16000"}

    try:
        res = requests.post(url, data=audio_bytes, headers=headers, timeout=10)
        result = res.json()
        err_no = result.get("err_no", -1)
        if err_no == 0 and result.get("result"):
            text = result["result"][0].strip()
            print(f"[ASR] 识别成功: {text[:50]}...")
            return text
        else:
            err_msg = result.get("err_msg", "未知错误")
            print(f"[ASR] 识别失败 err_no={err_no}: {err_msg}")
            return ""
    except requests.exceptions.Timeout:
        print("[ASR] 请求超时")
        return ""
    except Exception as e:
        print(f"[ASR] 异常: {e}")
        return ""
