"""Точка входа: запуск бота HYPETOWN + TMA API сервер."""

import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from db.database import engine
from db.models import Base
from services.redis_service import redis_client

from bot.handlers.miniapp import create_webapp
from bot.handlers.start import router as start_router
from bot.handlers.profile import router as profile_router
from bot.handlers.clicker import router as clicker_router
from bot.handlers.farms import router as farms_router
from bot.handlers.city import router as city_router
from bot.handlers.orders import router as orders_router
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.antiflood import AntifloodMiddleware
from services.scheduler import setup_scheduler, shutdown_scheduler

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, config.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    """Действия при запуске бота: создание таблиц, проверка Redis."""
    # Создание таблиц (для первого запуска; в продакшене — через Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы БД готовы")

    # Проверка Redis
    await redis_client.ping()
    logger.info("Redis подключён")

    # Планировщик (уведомления о готовности ферм)
    setup_scheduler(bot)

    bot_info = await bot.me()
    logger.info("Бот запущен: @%s", bot_info.username)


async def on_shutdown(bot: Bot) -> None:
    """Действия при остановке бота."""
    shutdown_scheduler()
    await redis_client.aclose()
    await engine.dispose()
    logger.info("Бот остановлен, соединения закрыты")


async def run_tma_api() -> None:
    """Запуск aiohttp TMA API сервера на порту 8080."""
    app = create_webapp()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("TMA API запущен на :8080")


async def main() -> None:
    """Инициализация и запуск бота + TMA API."""
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Middleware (порядок важен: antiflood → auth)
    dp.update.middleware(AntifloodMiddleware())
    dp.update.middleware(AuthMiddleware())

    # Роутеры хендлеров
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(clicker_router)
    dp.include_router(farms_router)
    dp.include_router(city_router)
    dp.include_router(orders_router)

    # Запуск TMA API параллельно с ботом
    await run_tma_api()

    logger.info("Запуск polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
