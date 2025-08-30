from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from src.db.sqlalchemy.base import Base
from src.models.orders.enums.order_purpose import OrderPurpose
from src.models.orders.enums.order_status import OrderStatus

# Many-to-many association
order_resources = Table(
    "order_resources",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True),
    Column("resource_id", ForeignKey("base_resources.id", ondelete="CASCADE"), primary_key=True),
)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    purpose = Column(Enum(OrderPurpose), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.CREATED, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="orders")
    resources = relationship("BaseResource", secondary=order_resources, back_populates="orders")
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete")
    conflicts = relationship("OrderConflict", back_populates="order",
                             foreign_keys="[OrderConflict.order_id]", cascade="all, delete")
