# rate_limiter.py
import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = structlog.get_logger()


class SlidingWindowRateLimiter:
    """
    Высокопроизводительный sliding window rate limiter.
    - Точный расчет Retry-After (до секунды освобождения слота)
    - Автоматическая очистка устаревших IP (предотвращение утечек памяти)
    - Исключение служебных эндпоинтов (/health, /metrics)
    """

    def __init__(self, requests_per_minute: int = 60, cleanup_interval_sec: int = 300):
        self.requests_per_minute = requests_per_minute
        self.window_sec = 60
        self.cleanup_interval_sec = cleanup_interval_sec
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._last_cleanup = time.time()
        self._lock = asyncio.Lock()

    def _cleanup_stale_keys(self, now: float):
        """Периодическая очистка IP, не делавших запросы дольше размера окна."""
        if now - self._last_cleanup < self.cleanup_interval_sec:
            return

        window_start = now - self.window_sec
        stale_keys = [
            k for k, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] <= window_start
        ]
        for k in stale_keys:
            del self._requests[k]

        self._last_cleanup = now
        logger.debug("rate_limiter_cleaned_stale_keys", removed_keys=len(stale_keys))

    async def is_allowed(self, key: str) -> Tuple[bool, int, int]:
        """
        Проверяет, разрешен ли запрос.
        Возвращает: (is_allowed, remaining_requests, retry_after_sec)
        """
        async with self._lock:
            now = time.time()
            window_start = now - self.window_sec

            # Авто-очистка устаревших ключей
            self._cleanup_stale_keys(now)

            # Очищаем запросы старше 60 секунд для текущего ключа
            valid_requests = [t for t in self._requests[key] if t > window_start]
            self._requests[key] = valid_requests

            # Проверяем лимит
            if len(valid_requests) >= self.requests_per_minute:
                oldest_request = valid_requests[0]
                retry_after = max(1, int(oldest_request + self.window_sec - now))
                return False, 0, retry_after

            # Добавляем текущий запрос
            self._requests[key].append(now)
            remaining = self.requests_per_minute - len(self._requests[key])
            return True, remaining, 0


_rate_limiter: Optional[SlidingWindowRateLimiter] = None


def get_rate_limiter(requests_per_minute: int = 60) -> SlidingWindowRateLimiter:
    """Получить глобальный rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = SlidingWindowRateLimiter(requests_per_minute=requests_per_minute)
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware для rate limiting на основе Sliding Window.
    Защищает API от перегрузок и брутфорса, пропуская системные эндпоинты.
    """

    EXEMPT_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json", "/"}

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rate_limiter = get_rate_limiter(requests_per_minute)

    async def dispatch(self, request: Request, call_next):
        # Исключаем системные и мониторинговые маршруты
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Извлекаем IP с учетом прокси (X-Forwarded-For, X-Real-IP)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")

        is_allowed, remaining, retry_after = await self.rate_limiter.is_allowed(client_ip)

        if not is_allowed:
            logger.warning(
                "rate_limit_exceeded",
                ip=client_ip,
                path=request.url.path,
                retry_after=retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.rate_limiter.requests_per_minute} requests per minute",
                    "retry_after_seconds": retry_after,
                    "request_id": getattr(request.state, "request_id", None),
                },
                headers={
                    "X-RateLimit-Limit": str(self.rate_limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(retry_after),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
