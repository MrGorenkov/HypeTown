"""SQLAlchemy модели для всех таблиц HYPETOWN."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from game.constants import (
    Archetype,
    BuildingType,
    ClickerUpgradeType,
    GuildRole,
    MatchType,
    Resource,
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


class Player(Base):
    """Игрок."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    avatar: Mapped[str] = mapped_column(String(8), nullable=False)
    archetype: Mapped[Archetype] = mapped_column(Enum(Archetype), nullable=False)

    level: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    xp: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    coins: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    stars: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    pvp_rating: Mapped[int] = mapped_column(Integer, default=1000, server_default="1000")
    prestige: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    tap_power: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    passive_income: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    premium_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # TMA / 3D
    model_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ton_wallet: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_active: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Связи
    buildings: Mapped[list["Building"]] = relationship(back_populates="player", lazy="selectin")
    inventory: Mapped[list["Inventory"]] = relationship(back_populates="player", lazy="selectin")
    orders: Mapped[list["Order"]] = relationship(back_populates="player", lazy="selectin")
    clicker_upgrades: Mapped[list["ClickerUpgrade"]] = relationship(back_populates="player", lazy="selectin")
    achievements: Mapped[list["Achievement"]] = relationship(back_populates="player", lazy="selectin")
    daily_quests: Mapped[list["DailyQuest"]] = relationship(back_populates="player", lazy="selectin")


class Building(Base):
    """Здание (ферма) игрока."""

    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    type: Mapped[BuildingType] = mapped_column(Enum(BuildingType), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    is_producing: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    production_started: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    production_ends: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_collected: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    player: Mapped["Player"] = relationship(back_populates="buildings")


class Inventory(Base):
    """Инвентарь игрока (ресурсы)."""

    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    resource: Mapped[Resource] = mapped_column(Enum(Resource), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    player: Mapped["Player"] = relationship(back_populates="inventory")


class Order(Base):
    """Заказ от NPC."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    npc_name: Mapped[str] = mapped_column(String(64), nullable=False)
    npc_category: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[dict] = mapped_column(JSON, nullable=False)
    reward_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_reward_coins: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    player: Mapped["Player"] = relationship(back_populates="orders")


class MarketLot(Base):
    """Лот на рынке."""

    __tablename__ = "market_lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    resource: Mapped[Resource] = mapped_column(Enum(Resource), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    buyer_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    sold_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    seller: Mapped["Player"] = relationship(foreign_keys=[seller_id])
    buyer: Mapped["Player | None"] = relationship(foreign_keys=[buyer_id])


class PvpMatch(Base):
    """PvP матч."""

    __tablename__ = "pvp_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player1_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    player2_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    match_type: Mapped[MatchType] = mapped_column(Enum(MatchType), nullable=False)
    bet: Mapped[int] = mapped_column(Integer, nullable=False)
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)
    rating_change: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    player1: Mapped["Player"] = relationship(foreign_keys=[player1_id])
    player2: Mapped["Player"] = relationship(foreign_keys=[player2_id])
    winner: Mapped["Player | None"] = relationship(foreign_keys=[winner_id])


class Guild(Base):
    """Гильдия (медиахолдинг)."""

    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    leader_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    leader: Mapped["Player"] = relationship(foreign_keys=[leader_id])
    members: Mapped[list["GuildMember"]] = relationship(back_populates="guild", lazy="selectin")


class GuildMember(Base):
    """Участник гильдии."""

    __tablename__ = "guild_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guild_id: Mapped[int] = mapped_column(ForeignKey("guilds.id"), nullable=False, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, unique=True)
    role: Mapped[GuildRole] = mapped_column(Enum(GuildRole), nullable=False, default=GuildRole.MEMBER)
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    guild: Mapped["Guild"] = relationship(back_populates="members")
    player: Mapped["Player"] = relationship()


class ClickerUpgrade(Base):
    """Апгрейд кликера игрока."""

    __tablename__ = "clicker_upgrades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    upgrade_type: Mapped[ClickerUpgradeType] = mapped_column(Enum(ClickerUpgradeType), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    player: Mapped["Player"] = relationship(back_populates="clicker_upgrades")


class Achievement(Base):
    """Достижение игрока."""

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    achievement_type: Mapped[str] = mapped_column(String(64), nullable=False)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    player: Mapped["Player"] = relationship(back_populates="achievements")


class DailyQuest(Base):
    """Ежедневный квест."""

    __tablename__ = "daily_quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    quest_type: Mapped[str] = mapped_column(String(64), nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    target: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    date: Mapped[date] = mapped_column(Date, nullable=False)

    player: Mapped["Player"] = relationship(back_populates="daily_quests")
