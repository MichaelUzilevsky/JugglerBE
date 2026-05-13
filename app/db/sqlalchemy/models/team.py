from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.db.sqlalchemy.base import Base
from app.domain.schemas.order.enums.order_purpose import OrderPurpose


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    users = relationship("User", back_populates="team")
    permissions = relationship("TeamPermission", back_populates="team", cascade="all, delete-orphan")


class TeamPermission(Base):
    __tablename__ = "team_permissions"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    order_purpose = Column(Enum(OrderPurpose), nullable=False)

    team = relationship("Team", back_populates="permissions")

    __table_args__ = (
        UniqueConstraint("team_id", "order_purpose", name="uq_team_purpose"),
    )
