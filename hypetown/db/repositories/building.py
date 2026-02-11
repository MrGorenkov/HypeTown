"""CRUD операции для зданий."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Building


async def get_player_buildings(session: AsyncSession, player_id: int) -> list[Building]:
    """Получить все здания игрока."""
    result = await session.execute(
        select(Building).where(Building.player_id == player_id)
    )
    return list(result.scalars().all())


async def get_ready_buildings(session: AsyncSession) -> list[Building]:
    """Получить все здания, где производство завершено (для уведомлений)."""
    now = datetime.utcnow()
    result = await session.execute(
        select(Building).where(
            Building.is_producing == True,
            Building.production_ends <= now,
        )
    )
    return list(result.scalars().all())
