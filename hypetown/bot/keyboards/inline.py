"""Все InlineKeyboardMarkup для бота HYPETOWN."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from game.constants import ARCHETYPES, CITY_LOCATIONS


# ── Онбординг ─────────────────────────────────────────────────────────

AVATAR_OPTIONS = ["🎬", "🎮", "🎵", "🏟", "📱", "📰", "🎤", "🎧", "⚽", "🎯"]


def avatar_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора аватара (эмодзи)."""
    buttons = []
    row = []
    for emoji in AVATAR_OPTIONS:
        row.append(InlineKeyboardButton(text=emoji, callback_data=f"avatar:{emoji}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def archetype_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора архетипа."""
    buttons = []
    for key, data in ARCHETYPES.items():
        bonus_pct = int(data["bonus"] * 100)
        text = f"{data['emoji']} {data['name']} (+{bonus_pct}% {data['bonus_type']})"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"archetype:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Город (главное меню) ──────────────────────────────────────────────

def city_keyboard(player_level: int) -> InlineKeyboardMarkup:
    """Клавиатура навигации по городу с учётом уровня игрока."""
    buttons = []
    for loc_key, loc_data in CITY_LOCATIONS.items():
        if player_level >= loc_data["unlock_level"]:
            text = f"{loc_data['emoji']} {loc_data['name']}"
        else:
            text = f"🔒 {loc_data['name']} (ур. {loc_data['unlock_level']})"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"city:{loc_key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Профиль ───────────────────────────────────────────────────────────

def profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура профиля игрока."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏙 В город", callback_data="city:central")],
        [InlineKeyboardButton(text="🎮 Кликер", callback_data="clicker:main")],
        [InlineKeyboardButton(text="📊 Лидерборд", callback_data="profile:leaderboard")],
    ])


# ── Общие ─────────────────────────────────────────────────────────────

def back_to_city_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в город."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в город", callback_data="city:central")],
    ])
