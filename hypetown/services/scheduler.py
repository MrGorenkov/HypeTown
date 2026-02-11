"""APScheduler: таймеры ферм, уведомления о готовности производства."""

import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db.database import async_session
from db.repositories.building import get_ready_buildings
from game.constants import BUILDINGS

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_production_ready(bot: Bot) -> None:
    """Проверить все здания с завершённым производством и отправить уведомления."""
    async with async_session() as session:
        ready = await get_ready_buildings(session)

    if not ready:
        return

    for building in ready:
        info = BUILDINGS.get(building.type.value, {})
        try:
            # Получаем tg_id игрока через relationship
            async with async_session() as session:
                from db.models import Player
                from sqlalchemy import select
                result = await session.execute(
                    select(Player.tg_id).where(Player.id == building.player_id)
                )
                tg_id = result.scalar_one_or_none()

            if tg_id:
                await bot.send_message(
                    tg_id,
                    f"📦 {info.get('emoji', '🏗')} <b>{info.get('name', 'Здание')}</b> "
                    f"завершило производство!\n"
                    f"Зайди собрать продукцию 💰",
                )
        except Exception as e:
            logger.error("Ошибка уведомления для building_id=%d: %s", building.id, e)

    logger.info("Отправлено %d уведомлений о готовности", len(ready))


def setup_scheduler(bot: Bot) -> None:
    """Настроить и запустить планировщик."""
    # Проверка готовности ферм каждые 30 секунд
    scheduler.add_job(
        check_production_ready,
        "interval",
        seconds=30,
        args=[bot],
        id="check_production",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Планировщик запущен")


def shutdown_scheduler() -> None:
    """Остановить планировщик."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Планировщик остановлен")
