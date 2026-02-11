"""Валидация Telegram WebApp initData для Mini App."""

import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qs, unquote

from config import config

logger = logging.getLogger(__name__)


def validate_init_data(init_data: str) -> dict | None:
    """Валидация initData от Telegram WebApp.

    Возвращает распарсенные данные пользователя или None при невалидном хеше.
    Документация: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    parsed = parse_qs(init_data)
    received_hash = parsed.get("hash", [None])[0]

    if not received_hash:
        logger.warning("initData без hash")
        return None

    # Собираем data-check-string: все поля кроме hash, отсортированные по ключу
    data_pairs = []
    for key, values in parsed.items():
        if key == "hash":
            continue
        data_pairs.append(f"{key}={unquote(values[0])}")
    data_pairs.sort()
    data_check_string = "\n".join(data_pairs)

    # HMAC-SHA256: secret_key = HMAC_SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        b"WebAppData",
        config.bot_token.encode(),
        hashlib.sha256,
    ).digest()

    # Вычисляем хеш и сравниваем
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        logger.warning("Невалидный hash в initData")
        return None

    # Парсим данные пользователя
    user_raw = parsed.get("user", [None])[0]
    if user_raw:
        user_data = json.loads(unquote(user_raw))
    else:
        user_data = {}

    return {
        "user": user_data,
        "auth_date": parsed.get("auth_date", [None])[0],
        "query_id": parsed.get("query_id", [None])[0],
    }
