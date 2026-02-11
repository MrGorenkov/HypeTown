"""Хендлер /start и онбординг: создание персонажа (имя → аватар → архетип)."""

import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import archetype_keyboard, avatar_keyboard, city_keyboard
from bot.states.onboarding import OnboardingStates
from db.database import async_session
from db.repositories.player import create_player, get_player_by_tg_id
from game.constants import ARCHETYPES, Archetype

logger = logging.getLogger(__name__)

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработка /start — проверка существующего игрока или начало онбординга."""
    async with async_session() as session:
        player = await get_player_by_tg_id(session, message.from_user.id)

    if player:
        # Игрок уже есть — показываем город
        arch = ARCHETYPES.get(player.archetype.value, {})
        await message.answer(
            f"С возвращением, {player.avatar} <b>{player.name}</b>!\n"
            f"Архетип: {arch.get('emoji', '')} {arch.get('name', '')}\n"
            f"Уровень: {player.level} | Монеты: {player.coins:,}\n\n"
            "🏙 <b>Добро пожаловать в HYPETOWN!</b>",
            reply_markup=city_keyboard(player.level),
        )
        return

    # Новый игрок — начинаем онбординг
    await state.set_state(OnboardingStates.waiting_for_name)
    await message.answer(
        "🎬 <b>Добро пожаловать в HYPETOWN!</b>\n\n"
        "Ты попал в город, где рождаются медиа-империи.\n"
        "Создай своего персонажа и начни путь к славе!\n\n"
        "📝 <b>Шаг 1/3:</b> Введи имя персонажа (до 32 символов):"
    )


@router.message(OnboardingStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext) -> None:
    """Обработка ввода имени персонажа."""
    name = message.text.strip()

    if not name or len(name) > 32:
        await message.answer(
            "❌ Имя должно быть от 1 до 32 символов. Попробуй ещё раз:"
        )
        return

    if len(name) < 2:
        await message.answer(
            "❌ Слишком короткое имя. Минимум 2 символа:"
        )
        return

    await state.update_data(name=name)
    await state.set_state(OnboardingStates.waiting_for_avatar)
    await message.answer(
        f"✅ Отличное имя, <b>{name}</b>!\n\n"
        "🎭 <b>Шаг 2/3:</b> Выбери аватар:",
        reply_markup=avatar_keyboard(),
    )


@router.callback_query(OnboardingStates.waiting_for_avatar, F.data.startswith("avatar:"))
async def process_avatar(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора аватара."""
    avatar = callback.data.split(":", 1)[1]
    await state.update_data(avatar=avatar)
    await state.set_state(OnboardingStates.waiting_for_archetype)
    await callback.message.edit_text(
        f"✅ Аватар: {avatar}\n\n"
        "🎯 <b>Шаг 3/3:</b> Выбери свой архетип:\n\n"
        "Каждый архетип даёт бонус к определённой сфере.\n"
        "Выбирай с умом — это определит твой стиль игры!",
        reply_markup=archetype_keyboard(),
    )
    await callback.answer()


@router.callback_query(OnboardingStates.waiting_for_archetype, F.data.startswith("archetype:"))
async def process_archetype(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора архетипа — создание персонажа."""
    archetype_key = callback.data.split(":", 1)[1]

    if archetype_key not in ARCHETYPES:
        await callback.answer("❌ Неизвестный архетип!", show_alert=True)
        return

    data = await state.get_data()
    arch_data = ARCHETYPES[archetype_key]

    async with async_session() as session:
        player = await create_player(
            session=session,
            tg_id=callback.from_user.id,
            username=callback.from_user.username,
            name=data["name"],
            avatar=data["avatar"],
            archetype=Archetype(archetype_key),
        )

    await state.clear()

    await callback.message.edit_text(
        f"🎉 <b>Персонаж создан!</b>\n\n"
        f"{player.avatar} <b>{player.name}</b>\n"
        f"Архетип: {arch_data['emoji']} {arch_data['name']}\n"
        f"Бонус: +{int(arch_data['bonus'] * 100)}% к {arch_data['bonus_type']}\n"
        f"Монеты: {player.coins:,} 💰\n\n"
        "🏙 <b>Добро пожаловать в HYPETOWN!</b>\n"
        "Исследуй город и начни строить свою медиаимперию!",
        reply_markup=city_keyboard(player.level),
    )
    await callback.answer("🎉 Добро пожаловать!")
    logger.info("Новый игрок: %s (@%s), архетип: %s", player.name, player.username, archetype_key)
