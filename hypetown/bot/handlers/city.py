"""Хендлер города: навигация по локациям, главное меню."""

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from db.database import async_session
from db.repositories.player import get_player_by_tg_id
from game.constants import BUILDINGS, CITY_LOCATIONS
from game.farms import get_building_info

logger = logging.getLogger(__name__)

router = Router(name="city")


# ── Клавиатуры ────────────────────────────────────────────────────────

def city_main_keyboard(player_level: int) -> InlineKeyboardMarkup:
    """Главное меню города с доступными локациями."""
    buttons = []

    # Кликер - всегда доступен
    buttons.append([InlineKeyboardButton(text="👆 Кликер", callback_data="clicker:main")])

    for loc_key, loc in CITY_LOCATIONS.items():
        # Пропускаем центральную площадь из списка
        if loc_key == "central":
            continue
        unlocked = player_level >= loc["unlock_level"]
        if unlocked:
            text = f"{loc['emoji']} {loc['name']}"
        else:
            text = f"🔒 {loc['name']} (ур. {loc['unlock_level']})"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"city:{loc_key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def location_keyboard(location_key: str, player_level: int, buildings_info: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура конкретной локации с её зданиями."""
    buttons = []

    # Здания игрока в этой локации
    for b in buildings_info:
        if b["ready"]:
            status = "✅"
        elif b["is_producing"]:
            status = "⏳"
        else:
            status = "💤"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {b['emoji']} {b['name']} ур.{b['level']}",
            callback_data=f"farm:view:{b['id']}",
        )])

    # Доступные для покупки здания в этой локации
    loc_buildings = {k: v for k, v in BUILDINGS.items() if v["location"] == location_key}
    owned_types = {b["type"] for b in buildings_info}
    for key, info in loc_buildings.items():
        if key in owned_types:
            continue
        if player_level >= info["unlock_level"]:
            buttons.append([InlineKeyboardButton(
                text=f"🏗 Купить {info['emoji']} {info['name']} ({info['cost']:,} 💰)",
                callback_data=f"farm:buy:{key}",
            )])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад в город", callback_data="city:central")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Хендлеры ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "city:central")
async def show_city(callback: CallbackQuery) -> None:
    """Центральная площадь — главное меню."""
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)

    if not player:
        await callback.answer("❌ Персонаж не найден!", show_alert=True)
        return

    text = (
        f"🏙 <b>HYPETOWN — Центральная площадь</b>\n\n"
        f"{player.avatar} <b>{player.name}</b> | ⭐ Ур. {player.level}\n"
        f"💰 {player.coins:,} | 💸 {player.passive_income}/мин\n\n"
        "Выбери локацию:"
    )
    try:
        await callback.message.edit_text(text, reply_markup=city_main_keyboard(player.level))
    except TelegramBadRequest:
        # Сообщение не изменилось — игнорируем
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("city:"))
async def open_location(callback: CallbackQuery) -> None:
    """Открыть конкретную локацию."""
    loc_key = callback.data.split(":", 1)[1]

    # central обрабатывается выше
    if loc_key == "central":
        return

    loc = CITY_LOCATIONS.get(loc_key)
    if not loc:
        await callback.answer("❌ Локация не найдена!", show_alert=True)
        return

    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)

    if not player:
        await callback.answer("❌ Персонаж не найден!", show_alert=True)
        return

    if player.level < loc["unlock_level"]:
        await callback.answer(
            f"🔒 Нужен уровень {loc['unlock_level']}! Твой: {player.level}",
            show_alert=True,
        )
        return

    # Доска заказов → делегируем в orders handler
    if loc_key == "orders":
        from bot.handlers.orders import show_orders
        await show_orders(callback)
        return

    # Ещё не реализованные локации → заглушка
    stub_locations = {"market", "pvp_arena", "vip_club"}
    if loc_key in stub_locations:
        await callback.message.edit_text(
            f"{loc['emoji']} <b>{loc['name']}</b>\n\n"
            "🚧 Этот раздел в разработке...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ В город", callback_data="city:central")],
            ]),
        )
        await callback.answer()
        return

    # Локации с зданиями (hollywood, gamer_street, music_hall, sports, media_tower)
    buildings_info = []
    for b in player.buildings:
        bld_data = BUILDINGS.get(b.type.value, {})
        if bld_data.get("location") == loc_key:
            buildings_info.append(get_building_info(b, player.archetype.value))

    text = (
        f"{loc['emoji']} <b>{loc['name']}</b>\n\n"
        f"💰 Монеты: <b>{player.coins:,}</b>\n"
    )

    if buildings_info:
        text += f"🏗 Зданий: {len(buildings_info)}\n"
    else:
        text += "У тебя пока нет зданий в этой локации.\n"

    await callback.message.edit_text(
        text,
        reply_markup=location_keyboard(loc_key, player.level, buildings_info),
    )
    await callback.answer()
