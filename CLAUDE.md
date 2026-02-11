# CLAUDE.md — HYPETOWN: Telegram Bot Game

## Обзор проекта

HYPETOWN — Telegram-бот-игра в жанре idle clicker / tycoon с медиа-тематикой. Игрок создаёт персонажа, исследует город с тематическими локациями (кино, игры, музыка, спорт, ТВ) и строит свою медиаимперию. Ядро геймплея: кликер + фермы (медиа-производства) с реальными таймерами + PvP + торговля.

---

## Стек

- **Python 3.12+**
- **aiogram 3.x** — Telegram Bot API (async, FSM, inline-кнопки, callback_query)
- **PostgreSQL** — основная база данных
- **SQLAlchemy 2.0 (async)** + **Alembic** — ORM и миграции
- **Redis** — кэш кулдаунов, батчинг кликера, лидерборды, сессии
- **APScheduler** — таймеры ферм, обновление заказов, ивенты
- **Docker + Docker Compose** — контейнеризация всех сервисов
- **python-dotenv** — конфигурация через .env

---

## Структура проекта

```
hypetown/
├── bot/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py           # /start, онбординг, создание персонажа
│   │   ├── city.py            # навигация по городу (главное меню)
│   │   ├── clicker.py         # кликер-механика
│   │   ├── farms.py           # фермы: запуск, сбор, апгрейд
│   │   ├── orders.py          # доска заказов от NPC
│   │   ├── market.py          # рынок (торговля между игроками)
│   │   ├── pvp.py             # PvP: баттлы, викторина
│   │   ├── profile.py         # профиль, инвентарь, достижения
│   │   ├── guild.py           # гильдии (медиахолдинги)
│   │   └── shop.py            # VIP-магазин, покупка за Звёзды
│   ├── keyboards/
│   │   ├── __init__.py
│   │   └── inline.py          # все InlineKeyboardMarkup
│   ├── middlewares/
│   │   ├── __init__.py
│   │   ├── antiflood.py       # антифлуд (Rate Limiting)
│   │   ├── auth.py            # проверка/создание игрока в БД
│   │   └── logging.py         # логирование действий
│   ├── states/
│   │   ├── __init__.py
│   │   └── onboarding.py      # FSM для создания персонажа
│   ├── filters/
│   │   ├── __init__.py
│   │   └── custom.py          # кастомные фильтры
│   └── utils/
│       ├── __init__.py
│       ├── notifications.py   # push-уведомления
│       └── helpers.py         # вспомогательные функции
├── game/
│   ├── __init__.py
│   ├── engine.py              # основной игровой движок
│   ├── clicker.py             # логика кликера, апгрейды, формулы
│   ├── farms.py               # логика ферм, таймеры, цепочки крафта
│   ├── market.py              # логика рынка, лоты, аукционы
│   ├── pvp.py                 # PvP: баттлы, викторина, ELO
│   ├── quests.py              # заказы, квесты, NPC
│   ├── guilds.py              # гильдии, мега-заказы
│   ├── progression.py         # уровни, XP, достижения, престиж
│   ├── economy.py             # экономика, баланс, формулы цен
│   └── constants.py           # все игровые константы и конфиги
├── db/
│   ├── __init__.py
│   ├── database.py            # async engine, sessionmaker
│   ├── models.py              # SQLAlchemy модели (все таблицы)
│   └── repositories/
│       ├── __init__.py
│       ├── player.py          # CRUD операции для игроков
│       ├── building.py        # CRUD для зданий
│       ├── inventory.py       # CRUD для инвентаря
│       ├── market.py          # CRUD для рынка
│       └── pvp.py             # CRUD для PvP
├── services/
│   ├── __init__.py
│   ├── redis_service.py       # Redis: кэш, лидерборды, батчинг
│   ├── scheduler.py           # APScheduler: таймеры ферм, обновления
│   └── payment.py             # Telegram Stars: платежи, покупки
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── config.py                  # загрузка .env, настройки
├── main.py                    # точка входа: запуск бота
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## Модели БД (SQLAlchemy)

### players
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | |
| tg_id | BigInteger, unique | Telegram user ID |
| username | String(64), nullable | Telegram username |
| name | String(32) | Имя персонажа |
| avatar | String(8) | Эмодзи-аватар |
| archetype | Enum(Archetype) | Режиссёр/Стример/Продюсер/Магнат/Блогер/Журналист |
| level | Integer, default=1 | |
| xp | BigInteger, default=0 | |
| coins | BigInteger, default=0 | Вьюкоины |
| stars | Integer, default=0 | Премиум-валюта |
| pvp_rating | Integer, default=1000 | ELO рейтинг |
| prestige | Integer, default=0 | Количество престижей |
| tap_power | Integer, default=1 | Текущая сила тапа |
| passive_income | Integer, default=0 | Доход в минуту |
| is_premium | Boolean, default=False | Подписка активна |
| premium_until | DateTime, nullable | |
| created_at | DateTime | |
| last_active | DateTime | |

### buildings
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | |
| player_id | FK → players | |
| type | Enum(BuildingType) | Тип здания |
| level | Integer, default=1 | |
| is_producing | Boolean, default=False | |
| production_started | DateTime, nullable | |
| production_ends | DateTime, nullable | |
| last_collected | DateTime | |

### inventory
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | |
| player_id | FK → players | |
| resource | Enum(Resource) | Тип ресурса |
| quantity | Integer, default=0 | |

### orders
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | |
| player_id | FK → players | |
| npc_name | String(64) | Имя NPC |
| npc_category | String(32) | Категория NPC |
| description | Text | Текст заказа |
| requirements | JSON | {"resource": quantity, ...} |
| reward_coins | Integer | |
| reward_xp | Integer | |
| bonus_reward_coins | Integer | Бонус за быстрое выполнение |
| created_at | DateTime | |
| expires_at | DateTime | |
| completed_at | DateTime, nullable | |

### market_lots
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | |
| seller_id | FK → players | |
| resource | Enum(Resource) | |
| quantity | Integer | |
| price | Integer | Цена за единицу |
| created_at | DateTime | |
| expires_at | DateTime | |
| buyer_id | FK → players, nullable | |
| sold_at | DateTime, nullable | |

### pvp_matches
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | |
| player1_id | FK → players | |
| player2_id | FK → players | |
| match_type | Enum(MatchType) | battle / quiz |
| bet | Integer | Ставка |
| winner_id | FK → players, nullable | |
| rating_change | Integer | |
| created_at | DateTime | |

### guilds
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | |
| name | String(32) | |
| leader_id | FK → players | |
| level | Integer, default=1 | |
| created_at | DateTime | |

### guild_members
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | |
| guild_id | FK → guilds | |
| player_id | FK → players | |
| role | Enum(GuildRole) | leader / officer / member |
| joined_at | DateTime | |

### clicker_upgrades
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | |
| player_id | FK → players | |
| upgrade_type | Enum(ClickerUpgrade) | |
| level | Integer, default=0 | |

### achievements
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | |
| player_id | FK → players | |
| achievement_type | String(64) | |
| unlocked_at | DateTime | |

### daily_quests
| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer, PK | |
| player_id | FK → players | |
| quest_type | String(64) | |
| progress | Integer, default=0 | |
| target | Integer | |
| reward_coins | Integer | |
| reward_xp | Integer | |
| completed | Boolean, default=False | |
| date | Date | |

---

## Игровые константы (game/constants.py)

### Архетипы
```python
ARCHETYPES = {
    "director":  {"emoji": "🎬", "name": "Режиссёр",          "bonus_type": "cinema",  "bonus": 0.15},
    "streamer":  {"emoji": "🎮", "name": "Стример",           "bonus_type": "games",   "bonus": 0.15},
    "producer":  {"emoji": "🎵", "name": "Продюсер",          "bonus_type": "music",   "bonus": 0.15},
    "magnate":   {"emoji": "🏟", "name": "Спортивный магнат", "bonus_type": "sports",  "bonus": 0.15},
    "blogger":   {"emoji": "📱", "name": "Блогер",            "bonus_type": "clicker", "bonus": 0.20},
    "journalist":{"emoji": "📰", "name": "Журналист",         "bonus_type": "orders",  "bonus": 0.15},
}
```

### Апгрейды кликера
```python
CLICKER_UPGRADES = {
    "smartphone":  {"tap_bonus": 1,   "base_cost": 50,      "cost_mult": 1.5, "max_level": 50},
    "camera":      {"tap_bonus": 3,   "base_cost": 200,     "cost_mult": 1.6, "max_level": 40},
    "laptop":      {"tap_bonus": 10,  "base_cost": 1000,    "cost_mult": 1.7, "max_level": 30},
    "studio":      {"tap_bonus": 30,  "base_cost": 5000,    "cost_mult": 1.8, "max_level": 25},
    "production":  {"tap_bonus": 100, "base_cost": 25000,   "cost_mult": 1.9, "max_level": 20},
    "media_corp":  {"tap_bonus": 500, "base_cost": 200000,  "cost_mult": 2.0, "max_level": 15},
    "viral_algo":  {"multiplier": 2,  "base_cost": 100000,  "cost_mult": 3.0, "max_level": 5},
    "gold_button": {"multiplier": 1.5,"base_cost": 500000,  "cost_mult": 4.0, "max_level": 3},
}
```

### Здания (фермы)
```python
BUILDINGS = {
    "cinema_studio":   {"location": "hollywood",     "emoji": "🎬", "name": "Киностудия",      "base_time": 1800, "base_income": 500,  "cost": 2000,  "unlock_level": 1},
    "series_lot":      {"location": "hollywood",     "emoji": "📺", "name": "Сериальный лот",   "base_time": 900,  "base_income": 200,  "cost": 1000,  "unlock_level": 1},
    "game_studio":     {"location": "gamer_street",  "emoji": "🎮", "name": "Игровая студия",   "base_time": 3600, "base_income": 1200, "cost": 5000,  "unlock_level": 3},
    "cyber_arena":     {"location": "gamer_street",  "emoji": "🕹",  "name": "Кибер-арена",     "base_time": 1200, "base_income": 350,  "cost": 3000,  "unlock_level": 3},
    "recording":       {"location": "music_hall",    "emoji": "🎵", "name": "Звукозапись",      "base_time": 600,  "base_income": 150,  "cost": 800,   "unlock_level": 5},
    "concert_hall":    {"location": "music_hall",    "emoji": "🎤", "name": "Концертный зал",   "base_time": 2700, "base_income": 800,  "cost": 4000,  "unlock_level": 5},
    "sports_arena":    {"location": "sports",        "emoji": "🏟", "name": "Спорт-арена",      "base_time": 1800, "base_income": 600,  "cost": 3500,  "unlock_level": 7},
    "tv_studio":       {"location": "media_tower",   "emoji": "📡", "name": "ТВ-студия",        "base_time": 1500, "base_income": 450,  "cost": 2500,  "unlock_level": 10},
    "podcast_studio":  {"location": "media_tower",   "emoji": "🎙", "name": "Подкаст-студия",   "base_time": 600,  "base_income": 120,  "cost": 600,   "unlock_level": 10},
}
```

### Локации города
```python
CITY_LOCATIONS = {
    "central":      {"emoji": "🏙", "name": "Центральная площадь", "unlock_level": 1},
    "hollywood":    {"emoji": "🎬", "name": "Голливуд",            "unlock_level": 1},
    "gamer_street": {"emoji": "🎮", "name": "Геймер-стрит",        "unlock_level": 3},
    "music_hall":   {"emoji": "🎵", "name": "Мьюзик-холл",         "unlock_level": 5},
    "sports":       {"emoji": "🏟", "name": "Спорт-квартал",       "unlock_level": 7},
    "media_tower":  {"emoji": "📡", "name": "Медиа-башня",         "unlock_level": 10},
    "market":       {"emoji": "🛒", "name": "Рынок",               "unlock_level": 4},
    "orders":       {"emoji": "📋", "name": "Доска заказов",       "unlock_level": 2},
    "pvp_arena":    {"emoji": "⚔️", "name": "Арена PvP",            "unlock_level": 6},
    "vip_club":     {"emoji": "👑", "name": "VIP-клуб",            "unlock_level": 1},
}
```

### NPC-знаменитости
```python
NPCS = {
    "cinema": [
        {"name": "Кристофер Нолан", "emoji": "🎬"},
        {"name": "Стивен Спилберг", "emoji": "🎥"},
        {"name": "Квентин Тарантино", "emoji": "🎞"},
    ],
    "games": [
        {"name": "Хидео Кодзима", "emoji": "🎮"},
        {"name": "Тодд Говард", "emoji": "🕹"},
    ],
    "music": [
        {"name": "Drake", "emoji": "🎤"},
        {"name": "Taylor Swift", "emoji": "🎵"},
        {"name": "The Weeknd", "emoji": "🎧"},
    ],
    "sports": [
        {"name": "LeBron James", "emoji": "🏀"},
        {"name": "Lionel Messi", "emoji": "⚽"},
    ],
    "tv": [
        {"name": "Шонда Раймс", "emoji": "📺"},
        {"name": "Райан Мёрфи", "emoji": "📡"},
    ],
}
```

---

## Формулы (game/economy.py)

```python
# Доход за тап
tap_income = (base_tap + sum(upgrade_bonuses)) * archetype_multiplier * boost_multiplier

# Стоимость апгрейда
upgrade_cost = base_cost * (cost_multiplier ** current_level)

# Доход фермы
farm_income = base_income * (1.25 ** (building_level - 1)) * archetype_bonus

# Время производства фермы
production_time = base_time * (0.95 ** (building_level - 1))

# Стоимость апгрейда здания
building_upgrade_cost = base_building_cost * (2 ** current_level)

# XP для уровня
xp_for_level = int(100 * (level ** 1.5))

# PvP ELO
K = 32
expected = 1 / (1 + 10 ** ((opponent_rating - player_rating) / 400))
new_rating = player_rating + K * (result - expected)  # result: 1=win, 0=loss
```

---

## Правила и соглашения

### Код
- Весь код на **русском** (комментарии, docstrings), переменные и функции на **английском**
- Используй **type hints** везде
- **async/await** для всех I/O операций
- **Repository pattern** для работы с БД (db/repositories/)
- Бизнес-логика строго в **game/** — хендлеры только вызывают функции из game/
- Хендлеры в **bot/handlers/** регистрируют роутеры через `Router()`
- Callback data с префиксами: `city:`, `farm:`, `clicker:`, `pvp:`, `market:`, `order:`, `shop:`, `guild:`, `profile:`
- Все магические числа — в **game/constants.py**
- Логирование через стандартный `logging` модуль

### Telegram Bot
- Используй **InlineKeyboardMarkup** для всей навигации
- Обновляй сообщения через `callback_query.message.edit_text()` вместо новых сообщений
- Антифлуд: middleware с Redis-based rate limiting
- Кликер: батчинг кликов (накопление на сервере, обновление UI раз в 1-2 сек)
- Уведомления: отправлять через `bot.send_message()` когда производство завершено
- FSM (Finite State Machine) для онбординга (ввод имени → выбор аватара → выбор архетипа)
- Telegram Stars для платежей (PreCheckoutQuery, SuccessfulPayment)

### База данных
- Все запросы через **async session**
- Используй `select()`, `update()`, `delete()` из SQLAlchemy 2.0 style
- Транзакции для операций с несколькими таблицами (торговля, PvP)
- Индексы на: `players.tg_id`, `buildings.player_id`, `market_lots.resource`, `market_lots.expires_at`

### Redis
- Ключи с namespace: `hypetown:clicker:{tg_id}`, `hypetown:cooldown:{tg_id}:{action}`, `hypetown:leaderboard:coins`
- TTL на все временные ключи
- Sorted sets для лидербордов

---

## Порядок разработки (MVP)

### Фаза 1 — Каркас
1. Инициализировать проект: `requirements.txt`, `config.py`, `.env.example`
2. Настроить Docker Compose: PostgreSQL + Redis + Bot
3. Создать `db/database.py` — async engine и session
4. Создать `db/models.py` — все модели
5. Настроить Alembic и создать первую миграцию
6. Создать `main.py` — запуск бота с подключением к БД и Redis

### Фаза 2 — Онбординг
7. `bot/handlers/start.py` — команда /start
8. `bot/states/onboarding.py` — FSM: имя → аватар → архетип
9. `bot/middlewares/auth.py` — автосоздание игрока при первом контакте
10. `bot/handlers/profile.py` — /profile с основной инфой

### Фаза 3 — Кликер
11. `game/clicker.py` — логика тапа, апгрейды, формулы
12. `bot/handlers/clicker.py` — кнопка тапа, экран апгрейдов
13. `services/redis_service.py` — батчинг кликов через Redis
14. `bot/middlewares/antiflood.py` — защита от спама

### Фаза 4 — Фермы
15. `game/farms.py` — логика производства, таймеры, апгрейды
16. `bot/handlers/farms.py` — интерфейс ферм: запуск, сбор, улучшение
17. `services/scheduler.py` — APScheduler для уведомлений о готовности
18. `bot/handlers/city.py` — навигация по городу с локациями

### Фаза 5 — Заказы
19. `game/quests.py` — генерация заказов, NPC, проверка выполнения
20. `bot/handlers/orders.py` — доска заказов, выполнение

---

## .env.example
```env
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql+asyncpg://hypetown:password@localhost:5432/hypetown
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO
```

---

## Важно

- **Не пиши всё сразу** — двигайся по фазам, тестируй каждую
- **Каждый хендлер** должен регистрироваться через Router и подключаться в main.py
- **Все ответы бота** — через edit_message_text с InlineKeyboard (не новые сообщения)
- **Игровая логика** отделена от хендлеров: handler вызывает game/ функцию → получает результат → форматирует ответ
- Перед каждым этапом спрашивай, если что-то неясно
