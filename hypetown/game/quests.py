"""Бизнес-логика заказов: генерация, NPC, проверка выполнения."""

import random
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Inventory, Order, Player
from game.constants import ARCHETYPES, NPCS, Resource


# ── Шаблоны заказов по категориям ─────────────────────────────────────

ORDER_TEMPLATES: dict[str, list[dict]] = {
    "cinema": [
        {"desc": "Снять блокбастер для проката",             "resources": {"film": (1, 3)},    "base_coins": 800,  "base_xp": 50},
        {"desc": "Сделать сериал для стриминга",             "resources": {"series": (2, 5)},  "base_coins": 600,  "base_xp": 40},
        {"desc": "Организовать кинопремьеру",                "resources": {"film": (1, 2), "concert": (1, 1)}, "base_coins": 1200, "base_xp": 80},
    ],
    "games": [
        {"desc": "Разработать инди-игру",                    "resources": {"game": (1, 2)},    "base_coins": 1000, "base_xp": 60},
        {"desc": "Провести киберспортивный турнир",          "resources": {"stream": (2, 4)},  "base_coins": 700,  "base_xp": 45},
        {"desc": "Выпустить DLC для хита",                   "resources": {"game": (1, 1), "stream": (1, 2)}, "base_coins": 1500, "base_xp": 90},
    ],
    "music": [
        {"desc": "Записать новый альбом",                    "resources": {"track": (2, 5)},   "base_coins": 500,  "base_xp": 35},
        {"desc": "Организовать мировой тур",                 "resources": {"concert": (1, 3)}, "base_coins": 900,  "base_xp": 55},
        {"desc": "Снять клип и выложить на ютуб",            "resources": {"track": (1, 2), "film": (1, 1)}, "base_coins": 1100, "base_xp": 70},
    ],
    "sports": [
        {"desc": "Провести чемпионат",                       "resources": {"match": (2, 4)},   "base_coins": 1000, "base_xp": 60},
        {"desc": "Организовать трансляцию матча",            "resources": {"match": (1, 2), "broadcast": (1, 2)}, "base_coins": 1300, "base_xp": 75},
    ],
    "tv": [
        {"desc": "Запустить новое шоу",                      "resources": {"broadcast": (2, 4)}, "base_coins": 800,  "base_xp": 50},
        {"desc": "Записать серию подкастов",                 "resources": {"podcast": (2, 5)},  "base_coins": 400,  "base_xp": 30},
        {"desc": "Организовать прямой эфир",                 "resources": {"broadcast": (1, 2), "podcast": (1, 2)}, "base_coins": 1100, "base_xp": 65},
    ],
}

# Сколько одновременно активных заказов
MAX_ACTIVE_ORDERS = 3
ORDER_DURATION_HOURS = 4
BONUS_WINDOW_MINUTES = 30  # Бонус за быстрое выполнение


def _pick_npc(category: str) -> dict:
    """Выбрать случайного NPC из категории."""
    npcs = NPCS.get(category, [])
    if not npcs:
        return {"name": "Неизвестный", "emoji": "❓"}
    return random.choice(npcs)


def _scale_order(template: dict, player_level: int) -> dict:
    """Масштабировать заказ под уровень игрока."""
    level_mult = 1.0 + (player_level - 1) * 0.1  # +10% за уровень

    requirements = {}
    for res, (lo, hi) in template["resources"].items():
        qty = random.randint(lo, hi)
        # Масштабирование количества для высоких уровней
        qty = max(1, int(qty * (1 + (player_level - 1) * 0.05)))
        requirements[res] = qty

    coins = int(template["base_coins"] * level_mult)
    xp = int(template["base_xp"] * level_mult)
    bonus_coins = int(coins * 0.5)  # +50% за быстрое выполнение

    return {
        "requirements": requirements,
        "reward_coins": coins,
        "reward_xp": xp,
        "bonus_reward_coins": bonus_coins,
    }


async def generate_orders(
    session: AsyncSession,
    player: Player,
) -> list[Order]:
    """Сгенерировать новые заказы для игрока (до MAX_ACTIVE_ORDERS).

    Возвращает список новых заказов.
    """
    # Подсчёт текущих активных
    result = await session.execute(
        select(Order).where(
            Order.player_id == player.id,
            Order.completed_at.is_(None),
            Order.expires_at > datetime.utcnow(),
        )
    )
    active = list(result.scalars().all())

    slots = MAX_ACTIVE_ORDERS - len(active)
    if slots <= 0:
        return []

    # Бонус архетипа «Журналист» — больше наград
    arch = ARCHETYPES.get(player.archetype.value, {})
    journalist_bonus = arch.get("bonus_type") == "orders"

    new_orders = []
    categories = list(ORDER_TEMPLATES.keys())

    for _ in range(slots):
        category = random.choice(categories)
        template = random.choice(ORDER_TEMPLATES[category])
        npc = _pick_npc(category)
        scaled = _scale_order(template, player.level)

        # Бонус журналиста: +15% к наградам
        if journalist_bonus:
            scaled["reward_coins"] = int(scaled["reward_coins"] * (1 + arch["bonus"]))
            scaled["reward_xp"] = int(scaled["reward_xp"] * (1 + arch["bonus"]))

        now = datetime.utcnow()
        order = Order(
            player_id=player.id,
            npc_name=npc["name"],
            npc_category=category,
            description=template["desc"],
            requirements=scaled["requirements"],
            reward_coins=scaled["reward_coins"],
            reward_xp=scaled["reward_xp"],
            bonus_reward_coins=scaled["bonus_reward_coins"],
            expires_at=now + timedelta(hours=ORDER_DURATION_HOURS),
        )
        session.add(order)
        new_orders.append(order)

    await session.commit()
    return new_orders


async def get_active_orders(session: AsyncSession, player_id: int) -> list[Order]:
    """Получить все активные (не выполненные, не истёкшие) заказы."""
    result = await session.execute(
        select(Order).where(
            Order.player_id == player_id,
            Order.completed_at.is_(None),
            Order.expires_at > datetime.utcnow(),
        ).order_by(Order.expires_at)
    )
    return list(result.scalars().all())


async def check_and_complete_order(
    session: AsyncSession,
    player: Player,
    order_id: int,
) -> dict:
    """Проверить выполнение заказа и выдать награду.

    Возвращает: {"ok": bool, "error"?: str, ...reward_info}
    """
    # Найти заказ
    result = await session.execute(
        select(Order).where(Order.id == order_id, Order.player_id == player.id)
    )
    order = result.scalar_one_or_none()

    if not order:
        return {"ok": False, "error": "order_not_found"}

    if order.completed_at:
        return {"ok": False, "error": "already_completed"}

    now = datetime.utcnow()
    if order.expires_at < now:
        return {"ok": False, "error": "expired"}

    # Проверить ресурсы в инвентаре
    inv_result = await session.execute(
        select(Inventory).where(Inventory.player_id == player.id)
    )
    inventory = {inv.resource.value: inv for inv in inv_result.scalars().all()}

    missing = {}
    for res_key, qty_needed in order.requirements.items():
        inv_item = inventory.get(res_key)
        have = inv_item.quantity if inv_item else 0
        if have < qty_needed:
            missing[res_key] = qty_needed - have

    if missing:
        return {"ok": False, "error": "not_enough_resources", "missing": missing}

    # Списать ресурсы
    for res_key, qty_needed in order.requirements.items():
        inventory[res_key].quantity -= qty_needed

    # Начислить награду
    total_coins = order.reward_coins

    # Бонус за быстрое выполнение (в первые 30 мин)
    elapsed = (now - order.created_at).total_seconds()
    got_bonus = elapsed <= BONUS_WINDOW_MINUTES * 60
    if got_bonus:
        total_coins += order.bonus_reward_coins

    player.coins += total_coins
    player.xp += order.reward_xp

    # Проверка левелапа
    from game.economy import xp_for_level
    leveled_up = False
    while player.xp >= xp_for_level(player.level + 1):
        player.level += 1
        leveled_up = True

    order.completed_at = now
    await session.commit()

    return {
        "ok": True,
        "coins_earned": total_coins,
        "xp_earned": order.reward_xp,
        "got_bonus": got_bonus,
        "bonus_amount": order.bonus_reward_coins if got_bonus else 0,
        "leveled_up": leveled_up,
        "new_level": player.level if leveled_up else None,
        "npc_name": order.npc_name,
    }


def format_requirements(requirements: dict) -> str:
    """Отформатировать требования заказа для UI."""
    RESOURCE_NAMES = {
        "film": "🎬 Фильм",
        "series": "📺 Сериал",
        "game": "🎮 Игра",
        "stream": "🕹 Стрим",
        "track": "🎵 Трек",
        "concert": "🎤 Концерт",
        "match": "🏟 Матч",
        "broadcast": "📡 Эфир",
        "podcast": "🎙 Подкаст",
    }
    lines = []
    for res, qty in requirements.items():
        name = RESOURCE_NAMES.get(res, res)
        lines.append(f"  {name} x{qty}")
    return "\n".join(lines)
