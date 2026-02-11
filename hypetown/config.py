"""Загрузка конфигурации из .env файла."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    """Конфигурация приложения."""

    bot_token: str
    database_url: str
    redis_url: str
    log_level: str
    # TMA / Miniapp
    webapp_url: str
    s3_bucket: str
    s3_endpoint: str
    cloudinary_url: str

    @staticmethod
    def from_env() -> "Config":
        """Создать конфиг из переменных окружения."""
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN не задан в .env")

        return Config(
            bot_token=bot_token,
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://hypetown:password@localhost:5432/hypetown",
            ),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            webapp_url=os.getenv("WEBAPP_URL", ""),
            s3_bucket=os.getenv("S3_BUCKET", ""),
            s3_endpoint=os.getenv("S3_ENDPOINT", ""),
            cloudinary_url=os.getenv("CLOUDINARY_URL", ""),
        )


config = Config.from_env()
