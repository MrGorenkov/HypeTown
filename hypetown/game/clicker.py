"""Бизнес-логика кликера: формулы тапа, апгрейды, мультипликаторы."""

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ClickerUpgrade, Player
from game.constants import (
    ARCHETYPES,
    CLICKER_UPGRADES,
    ClickerUpgradeType,
)


def calc_upgrade_cost(upgrade_key: str, current_level: int) -> int:
    """Стоимость апгрейда на следующий уровень."""
    info = CLICKER_UPGRADES[upgrade_key]
    return int(info["base_cost"] * (info["cost_mult"] ** current_level))


def calc_tap_power(upgrades: list[ClickerUpgrade], archetype: str) -> int:
    """Вычислить итоговую силу тапа с учётом всех апгрейдов и архетипа.

    tap_power = (1 + sum(tap_bonus * level)) * multipliers * archetype_bonus
    """
    base_tap = 1
    additive = 0
    multiplier = 1.0

    for upg in upgrades:
        info = CLICKER_UPGRADES.get(upg.upgrade_type.value, {})
        if "tap_bonus" in info:
            additive += info["tap_bonus"] * upg.level
        if "multiplier" in info and upg.level > 0:
            multiplier *= info["multiplier"] ** upg.level

    # Бонус архетипа «Блогер» — +20% к кликеру
    arch = ARCHETYPES.get(archetype, {})
    if arch.get("bonus_type") == "clicker":
        multiplier *= 1.0 + arch["bonus"]

    return max(1, int((base_tap + additive) * multiplier))


async def process_tap(
    session: AsyncSession,
    player: Player,
    tap_count: int = 1,
) -> dict:
    """Обработать тап(ы): начислить монеты, вернуть результат.

    Возвращает: {"earned": int, "total_coins": int, "tap_power": int}
    """
    tap_count = min(tap_count, 50)
    earned = player.tap_power * tap_count
    player.coins += earned
    await session.commit()

    return {
        "earned": earned,
        "total_coins": player.coins,
        "tap_power": player.tap_power,
    }


async def buy_upgrade(
    session: AsyncSession,
    player: Player,
    upgrade_key: str,
) -> dict:
    """Купить апгрейд кликера.

    Возвращает: {"ok": bool, "error"?: str, "new_level"?: int, "new_tap_power"?: int, "cost"?: int}
    """
    if upgrade_key not in CLICKER_UPGRADES:
        return {"ok": False, "error": "unknown_upgrade"}

    info = CLICKER_UPGRADES[upgrade_key]
    upgrade_type = ClickerUpgradeType(upgrade_key)

    # Найти текущий апгрейд игрока
    current = None
    for upg in player.clicker_upgrades:
        if upg.upgrade_type == upgrade_type:
            current = upg
            break

    current_level = current.level if current else 0

    # Проверка лимита
    if current_level >= info["max_level"]:
        return {"ok": False, "error": "max_level"}

    # Стоимость
    cost = calc_upgrade_cost(upgrade_key, current_level)
    if player.coins < cost:
        return {"ok": False, "error": "not_enough_coins", "cost": cost}

    # Покупка
    player.coins -= cost

    if current:
        current.level += 1
    else:
        new_upg = ClickerUpgrade(
            player_id=player.id,
            upgrade_type=upgrade_type,
            level=1,
        )
        session.add(new_upg)
        player.clicker_upgrades.append(new_upg)

    # Пересчёт tap_power
    new_tap_power = calc_tap_power(player.clicker_upgrades, player.archetype.value)
    player.tap_power = new_tap_power

    await session.commit()

    return {
        "ok": True,
        "new_level": current_level + 1,
        "new_tap_power": new_tap_power,
        "cost": cost,
    }


def get_upgrades_info(player: Player) -> list[dict]:
    """Получить инфо обо всех апгрейдах для отображения в UI."""
    result = []

    # Словарь текущих уровней
    owned = {}
    for upg in player.clicker_upgrades:
        owned[upg.upgrade_type.value] = upg.level

    for key, info in CLICKER_UPGRADES.items():
        level = owned.get(key, 0)
        maxed = level >= info["max_level"]
        cost = calc_upgrade_cost(key, level) if not maxed else 0

        # Описание бонуса
        if "tap_bonus" in info:
            bonus = f"+{info['tap_bonus']} за тап"
        else:
            bonus = f"x{info['multiplier']} множитель"

        result.append({
            "key": key,
            "name": key.replace("_", " ").title(),
            "bonus": bonus,
            "level": level,
            "max_level": info["max_level"],
            "cost": cost,
            "maxed": maxed,
            "affordable": player.coins >= cost and not maxed,
        })

    return result
