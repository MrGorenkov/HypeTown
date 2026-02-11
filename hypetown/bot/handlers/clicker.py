"""Хендлер кликера: тап-кнопка, экран апгрейдов, покупка."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from db.database import async_session
from db.repositories.player import get_player_by_tg_id
from game.clicker import buy_upgrade, get_upgrades_info, process_tap
from services.redis_service import add_pending_taps, update_leaderboard

logger = logging.getLogger(__name__)

router = Router(name="clicker")


# ── Клавиатуры ────────────────────────────────────────────────────────

def clicker_main_keyboard() -> InlineKeyboardMarkup:
    """Главный экран кликера."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👆 ТАП!", callback_data="clicker:tap")],
        [InlineKeyboardButton(text="⬆️ Апгрейды", callback_data="clicker:upgrades")],
        [InlineKeyboardButton(text="⬅️ В город", callback_data="city:central")],
    ])


def upgrades_keyboard(upgrades: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура апгрейдов кликера."""
    buttons = []
    for upg in upgrades:
        if upg["maxed"]:
            text = f"✅ {upg['name']} [{upg['level']}/{upg['max_level']}] MAX"
        elif upg["affordable"]:
            text = f"💰 {upg['name']} [{upg['level']}/{upg['max_level']}] — {upg['cost']:,}"
        else:
            text = f"🔒 {upg['name']} [{upg['level']}/{upg['max_level']}] — {upg['cost']:,}"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"clicker:buy:{upg['key']}",
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="clicker:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Хендлеры ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "clicker:main")
async def show_clicker(callback: CallbackQuery) -> None:
    """Показать экран кликера."""
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)

    if not player:
        await callback.answer("❌ Персонаж не найден!", show_alert=True)
        return

    await callback.message.edit_text(
        f"🎮 <b>Кликер</b>\n\n"
        f"💰 Монеты: <b>{player.coins:,}</b>\n"
        f"👆 Сила тапа: <b>{player.tap_power}</b>\n"
        f"⭐ Уровень: {player.level}\n\n"
        "Нажми «ТАП!» чтобы заработать вьюкоины!",
        reply_markup=clicker_main_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "clicker:tap")
async def handle_tap(callback: CallbackQuery) -> None:
    """Обработка тапа из бота."""
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
        if not player:
            await callback.answer("❌ Персонаж не найден!", show_alert=True)
            return

        result = await process_tap(session, player, tap_count=1)

    # Батчинг в Redis + лидерборд
    await add_pending_taps(callback.from_user.id, 1)
    await update_leaderboard(callback.from_user.id, result["total_coins"])

    await callback.message.edit_text(
        f"🎮 <b>Кликер</b>\n\n"
        f"💰 Монеты: <b>{result['total_coins']:,}</b>\n"
        f"👆 Сила тапа: <b>{result['tap_power']}</b>\n"
        f"✨ +{result['earned']:,} за тап!\n\n"
        "Нажми «ТАП!» ещё раз!",
        reply_markup=clicker_main_keyboard(),
    )
    await callback.answer(f"+{result['earned']} 💰")


@router.callback_query(F.data == "clicker:upgrades")
async def show_upgrades(callback: CallbackQuery) -> None:
    """Показать список апгрейдов."""
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)

    if not player:
        await callback.answer("❌ Персонаж не найден!", show_alert=True)
        return

    upgrades = get_upgrades_info(player)

    text = (
        f"⬆️ <b>Апгрейды кликера</b>\n\n"
        f"💰 Монеты: <b>{player.coins:,}</b>\n"
        f"👆 Текущая сила тапа: <b>{player.tap_power}</b>\n\n"
    )
    for upg in upgrades:
        status = "✅ MAX" if upg["maxed"] else f"[{upg['level']}/{upg['max_level']}]"
        text += f"• {upg['name']} {status} — {upg['bonus']}\n"

    await callback.message.edit_text(
        text + "\nВыбери апгрейд для покупки:",
        reply_markup=upgrades_keyboard(upgrades),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("clicker:buy:"))
async def handle_buy_upgrade(callback: CallbackQuery) -> None:
    """Покупка апгрейда."""
    upgrade_key = callback.data.split(":", 2)[2]

    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
        if not player:
            await callback.answer("❌ Персонаж не найден!", show_alert=True)
            return

        result = await buy_upgrade(session, player, upgrade_key)

    if not result["ok"]:
        error_msgs = {
            "unknown_upgrade": "Неизвестный апгрейд!",
            "max_level": "Достигнут максимальный уровень!",
            "not_enough_coins": f"Не хватает монет! Нужно: {result.get('cost', 0):,}",
        }
        await callback.answer(f"❌ {error_msgs.get(result['error'], 'Ошибка')}", show_alert=True)
        return

    await callback.answer(
        f"✅ Апгрейд! Ур. {result['new_level']} | Сила тапа: {result['new_tap_power']}",
        show_alert=True,
    )

    # Обновить экран апгрейдов
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
        upgrades = get_upgrades_info(player)

    text = (
        f"⬆️ <b>Апгрейды кликера</b>\n\n"
        f"💰 Монеты: <b>{player.coins:,}</b>\n"
        f"👆 Текущая сила тапа: <b>{player.tap_power}</b>\n\n"
    )
    for upg in upgrades:
        status = "✅ MAX" if upg["maxed"] else f"[{upg['level']}/{upg['max_level']}]"
        text += f"• {upg['name']} {status} — {upg['bonus']}\n"

    await callback.message.edit_text(
        text + "\nВыбери апгрейд для покупки:",
        reply_markup=upgrades_keyboard(upgrades),
    )
