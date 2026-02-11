"""Middleware авторизации: загрузка игрока в контекст каждого запроса."""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from db.database import async_session
from db.repositories.player import get_player_by_tg_id

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Загружает объект Player из БД и кладёт в data['player'].
    Если игрок не найден — player=None (онбординг обработает)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Получаем tg_id из любого типа события
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        async with async_session() as session:
            player = await get_player_by_tg_id(session, user.id)
            data["player"] = player
            data["db_session"] = session
            return await handler(event, data)
