"""Хендлер профиля игрока: /profile и callback."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import profile_keyboard
from db.database import async_session
from db.repositories.player import get_player_by_tg_id
from game.constants import ARCHETYPES

logger = logging.getLogger(__name__)

router = Router(name="profile")


def format_profile(player) -> str:
    """Форматирование текста профиля."""
    arch = ARCHETYPES.get(player.archetype.value, {})
    return (
        f"{player.avatar} <b>{player.name}</b>\n"
        f"{'━' * 20}\n"
        f"🎯 Архетип: {arch.get('emoji', '')} {arch.get('name', '')}\n"
        f"⭐ Уровень: {player.level}\n"
        f"✨ Опыт: {player.xp:,}\n"
        f"💰 Вьюкоины: {player.coins:,}\n"
        f"⭐ Звёзды: {player.stars}\n"
        f"{'━' * 20}\n"
        f"👆 Сила тапа: {player.tap_power}\n"
        f"💸 Пассивный доход: {player.passive_income}/мин\n"
        f"⚔️ PvP рейтинг: {player.pvp_rating}\n"
        f"🔄 Престиж: {player.prestige}\n"
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message) -> None:
    """Команда /profile — показать профиль."""
    async with async_session() as session:
        player = await get_player_by_tg_id(session, message.from_user.id)

    if not player:
        await message.answer("❌ Сначала создай персонажа: /start")
        return

    await message.answer(
        format_profile(player),
        reply_markup=profile_keyboard(),
    )


@router.callback_query(F.data == "profile:main")
async def show_profile(callback: CallbackQuery) -> None:
    """Показать профиль через callback."""
    async with async_session() as session:
        player = await get_player_by_tg_id(session, callback.from_user.id)

    if not player:
        await callback.answer("❌ Персонаж не найден!", show_alert=True)
        return

    await callback.message.edit_text(
        format_profile(player),
        reply_markup=profile_keyboard(),
    )
    await callback.answer()
