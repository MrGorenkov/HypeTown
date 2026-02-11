"""TMA API: HTTP-эндпоинты для Telegram Mini App (Unity WebGL).

Запускается как aiohttp web-сервер параллельно с ботом.
Unity клиент шлёт запросы с initData в заголовке Authorization.
"""

import json
import logging
from datetime import datetime

from aiohttp import web
from aiohttp.web import Request, Response

from db.database import async_session
from db.repositories.player import get_player_by_tg_id
from game.constants import ARCHETYPES, BUILDINGS
from services.tma_auth import validate_init_data

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()


def _get_tg_id(request: Request) -> int | None:
    """Извлечь и валидировать tg_id из initData в заголовке Authorization."""
    init_data = request.headers.get("Authorization", "")
    if not init_data:
        return None
    data = validate_init_data(init_data)
    if not data or not data.get("user"):
        return None
    return data["user"].get("id")


# ── Game State ────────────────────────────────────────────────────────

@routes.get("/api/state")
async def get_game_state(request: Request) -> Response:
    """Получить полное состояние игрока для Unity — монеты, здания, апгрейды."""
    tg_id = _get_tg_id(request)
    if not tg_id:
        return web.json_response({"error": "unauthorized"}, status=401)

    async with async_session() as session:
        player = await get_player_by_tg_id(session, tg_id)

    if not player:
        return web.json_response({"error": "player_not_found"}, status=404)

    arch = ARCHETYPES.get(player.archetype.value, {})
    buildings_data = []
    for b in player.buildings:
        bld_info = BUILDINGS.get(b.type.value, {})
        buildings_data.append({
            "id": b.id,
            "type": b.type.value,
            "name": bld_info.get("name", ""),
            "level": b.level,
            "is_producing": b.is_producing,
            "production_ends": b.production_ends.isoformat() if b.production_ends else None,
        })

    return web.json_response({
        "player": {
            "id": player.id,
            "tg_id": player.tg_id,
            "name": player.name,
            "avatar": player.avatar,
            "archetype": player.archetype.value,
            "archetype_emoji": arch.get("emoji", ""),
            "level": player.level,
            "xp": player.xp,
            "coins": player.coins,
            "stars": player.stars,
            "tap_power": player.tap_power,
            "passive_income": player.passive_income,
            "pvp_rating": player.pvp_rating,
            "model_url": player.model_url,
            "ton_wallet": player.ton_wallet,
        },
        "buildings": buildings_data,
        "upgrades": [
            {"type": u.upgrade_type.value, "level": u.level}
            for u in player.clicker_upgrades
        ],
    })


# ── Tap (клик из Unity) ──────────────────────────────────────────────

@routes.post("/api/tap")
async def handle_tap(request: Request) -> Response:
    """Обработка тапов из Unity Mini App. Принимает количество тапов за батч."""
    tg_id = _get_tg_id(request)
    if not tg_id:
        return web.json_response({"error": "unauthorized"}, status=401)

    body = await request.json()
    tap_count = min(body.get("taps", 1), 50)  # Макс 50 тапов за батч

    async with async_session() as session:
        player = await get_player_by_tg_id(session, tg_id)
        if not player:
            return web.json_response({"error": "player_not_found"}, status=404)

        earned = player.tap_power * tap_count
        player.coins += earned
        player.last_active = datetime.utcnow()
        await session.commit()

        return web.json_response({
            "earned": earned,
            "total_coins": player.coins,
            "tap_power": player.tap_power,
        })


# ── 3D Model URL ─────────────────────────────────────────────────────

@routes.post("/api/model")
async def update_model_url(request: Request) -> Response:
    """Обновить URL 3D-модели персонажа (GLB из TripoSR/Cloudinary)."""
    tg_id = _get_tg_id(request)
    if not tg_id:
        return web.json_response({"error": "unauthorized"}, status=401)

    body = await request.json()
    model_url = body.get("model_url", "")
    if not model_url or len(model_url) > 512:
        return web.json_response({"error": "invalid_model_url"}, status=400)

    async with async_session() as session:
        player = await get_player_by_tg_id(session, tg_id)
        if not player:
            return web.json_response({"error": "player_not_found"}, status=404)

        player.model_url = model_url
        await session.commit()

        return web.json_response({"ok": True, "model_url": model_url})


# ── TON Wallet ────────────────────────────────────────────────────────

@routes.post("/api/wallet/connect")
async def connect_wallet(request: Request) -> Response:
    """Привязать TON-кошелёк к профилю игрока."""
    tg_id = _get_tg_id(request)
    if not tg_id:
        return web.json_response({"error": "unauthorized"}, status=401)

    body = await request.json()
    wallet_address = body.get("address", "")
    if not wallet_address:
        return web.json_response({"error": "missing_address"}, status=400)

    async with async_session() as session:
        player = await get_player_by_tg_id(session, tg_id)
        if not player:
            return web.json_response({"error": "player_not_found"}, status=404)

        player.ton_wallet = wallet_address
        await session.commit()

        return web.json_response({"ok": True, "wallet": wallet_address})


# ── Фабрика приложения ───────────────────────────────────────────────

def create_webapp() -> web.Application:
    """Создать aiohttp приложение для TMA API."""
    app = web.Application()
    app.add_routes(routes)
    return app
