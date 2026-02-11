"""CRUD операции для игроков."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Player
from game.constants import Archetype, START_COINS, START_TAP_POWER


async def get_player_by_tg_id(session: AsyncSession, tg_id: int) -> Player | None:
    """Получить игрока по Telegram ID."""
    result = await session.execute(
        select(Player).where(Player.tg_id == tg_id)
    )
    return result.scalar_one_or_none()


async def create_player(
    session: AsyncSession,
    tg_id: int,
    username: str | None,
    name: str,
    avatar: str,
    archetype: Archetype,
) -> Player:
    """Создать нового игрока."""
    player = Player(
        tg_id=tg_id,
        username=username,
        name=name,
        avatar=avatar,
        archetype=archetype,
        coins=START_COINS,
        tap_power=START_TAP_POWER,
    )
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


async def player_exists(session: AsyncSession, tg_id: int) -> bool:
    """Проверить, существует ли игрок."""
    result = await session.execute(
        select(Player.id).where(Player.tg_id == tg_id)
    )
    return result.scalar_one_or_none() is not None
