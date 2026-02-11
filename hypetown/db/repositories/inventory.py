"""CRUD операции для инвентаря (ресурсы игрока)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Inventory
from game.constants import Resource


async def get_inventory(session: AsyncSession, player_id: int) -> dict[str, int]:
    """Получить инвентарь как словарь {resource: quantity}."""
    result = await session.execute(
        select(Inventory).where(Inventory.player_id == player_id)
    )
    return {inv.resource.value: inv.quantity for inv in result.scalars().all()}


async def add_resource(
    session: AsyncSession,
    player_id: int,
    resource: str,
    quantity: int,
) -> int:
    """Добавить ресурс в инвентарь. Возвращает новое количество."""
    result = await session.execute(
        select(Inventory).where(
            Inventory.player_id == player_id,
            Inventory.resource == Resource(resource),
        )
    )
    inv = result.scalar_one_or_none()

    if inv:
        inv.quantity += quantity
    else:
        inv = Inventory(
            player_id=player_id,
            resource=Resource(resource),
            quantity=quantity,
        )
        session.add(inv)

    await session.commit()
    return inv.quantity


async def has_resources(
    session: AsyncSession,
    player_id: int,
    requirements: dict[str, int],
) -> tuple[bool, dict[str, int]]:
    """Проверить наличие ресурсов. Возвращает (ok, missing)."""
    inventory = await get_inventory(session, player_id)
    missing = {}
    for res, needed in requirements.items():
        have = inventory.get(res, 0)
        if have < needed:
            missing[res] = needed - have
    return len(missing) == 0, missing
