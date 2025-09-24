from datetime import datetime

from sqlalchemy import Column, Integer, Enum, DateTime, ForeignKey, Table, func, UniqueConstraint, Index, Text
from sqlalchemy.orm import relationship
from app.db.sqlalchemy.base import Base
from app.domain.schemas.order.enums.order_purpose import OrderPurpose
from app.domain.schemas.order.enums.order_status import OrderStatus

# Many-to-many association
order_resources = Table(
    "order_resources",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True),
    Column("resource_id", ForeignKey("base_resources.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("order_id", "resource_id", name="uq_order_resource")
)

class OrderConflict(Base):
    __tablename__ = "order_conflicts"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    conflicting_order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    detected_at = Column(DateTime, default=datetime.now, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    order = relationship("Order", foreign_keys=[order_id], back_populates="conflicts")
    conflicting_order = relationship("Order", foreign_keys=[conflicting_order_id])

    __table_args__ = (
        Index("ix_order_conflict_orders", "order_id", "conflicting_order_id", unique=True),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    purpose = Column(Enum(OrderPurpose), nullable=False)
    order_description = Column(Text, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.CREATED, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    user = relationship("User", back_populates="orders", lazy="selectin", uselist=False)
    resources = relationship("BaseResource", secondary=order_resources, back_populates="orders",
                             lazy="selectin")
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete",
                                  lazy="selectin")
    conflicts = relationship("OrderConflict", back_populates="order", foreign_keys=[OrderConflict.order_id],
                             cascade="all, delete", lazy="selectin")