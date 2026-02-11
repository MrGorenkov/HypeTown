"""Бизнес-логика ферм: производство, таймеры, апгрейды зданий."""

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Building, Inventory, Player
from db.repositories.inventory import add_resource
from game.constants import ARCHETYPES, BUILDINGS, BuildingType, Resource

# Маппинг: тип здания → ресурс, который оно производит
BUILDING_RESOURCE_MAP: dict[str, str] = {
    "cinema_studio":  "film",
    "series_lot":     "series",
    "game_studio":    "game",
    "cyber_arena":    "stream",
    "recording":      "track",
    "concert_hall":   "concert",
    "sports_arena":   "match",
    "tv_studio":      "broadcast",
    "podcast_studio": "podcast",
}


def calc_production_time(building_type: str, level: int) -> int:
    """Время производства в секундах: base_time * 0.95^(level-1)."""
    info = BUILDINGS[building_type]
    return int(info["base_time"] * (0.95 ** (level - 1)))


def calc_farm_income(building_type: str, level: int, archetype: str) -> int:
    """Доход фермы: base_income * 1.25^(level-1) * archetype_bonus."""
    info = BUILDINGS[building_type]
    income = info["base_income"] * (1.25 ** (level - 1))

    # Бонус архетипа к конкретной локации
    arch = ARCHETYPES.get(archetype, {})
    location = info["location"]
    bonus_map = {
        "cinema": "hollywood",
        "games": "gamer_street",
        "music": "music_hall",
        "sports": "sports",
    }
    if bonus_map.get(arch.get("bonus_type")) == location:
        income *= 1.0 + arch["bonus"]

    return int(income)


def calc_upgrade_cost(building_type: str, current_level: int) -> int:
    """Стоимость апгрейда здания: base_cost * 2^current_level."""
    info = BUILDINGS[building_type]
    return int(info["cost"] * (2 ** current_level))


async def buy_building(
    session: AsyncSession,
    player: Player,
    building_type: str,
) -> dict:
    """Купить новое здание."""
    if building_type not in BUILDINGS:
        return {"ok": False, "error": "unknown_building"}

    info = BUILDINGS[building_type]

    # Проверка уровня
    if player.level < info["unlock_level"]:
        return {"ok": False, "error": "level_locked", "required_level": info["unlock_level"]}

    # Проверка: уже есть?
    for b in player.buildings:
        if b.type.value == building_type:
            return {"ok": False, "error": "already_owned"}

    # Стоимость
    cost = info["cost"]
    if player.coins < cost:
        return {"ok": False, "error": "not_enough_coins", "cost": cost}

    player.coins -= cost
    building = Building(
        player_id=player.id,
        type=BuildingType(building_type),
        level=1,
    )
    session.add(building)
    player.buildings.append(building)
    await session.commit()

    return {"ok": True, "building_id": building.id, "cost": cost}


async def start_production(
    session: AsyncSession,
    player: Player,
    building_id: int,
) -> dict:
    """Запустить производство в здании."""
    building = None
    for b in player.buildings:
        if b.id == building_id:
            building = b
            break

    if not building:
        return {"ok": False, "error": "building_not_found"}

    if building.is_producing:
        return {"ok": False, "error": "already_producing"}

    prod_time = calc_production_time(building.type.value, building.level)
    now = datetime.utcnow()

    building.is_producing = True
    building.production_started = now
    building.production_ends = now + timedelta(seconds=prod_time)
    await session.commit()

    return {
        "ok": True,
        "production_ends": building.production_ends,
        "duration_sec": prod_time,
    }


async def collect_production(
    session: AsyncSession,
    player: Player,
    building_id: int,
) -> dict:
    """Собрать готовую продукцию."""
    building = None
    for b in player.buildings:
        if b.id == building_id:
            building = b
            break

    if not building:
        return {"ok": False, "error": "building_not_found"}

    if not building.is_producing:
        return {"ok": False, "error": "not_producing"}

    now = datetime.utcnow()
    if building.production_ends and now < building.production_ends:
        remaining = int((building.production_ends - now).total_seconds())
        return {"ok": False, "error": "not_ready", "remaining_sec": remaining}

    # Начислить доход
    income = calc_farm_income(building.type.value, building.level, player.archetype.value)
    player.coins += income

    # Начислить ресурс в инвентарь
    resource_key = BUILDING_RESOURCE_MAP.get(building.type.value)
    resource_qty = 0
    if resource_key:
        resource_qty = max(1, building.level)  # Больше ресурсов с уровнем
        await add_resource(session, player.id, resource_key, resource_qty)

    # Обновить пассивный доход (пересчёт)
    player.passive_income = _calc_total_passive_income(player)

    building.is_producing = False
    building.production_started = None
    building.production_ends = None
    building.last_collected = now
    await session.commit()

    return {
        "ok": True,
        "income": income,
        "total_coins": player.coins,
        "resource": resource_key,
        "resource_qty": resource_qty,
    }


async def upgrade_building(
    session: AsyncSession,
    player: Player,
    building_id: int,
) -> dict:
    """Улучшить здание на 1 уровень."""
    building = None
    for b in player.buildings:
        if b.id == building_id:
            building = b
            break

    if not building:
        return {"ok": False, "error": "building_not_found"}

    if building.is_producing:
        return {"ok": False, "error": "cant_upgrade_while_producing"}

    cost = calc_upgrade_cost(building.type.value, building.level)
    if player.coins < cost:
        return {"ok": False, "error": "not_enough_coins", "cost": cost}

    player.coins -= cost
    building.level += 1

    # Пересчёт пассивного дохода
    player.passive_income = _calc_total_passive_income(player)
    await session.commit()

    return {
        "ok": True,
        "new_level": building.level,
        "cost": cost,
        "new_income": calc_farm_income(building.type.value, building.level, player.archetype.value),
    }


def _calc_total_passive_income(player: Player) -> int:
    """Пересчитать суммарный пассивный доход всех ферм (монет/мин)."""
    total = 0
    for b in player.buildings:
        info = BUILDINGS.get(b.type.value)
        if not info:
            continue
        income = calc_farm_income(b.type.value, b.level, player.archetype.value)
        prod_time = calc_production_time(b.type.value, b.level)
        # Доход в минуту = income / (prod_time / 60)
        if prod_time > 0:
            total += int(income / (prod_time / 60))
    return total


def get_building_info(building: Building, archetype: str) -> dict:
    """Информация о здании для отображения в UI."""
    info = BUILDINGS.get(building.type.value, {})
    income = calc_farm_income(building.type.value, building.level, archetype)
    prod_time = calc_production_time(building.type.value, building.level)
    upgrade_cost = calc_upgrade_cost(building.type.value, building.level)

    now = datetime.utcnow()
    remaining = 0
    if building.is_producing and building.production_ends:
        remaining = max(0, int((building.production_ends - now).total_seconds()))

    return {
        "id": building.id,
        "type": building.type.value,
        "emoji": info.get("emoji", ""),
        "name": info.get("name", ""),
        "level": building.level,
        "income": income,
        "prod_time_sec": prod_time,
        "upgrade_cost": upgrade_cost,
        "is_producing": building.is_producing,
        "remaining_sec": remaining,
        "ready": building.is_producing and remaining == 0,
    }


def get_available_buildings(player: Player) -> list[dict]:
    """Список зданий, доступных для покупки (ещё не куплены, уровень разблокирован)."""
    owned = {b.type.value for b in player.buildings}
    result = []
    for key, info in BUILDINGS.items():
        if key in owned:
            continue
        unlocked = player.level >= info["unlock_level"]
        result.append({
            "key": key,
            "emoji": info["emoji"],
            "name": info["name"],
            "cost": info["cost"],
            "unlock_level": info["unlock_level"],
            "unlocked": unlocked,
            "affordable": unlocked and player.coins >= info["cost"],
            "location": info["location"],
        })
    return result
