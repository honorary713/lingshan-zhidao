"""
IP 限流中间件：按 IP 限制公开 API 的请求频率
"""
import time
import threading
from collections import defaultdict
from fastapi import Request, HTTPException

# 限流窗口：60 秒内最多 N 次请求
_WINDOW_SECONDS = 60
_MAX_REQUESTS = 30  # 游客端公开接口

# { ip: [timestamp, timestamp, ...] }
_hits: dict[str, list[float]] = defaultdict(list)
_cleanup_times = 0
_lock = threading.Lock()


def _cleanup():
    """每隔一段时间清理过期记录"""
    now = time.time()
    with _lock:
        stale = [ip for ip, ts in _hits.items() if not ts or now - ts[-1] > _WINDOW_SECONDS * 2]
        for ip in stale:
            del _hits[ip]


class RateLimiter:
    def __init__(self, max_requests: int = _MAX_REQUESTS, window_seconds: int = _WINDOW_SECONDS):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def __call__(self, request: Request):
        global _cleanup_times
        _cleanup_times += 1
        if _cleanup_times % 100 == 0:
            _cleanup()

        ip = request.client.host if request.client else "unknown"
        now = time.time()

        with _lock:
            timestamps = _hits[ip]
            # 移除窗口外的记录
            timestamps = [t for t in timestamps if now - t < self.window_seconds]
            _hits[ip] = timestamps

            if len(timestamps) >= self.max_requests:
                raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")

            timestamps.append(now)


rate_limiter = RateLimiter()
