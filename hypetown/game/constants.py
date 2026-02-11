"""Все игровые константы и конфигурации HYPETOWN."""

import enum


# ── Перечисления (Enums) ──────────────────────────────────────────────

class Archetype(str, enum.Enum):
    """Архетипы персонажей."""
    DIRECTOR = "director"
    STREAMER = "streamer"
    PRODUCER = "producer"
    MAGNATE = "magnate"
    BLOGGER = "blogger"
    JOURNALIST = "journalist"


class BuildingType(str, enum.Enum):
    """Типы зданий (ферм)."""
    CINEMA_STUDIO = "cinema_studio"
    SERIES_LOT = "series_lot"
    GAME_STUDIO = "game_studio"
    CYBER_ARENA = "cyber_arena"
    RECORDING = "recording"
    CONCERT_HALL = "concert_hall"
    SPORTS_ARENA = "sports_arena"
    TV_STUDIO = "tv_studio"
    PODCAST_STUDIO = "podcast_studio"


class Resource(str, enum.Enum):
    """Типы ресурсов."""
    FILM = "film"
    SERIES = "series"
    GAME = "game"
    STREAM = "stream"
    TRACK = "track"
    CONCERT = "concert"
    MATCH = "match"
    BROADCAST = "broadcast"
    PODCAST = "podcast"


class MatchType(str, enum.Enum):
    """Типы PvP матчей."""
    BATTLE = "battle"
    QUIZ = "quiz"


class GuildRole(str, enum.Enum):
    """Роли в гильдии."""
    LEADER = "leader"
    OFFICER = "officer"
    MEMBER = "member"


class ClickerUpgradeType(str, enum.Enum):
    """Типы апгрейдов кликера."""
    SMARTPHONE = "smartphone"
    CAMERA = "camera"
    LAPTOP = "laptop"
    STUDIO = "studio"
    PRODUCTION = "production"
    MEDIA_CORP = "media_corp"
    VIRAL_ALGO = "viral_algo"
    GOLD_BUTTON = "gold_button"


# ── Архетипы ──────────────────────────────────────────────────────────

ARCHETYPES: dict[str, dict] = {
    "director":   {"emoji": "\U0001f3ac", "name": "Режиссёр",          "bonus_type": "cinema",  "bonus": 0.15},
    "streamer":   {"emoji": "\U0001f3ae", "name": "Стример",           "bonus_type": "games",   "bonus": 0.15},
    "producer":   {"emoji": "\U0001f3b5", "name": "Продюсер",          "bonus_type": "music",   "bonus": 0.15},
    "magnate":    {"emoji": "\U0001f3df", "name": "Спортивный магнат", "bonus_type": "sports",  "bonus": 0.15},
    "blogger":    {"emoji": "\U0001f4f1", "name": "Блогер",            "bonus_type": "clicker", "bonus": 0.20},
    "journalist": {"emoji": "\U0001f4f0", "name": "Журналист",         "bonus_type": "orders",  "bonus": 0.15},
}


# ── Апгрейды кликера ─────────────────────────────────────────────────

CLICKER_UPGRADES: dict[str, dict] = {
    "smartphone":  {"tap_bonus": 1,   "base_cost": 50,      "cost_mult": 1.5, "max_level": 50},
    "camera":      {"tap_bonus": 3,   "base_cost": 200,     "cost_mult": 1.6, "max_level": 40},
    "laptop":      {"tap_bonus": 10,  "base_cost": 1000,    "cost_mult": 1.7, "max_level": 30},
    "studio":      {"tap_bonus": 30,  "base_cost": 5000,    "cost_mult": 1.8, "max_level": 25},
    "production":  {"tap_bonus": 100, "base_cost": 25000,   "cost_mult": 1.9, "max_level": 20},
    "media_corp":  {"tap_bonus": 500, "base_cost": 200000,  "cost_mult": 2.0, "max_level": 15},
    "viral_algo":  {"multiplier": 2,  "base_cost": 100000,  "cost_mult": 3.0, "max_level": 5},
    "gold_button": {"multiplier": 1.5, "base_cost": 500000, "cost_mult": 4.0, "max_level": 3},
}


# ── Здания (фермы) ───────────────────────────────────────────────────

BUILDINGS: dict[str, dict] = {
    "cinema_studio":  {"location": "hollywood",    "emoji": "\U0001f3ac", "name": "Киностудия",     "base_time": 1800, "base_income": 500,  "cost": 2000,  "unlock_level": 1},
    "series_lot":     {"location": "hollywood",    "emoji": "\U0001f4fa", "name": "Сериальный лот",  "base_time": 900,  "base_income": 200,  "cost": 1000,  "unlock_level": 1},
    "game_studio":    {"location": "gamer_street", "emoji": "\U0001f3ae", "name": "Игровая студия",  "base_time": 3600, "base_income": 1200, "cost": 5000,  "unlock_level": 3},
    "cyber_arena":    {"location": "gamer_street", "emoji": "\U0001f579", "name": "Кибер-арена",     "base_time": 1200, "base_income": 350,  "cost": 3000,  "unlock_level": 3},
    "recording":      {"location": "music_hall",   "emoji": "\U0001f3b5", "name": "Звукозапись",     "base_time": 600,  "base_income": 150,  "cost": 800,   "unlock_level": 5},
    "concert_hall":   {"location": "music_hall",   "emoji": "\U0001f3a4", "name": "Концертный зал",  "base_time": 2700, "base_income": 800,  "cost": 4000,  "unlock_level": 5},
    "sports_arena":   {"location": "sports",       "emoji": "\U0001f3df", "name": "Спорт-арена",     "base_time": 1800, "base_income": 600,  "cost": 3500,  "unlock_level": 7},
    "tv_studio":      {"location": "media_tower",  "emoji": "\U0001f4e1", "name": "ТВ-студия",       "base_time": 1500, "base_income": 450,  "cost": 2500,  "unlock_level": 10},
    "podcast_studio": {"location": "media_tower",  "emoji": "\U0001f399", "name": "Подкаст-студия",  "base_time": 600,  "base_income": 120,  "cost": 600,   "unlock_level": 10},
}


# ── Локации города ────────────────────────────────────────────────────

CITY_LOCATIONS: dict[str, dict] = {
    "central":      {"emoji": "\U0001f3d9", "name": "Центральная площадь", "unlock_level": 1},
    "hollywood":    {"emoji": "\U0001f3ac", "name": "Голливуд",            "unlock_level": 1},
    "gamer_street": {"emoji": "\U0001f3ae", "name": "Геймер-стрит",        "unlock_level": 3},
    "music_hall":   {"emoji": "\U0001f3b5", "name": "Мьюзик-холл",         "unlock_level": 5},
    "sports":       {"emoji": "\U0001f3df", "name": "Спорт-квартал",       "unlock_level": 7},
    "media_tower":  {"emoji": "\U0001f4e1", "name": "Медиа-башня",         "unlock_level": 10},
    "market":       {"emoji": "\U0001f6d2", "name": "Рынок",               "unlock_level": 4},
    "orders":       {"emoji": "\U0001f4cb", "name": "Доска заказов",       "unlock_level": 2},
    "pvp_arena":    {"emoji": "\u2694\ufe0f",  "name": "Арена PvP",        "unlock_level": 6},
    "vip_club":     {"emoji": "\U0001f451", "name": "VIP-клуб",            "unlock_level": 1},
}


# ── NPC-знаменитости ─────────────────────────────────────────────────

NPCS: dict[str, list[dict]] = {
    "cinema": [
        {"name": "Кристофер Нолан", "emoji": "\U0001f3ac"},
        {"name": "Стивен Спилберг", "emoji": "\U0001f3a5"},
        {"name": "Квентин Тарантино", "emoji": "\U0001f39e"},
    ],
    "games": [
        {"name": "Хидео Кодзима", "emoji": "\U0001f3ae"},
        {"name": "Тодд Говард", "emoji": "\U0001f579"},
    ],
    "music": [
        {"name": "Drake", "emoji": "\U0001f3a4"},
        {"name": "Taylor Swift", "emoji": "\U0001f3b5"},
        {"name": "The Weeknd", "emoji": "\U0001f3a7"},
    ],
    "sports": [
        {"name": "LeBron James", "emoji": "\U0001f3c0"},
        {"name": "Lionel Messi", "emoji": "\u26bd"},
    ],
    "tv": [
        {"name": "Шонда Раймс", "emoji": "\U0001f4fa"},
        {"name": "Райан Мёрфи", "emoji": "\U0001f4e1"},
    ],
}


# ── Стартовые параметры ──────────────────────────────────────────────

START_COINS: int = 100
START_TAP_POWER: int = 1
BASE_XP_PER_LEVEL: int = 100
XP_LEVEL_EXPONENT: float = 1.5
PVP_BASE_RATING: int = 1000
PVP_K_FACTOR: int = 32
