"""Хендлер доски заказов: список, детали, выполнение."""

import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from db.database import async_session
from db.repositories.inventory import get_inventory
from db.repositories.player import get_player_by_tg_id
from game.quests import (
    check_and_complete_order,
    format_requirements,
    generate_orders,
    get_active_orders,
)

logger = logging.getLogger(__name__)

router = Router(name="orders")


# ── Хелперы ──────────────────────────────────────────────────────────

def _fmt_time_left(expires_at: datetime) -> str:
    """Форматировать оставшееся время."""
    delta = expires_at - datetime.utcnow()
    total_sec = max(0, int(delta.total_seconds()))
    h, rem = divmod(total_sec, 3600)
    m, _ = divmod(rem, 60)
    return f"{h}ч {m:02d}м"


NPC_CATEGORY_EMOJI = {
    "cinema": "🎬", "games": "🎮", "music": "🎵",
    "sports": "🏟", "tv": "📡",
}


# ── Клавиатуры ────────────────────────────────────────────────────────

def orders_list_keyboard(orders: list) -> InlineKeyboardMarkup:
    """Клавиатура списка заказов."""
    buttons = []
    for o in orders:
        cat_emoji = NPC_CATEGORY_EMOJI.get(o.npc_category, "📋")
        time_left = _fmt_time_left(o.expires_at)
        text = f"{cat_emoji} {o.npc_name} — {time_left}"
        buttons.append([InlineKeyboardButton(
            text=text,
            callback_data=f"order:view:{o.id}",
        )])
    buttons.append([InlineKeyboardButton(text="🔄 Обновить заказы", callback_data="order:refresh")])
    buttons.append([InlineKeyboardButton(text="⬅️ В город", callback_data="city:central")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def order_detail_keyboard(order_id: int, can_complete: bool) -> InlineKeyboardMarkup:
    """Клавиатура деталей заказа."""
    buttons = []
    if can_complete:
        buttons.append([InlineKeyboardButton(
            text="✅ Выполнить заказ",
            callback_data=f"order:complete:{order_id}",
        )])
    else:
        buttons.append([InlineKeyboardButton(
            text="❌ Не хватает ресурсов",
            callback_data="order:noop",
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ К заказам", callback_data="order:list")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Хендлеры ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "order:list")
async def show_orders(callback: CallbackQuery) -> None:
    """Показать доску заказов."""
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
        if not player:
            await callback.answer("❌ Персонаж не найден!", show_alert=True)
            return

        orders = await get_active_orders(session, player.id)

        # Если заказов мало — догенерировать
        if len(orders) < 3:
            new = await generate_orders(session, player)
            orders = await get_active_orders(session, player.id)

    text = (
        f"📋 <b>Доска заказов</b>\n\n"
        f"💰 Монеты: <b>{player.coins:,}</b>\n"
        f"Активных заказов: {len(orders)}/3\n\n"
        "Выполняй заказы от знаменитостей за вьюкоины и опыт!\n"
        "⚡ Бонус +50% за выполнение в первые 30 мин."
    )

    await callback.message.edit_text(text, reply_markup=orders_list_keyboard(orders))
    await callback.answer()


@router.callback_query(F.data.startswith("order:view:"))
async def view_order(callback: CallbackQuery) -> None:
    """Детали конкретного заказа."""
    order_id = int(callback.data.split(":")[2])

    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
        if not player:
            await callback.answer("❌ Персонаж не найден!", show_alert=True)
            return

        orders = await get_active_orders(session, player.id)
        inventory = await get_inventory(session, player.id)

    order = None
    for o in orders:
        if o.id == order_id:
            order = o
            break

    if not order:
        await callback.answer("❌ Заказ не найден или истёк!", show_alert=True)
        return

    # Проверить наличие ресурсов
    can_complete = True
    req_lines = []
    for res, qty in order.requirements.items():
        have = inventory.get(res, 0)
        ok = have >= qty
        if not ok:
            can_complete = False
        mark = "✅" if ok else "❌"
        req_lines.append(f"  {mark} {res}: {have}/{qty}")

    cat_emoji = NPC_CATEGORY_EMOJI.get(order.npc_category, "📋")
    time_left = _fmt_time_left(order.expires_at)

    # Проверка бонуса
    elapsed = (datetime.utcnow() - order.created_at).total_seconds()
    bonus_active = elapsed <= 30 * 60

    text = (
        f"{cat_emoji} <b>Заказ от {order.npc_name}</b>\n"
        f"{'━' * 22}\n"
        f"📝 {order.description}\n\n"
        f"<b>Требуется:</b>\n"
        + "\n".join(req_lines) + "\n\n"
        f"💰 Награда: <b>{order.reward_coins:,}</b> монет\n"
        f"✨ Опыт: <b>{order.reward_xp}</b> XP\n"
    )
    if bonus_active:
        text += f"⚡ Бонус: <b>+{order.bonus_reward_coins:,}</b> (осталось время!)\n"
    text += f"\n⏰ Истекает через: {time_left}"

    await callback.message.edit_text(
        text,
        reply_markup=order_detail_keyboard(order_id, can_complete),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order:complete:"))
async def complete_order(callback: CallbackQuery) -> None:
    """Выполнить заказ."""
    order_id = int(callback.data.split(":")[2])

    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
        if not player:
            await callback.answer("❌ Персонаж не найден!", show_alert=True)
            return

        result = await check_and_complete_order(session, player, order_id)

    if not result["ok"]:
        msgs = {
            "order_not_found": "Заказ не найден!",
            "already_completed": "Уже выполнен!",
            "expired": "Заказ истёк!",
            "not_enough_resources": "Не хватает ресурсов!",
        }
        await callback.answer(f"❌ {msgs.get(result['error'], 'Ошибка')}", show_alert=True)
        return

    # Формируем сообщение об успехе
    text = (
        f"🎉 <b>Заказ выполнен!</b>\n\n"
        f"👤 {result['npc_name']} доволен!\n"
        f"💰 +{result['coins_earned']:,} монет\n"
        f"✨ +{result['xp_earned']} XP\n"
    )
    if result["got_bonus"]:
        text += f"⚡ Бонус за скорость: +{result['bonus_amount']:,} 💰\n"
    if result["leveled_up"]:
        text += f"\n🆙 <b>Новый уровень: {result['new_level']}!</b>"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 К заказам", callback_data="order:list")],
            [InlineKeyboardButton(text="⬅️ В город", callback_data="city:central")],
        ]),
    )
    await callback.answer("🎉 Заказ выполнен!")


@router.callback_query(F.data == "order:refresh")
async def refresh_orders(callback: CallbackQuery) -> None:
    """Обновить / догенерировать заказы."""
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)
        if not player:
            await callback.answer("❌ Персонаж не найден!", show_alert=True)
            return

        new = await generate_orders(session, player)
        orders = await get_active_orders(session, player.id)

    if new:
        await callback.answer(f"📋 Новых заказов: {len(new)}")
    else:
        await callback.answer("Все слоты заняты — выполни текущие заказы")

    text = (
        f"📋 <b>Доска заказов</b>\n\n"
        f"💰 Монеты: <b>{player.coins:,}</b>\n"
        f"Активных заказов: {len(orders)}/3\n\n"
        "Выполняй заказы от знаменитостей за вьюкоины и опыт!\n"
        "⚡ Бонус +50% за выполнение в первые 30 мин."
    )
    await callback.message.edit_text(text, reply_markup=orders_list_keyboard(orders))


@router.callback_query(F.data == "order:noop")
async def noop(callback: CallbackQuery) -> None:
    """Заглушка для неактивных кнопок."""
    await callback.answer("❌ Не хватает ресурсов! Запусти производство на фермах.", show_alert=True)
