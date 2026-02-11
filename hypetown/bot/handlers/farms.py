"""Хендлер ферм: список зданий, запуск/сбор производства, апгрейд."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from db.database import async_session
from db.repositories.player import get_player_by_tg_id
from game.farms import (
    buy_building,
    collect_production,
    get_available_buildings,
    get_building_info,
    start_production,
    upgrade_building,
)

logger = logging.getLogger(__name__)

router = Router(name="farms")


# ── Форматирование ───────────────────────────────────────────────────

def _fmt_time(seconds: int) -> str:
    """Форматировать секунды в ЧЧ:ММ:СС или ММ:СС."""
    if seconds >= 3600:
        h, m = divmod(seconds, 3600)
        m, s = divmod(m, 60)
        return f"{h}ч {m:02d}м"
    m, s = divmod(seconds, 60)
    return f"{m}м {s:02d}с"


# ── Клавиатуры ────────────────────────────────────────────────────────

def buildings_list_keyboard(buildings_info: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура списка зданий игрока."""
    buttons = []
    for b in buildings_info:
        if b["ready"]:
            status = "✅ ГОТОВО"
        elif b["is_producing"]:
            status = f"⏳ {_fmt_time(b['remaining_sec'])}"
        else:
            status = "💤 Простаивает"
        text = f"{b['emoji']} {b['name']} ур.{b['level']} — {status}"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"farm:view:{b['id']}",
        )])
    buttons.append([InlineKeyboardButton(text="🏗 Купить здание", callback_data="farm:shop")])
    buttons.append([InlineKeyboardButton(text="⬅️ В город", callback_data="city:central")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def building_detail_keyboard(b: dict) -> InlineKeyboardMarkup:
    """Клавиатура конкретного здания."""
    buttons = []
    if b["ready"]:
        buttons.append([InlineKeyboardButton(
            text=f"📦 Собрать (+{b['income']:,} 💰)",
            callback_data=f"farm:collect:{b['id']}",
        )])
    elif not b["is_producing"]:
        buttons.append([InlineKeyboardButton(
            text=f"▶️ Запустить ({_fmt_time(b['prod_time_sec'])})",
            callback_data=f"farm:start:{b['id']}",
        )])
    if not b["is_producing"]:
        buttons.append([InlineKeyboardButton(
            text=f"⬆️ Улучшить ({b['upgrade_cost']:,} 💰)",
            callback_data=f"farm:upgrade:{b['id']}",
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Мои здания", callback_data="farm:list")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def shop_keyboard(available: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура магазина зданий."""
    buttons = []
    for b in available:
        if not b["unlocked"]:
            text = f"🔒 {b['name']} (ур. {b['unlock_level']})"
        elif b["affordable"]:
            text = f"💰 {b['emoji']} {b['name']} — {b['cost']:,}"
        else:
            text = f"🔒 {b['emoji']} {b['name']} — {b['cost']:,}"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"farm:buy:{b['key']}",
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Мои здания", callback_data="farm:list")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Хендлеры ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "farm:list")
async def show_buildings(callback: CallbackQuery) -> None:
    """Показать список зданий игрока."""
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)

    if not player:
        await callback.answer("❌ Персонаж не найден!", show_alert=True)
        return

    buildings_info = [get_building_info(b, player.archetype.value) for b in player.buildings]

    if not buildings_info:
        text = (
            "🏗 <b>Твои здания</b>\n\n"
            "У тебя пока нет зданий.\n"
            "Купи первое здание, чтобы начать производство!"
        )
    else:
        text = f"🏗 <b>Твои здания</b> ({len(buildings_info)})\n"
        text += f"💰 Монеты: <b>{player.coins:,}</b>\n"
        text += f"💸 Пассивный доход: {player.passive_income}/мин\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=buildings_list_keyboard(buildings_info),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("farm:view:"))
async def view_building(callback: CallbackQuery) -> None:
    """Детали конкретного здания."""
    building_id = int(callback.data.split(":")[2])

    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)

    if not player:
        await callback.answer("❌ Персонаж не найден!", show_alert=True)
        return

    building = None
    for b in player.buildings:
        if b.id == building_id:
            building = b
            break

    if not building:
        await callback.answer("❌ Здание не найдено!", show_alert=True)
        return

    info = get_building_info(building, player.archetype.value)
    status = "✅ Готово к сбору!" if info["ready"] else (
        f"⏳ Производство: {_fmt_time(info['remaining_sec'])}" if info["is_producing"]
        else "💤 Простаивает"
    )

    text = (
        f"{info['emoji']} <b>{info['name']}</b> (ур. {info['level']})\n"
        f"{'━' * 20}\n"
        f"💰 Доход: {info['income']:,} за цикл\n"
        f"⏱ Время: {_fmt_time(info['prod_time_sec'])}\n"
        f"⬆️ Апгрейд: {info['upgrade_cost']:,} 💰\n"
        f"{'━' * 20}\n"
        f"Статус: {status}\n"
    )

    await callback.message.edit_text(text, reply_markup=building_detail_keyboard(info))
    await callback.answer()


@router.callback_query(F.data.startswith("farm:start:"))
async def handle_start_production(callback: CallbackQuery) -> None:
    """Запустить производство."""
    building_id = int(callback.data.split(":")[2])

    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
        if not player:
            await callback.answer("❌ Персонаж не найден!", show_alert=True)
            return
        result = await start_production(session, player, building_id)

    if not result["ok"]:
        msgs = {
            "building_not_found": "Здание не найдено!",
            "already_producing": "Уже производит!",
        }
        await callback.answer(f"❌ {msgs.get(result['error'], 'Ошибка')}", show_alert=True)
        return

    await callback.answer(f"▶️ Производство запущено! Готово через {_fmt_time(result['duration_sec'])}")

    # Обновить вид здания
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
    for b in player.buildings:
        if b.id == building_id:
            info = get_building_info(b, player.archetype.value)
            text = (
                f"{info['emoji']} <b>{info['name']}</b> (ур. {info['level']})\n"
                f"{'━' * 20}\n"
                f"⏳ Производство: {_fmt_time(info['remaining_sec'])}\n"
            )
            await callback.message.edit_text(text, reply_markup=building_detail_keyboard(info))
            break


@router.callback_query(F.data.startswith("farm:collect:"))
async def handle_collect(callback: CallbackQuery) -> None:
    """Собрать продукцию."""
    building_id = int(callback.data.split(":")[2])

    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
        if not player:
            await callback.answer("❌ Персонаж не найден!", show_alert=True)
            return
        result = await collect_production(session, player, building_id)

    if not result["ok"]:
        msgs = {
            "building_not_found": "Здание не найдено!",
            "not_producing": "Ничего не производится!",
            "not_ready": f"Ещё не готово! Осталось: {_fmt_time(result.get('remaining_sec', 0))}",
        }
        await callback.answer(f"❌ {msgs.get(result['error'], 'Ошибка')}", show_alert=True)
        return

    res_text = ""
    if result.get("resource") and result.get("resource_qty"):
        res_text = f" + {result['resource_qty']}x {result['resource']}"
    await callback.answer(
        f"📦 +{result['income']:,} 💰{res_text} | Всего: {result['total_coins']:,}",
        show_alert=True,
    )

    # Вернуться к списку зданий
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
    buildings_info = [get_building_info(b, player.archetype.value) for b in player.buildings]
    text = f"🏗 <b>Твои здания</b> ({len(buildings_info)})\n"
    text += f"💰 Монеты: <b>{player.coins:,}</b>\n"
    text += f"💸 Пассивный доход: {player.passive_income}/мин\n"
    await callback.message.edit_text(text, reply_markup=buildings_list_keyboard(buildings_info))


@router.callback_query(F.data.startswith("farm:upgrade:"))
async def handle_upgrade(callback: CallbackQuery) -> None:
    """Улучшить здание."""
    building_id = int(callback.data.split(":")[2])

    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
        if not player:
            await callback.answer("❌ Персонаж не найден!", show_alert=True)
            return
        result = await upgrade_building(session, player, building_id)

    if not result["ok"]:
        msgs = {
            "building_not_found": "Здание не найдено!",
            "cant_upgrade_while_producing": "Нельзя улучшать во время производства!",
            "not_enough_coins": f"Не хватает монет! Нужно: {result.get('cost', 0):,}",
        }
        await callback.answer(f"❌ {msgs.get(result['error'], 'Ошибка')}", show_alert=True)
        return

    await callback.answer(
        f"⬆️ Улучшено до ур. {result['new_level']}! Доход: {result['new_income']:,}",
        show_alert=True,
    )

    # Обновить вид
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
    for b in player.buildings:
        if b.id == building_id:
            info = get_building_info(b, player.archetype.value)
            text = (
                f"{info['emoji']} <b>{info['name']}</b> (ур. {info['level']})\n"
                f"{'━' * 20}\n"
                f"💰 Доход: {info['income']:,} за цикл\n"
                f"⏱ Время: {_fmt_time(info['prod_time_sec'])}\n"
                f"⬆️ Апгрейд: {info['upgrade_cost']:,} 💰\n"
                f"{'━' * 20}\n"
                f"Статус: 💤 Простаивает\n"
            )
            await callback.message.edit_text(text, reply_markup=building_detail_keyboard(info))
            break


@router.callback_query(F.data == "farm:shop")
async def show_shop(callback: CallbackQuery) -> None:
    """Магазин зданий."""
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)

    if not player:
        await callback.answer("❌ Персонаж не найден!", show_alert=True)
        return

    available = get_available_buildings(player)
    text = (
        f"🏗 <b>Магазин зданий</b>\n\n"
        f"💰 Монеты: <b>{player.coins:,}</b>\n"
        f"⭐ Уровень: {player.level}\n\n"
    )
    if not available:
        text += "Все здания уже куплены! 🎉"

    await callback.message.edit_text(text, reply_markup=shop_keyboard(available))
    await callback.answer()


@router.callback_query(F.data.startswith("farm:buy:"))
async def handle_buy_building(callback: CallbackQuery) -> None:
    """Купить здание."""
    building_type = callback.data.split(":", 2)[2]

    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
        if not player:
            await callback.answer("❌ Персонаж не найден!", show_alert=True)
            return
        result = await buy_building(session, player, building_type)

    if not result["ok"]:
        msgs = {
            "unknown_building": "Неизвестное здание!",
            "level_locked": f"Нужен уровень {result.get('required_level', '?')}!",
            "already_owned": "Уже куплено!",
            "not_enough_coins": f"Не хватает монет! Нужно: {result.get('cost', 0):,}",
        }
        await callback.answer(f"❌ {msgs.get(result['error'], 'Ошибка')}", show_alert=True)
        return

    await callback.answer(f"🏗 Здание куплено за {result['cost']:,} 💰!", show_alert=True)

    # Показать список зданий
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
    buildings_info = [get_building_info(b, player.archetype.value) for b in player.buildings]
    text = f"🏗 <b>Твои здания</b> ({len(buildings_info)})\n"
    text += f"💰 Монеты: <b>{player.coins:,}</b>\n"
    text += f"💸 Пассивный доход: {player.passive_income}/мин\n"
    await callback.message.edit_text(text, reply_markup=buildings_list_keyboard(buildings_info))
