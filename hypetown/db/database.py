"""Асинхронное подключение к PostgreSQL через SQLAlchemy 2.0."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import config

# Асинхронный движок PostgreSQL
engine = create_async_engine(
    config.database_url,
    echo=False,
    pool_size=20,
    max_overflow=10,
)

# Фабрика асинхронных сессий
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
