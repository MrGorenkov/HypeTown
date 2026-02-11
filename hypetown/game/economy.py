"""Формулы экономики: XP, уровни, прогрессия."""

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Player
from game.constants import BASE_XP_PER_LEVEL, XP_LEVEL_EXPONENT


def xp_for_level(level: int) -> int:
    """XP, необходимый для достижения уровня."""
    return int(BASE_XP_PER_LEVEL * (level ** XP_LEVEL_EXPONENT))


def xp_to_next_level(player: Player) -> int:
    """Сколько XP до следующего уровня."""
    required = xp_for_level(player.level + 1)
    return max(0, required - player.xp)


async def add_xp(session: AsyncSession, player: Player, amount: int) -> dict:
    """Начислить XP и проверить повышение уровня.

    Возвращает: {"xp_added": int, "leveled_up": bool, "new_level"?: int}
    """
    player.xp += amount
    leveled_up = False
    new_level = player.level

    # Проверяем повышение (может быть несколько уровней за раз)
    while player.xp >= xp_for_level(player.level + 1):
        player.level += 1
        leveled_up = True
        new_level = player.level

    await session.commit()

    result = {"xp_added": amount, "leveled_up": leveled_up}
    if leveled_up:
        result["new_level"] = new_level
    return result
