"""TON-платежи: проверка транзакций, минт NFT (заготовка)."""

import hashlib
import logging

logger = logging.getLogger(__name__)


async def verify_ton_transaction(boc: str, expected_amount: int) -> dict | None:
    """Проверить TON-транзакцию по BoC (Bag of Cells).

    В продакшене: декодировать BoC через tonsdk, проверить получателя и сумму.
    Сейчас — заглушка для интеграции.
    """
    # TODO: Интеграция с TON Center API / tonsdk для верификации
    logger.info("Проверка TON-транзакции: boc=%s..., expected=%d", boc[:20], expected_amount)
    return None


async def mint_nft(
    wallet_address: str,
    metadata_url: str,
    collection_address: str | None = None,
) -> str | None:
    """Минт NFT персонажа на TON.

    В продакшене: деплой через tonsdk + смарт-контракт коллекции.
    Возвращает адрес NFT или None при ошибке.
    """
    # TODO: Реализация минта через TON SDK
    logger.info(
        "NFT mint запрос: wallet=%s, metadata=%s, collection=%s",
        wallet_address, metadata_url, collection_address,
    )
    return None
