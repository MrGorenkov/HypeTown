"""Redis-сервис: подключение, кэш, лидерборды, батчинг кликов."""

import time

import redis.asyncio as redis

from config import config

# Пул подключений к Redis
redis_client: redis.Redis = redis.from_url(
    config.redis_url,
    decode_responses=True,
)

NAMESPACE = "hypetown"


def key(*parts: str) -> str:
    """Генерация ключа с namespace: hypetown:part1:part2:..."""
    return f"{NAMESPACE}:{':'.join(parts)}"


# ── Батчинг кликов ───────────────────────────────────────────────────

async def add_pending_taps(tg_id: int, count: int) -> int:
    """Накопить тапы в Redis. Возвращает общее число pending."""
    k = key("clicker", str(tg_id))
    total = await redis_client.incrby(k, count)
    await redis_client.expire(k, 30)  # TTL 30 сек
    return total


async def flush_pending_taps(tg_id: int) -> int:
    """Забрать и обнулить накопленные тапы. Возвращает количество."""
    k = key("clicker", str(tg_id))
    pipe = redis_client.pipeline()
    pipe.get(k)
    pipe.delete(k)
    results = await pipe.execute()
    return int(results[0] or 0)


# ── Кулдауны / Rate Limiting ─────────────────────────────────────────

async def check_cooldown(tg_id: int, action: str, cooldown_sec: int) -> bool:
    """Проверить кулдаун. True = можно действовать, False = ещё на кулдауне."""
    k = key("cooldown", str(tg_id), action)
    if await redis_client.exists(k):
        return False
    await redis_client.setex(k, cooldown_sec, "1")
    return True


async def get_cooldown_ttl(tg_id: int, action: str) -> int:
    """Оставшееся время кулдауна в секундах."""
    k = key("cooldown", str(tg_id), action)
    ttl = await redis_client.ttl(k)
    return max(0, ttl)


# ── Rate Limiting (antiflood) ────────────────────────────────────────

async def check_rate_limit(tg_id: int, limit: int = 30, window: int = 60) -> bool:
    """Sliding window rate limiter. True = разрешено, False = лимит."""
    k = key("ratelimit", str(tg_id))
    now = time.time()
    pipe = redis_client.pipeline()
    pipe.zremrangebyscore(k, 0, now - window)  # Удалить старые
    pipe.zadd(k, {str(now): now})              # Добавить текущий
    pipe.zcard(k)                               # Подсчитать
    pipe.expire(k, window)
    results = await pipe.execute()
    count = results[2]
    return count <= limit


# ── Лидерборд ────────────────────────────────────────────────────────

async def update_leaderboard(tg_id: int, coins: int) -> None:
    """Обновить позицию в лидерборде монет."""
    k = key("leaderboard", "coins")
    await redis_client.zadd(k, {str(tg_id): coins})


async def get_leaderboard_top(count: int = 10) -> list[tuple[str, float]]:
    """Получить топ игроков по монетам."""
    k = key("leaderboard", "coins")
    return await redis_client.zrevrange(k, 0, count - 1, withscores=True)


async def get_leaderboard_rank(tg_id: int) -> int | None:
    """Получить ранг игрока (0-based). None если не в лидерборде."""
    k = key("leaderboard", "coins")
    rank = await redis_client.zrevrank(k, str(tg_id))
    return rank
