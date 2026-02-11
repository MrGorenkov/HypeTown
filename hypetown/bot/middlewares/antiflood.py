"""Antiflood middleware: защита от спама через Redis sliding window."""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from services.redis_service import check_rate_limit

logger = logging.getLogger(__name__)

# Лимиты: количество запросов / окно в секундах
DEFAULT_LIMIT = 30
DEFAULT_WINDOW = 60


class AntifloodMiddleware(BaseMiddleware):
    """Rate limiter: не более DEFAULT_LIMIT запросов в DEFAULT_WINDOW секунд."""

    def __init__(self, limit: int = DEFAULT_LIMIT, window: int = DEFAULT_WINDOW):
        self.limit = limit
        self.window = window

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        allowed = await check_rate_limit(user.id, self.limit, self.window)
        if not allowed:
            logger.warning("Rate limit: tg_id=%d", user.id)
            # Не отвечаем — просто дропаем
            return None

        return await handler(event, data)
