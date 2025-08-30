from sqlalchemy import Column, Integer, Enum, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from src.db.sqlalchemy.base import Base
from src.models.orders.enums.order_status import OrderStatus
from src.models.resources.enums.resource_state import ResourceState


class ResourceStateHistory(Base):
    __tablename__ = "resource_state_history"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("base_resources.id", ondelete="CASCADE"))
    old_state = Column(Enum(ResourceState))
    new_state = Column(Enum(ResourceState))
    description = Column(Text)
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    resource = relationship("BaseResource", back_populates="state_history")

class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    old_status = Column(Enum(OrderStatus))
    new_status = Column(Enum(OrderStatus))
    message = Column(Text)
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="status_history")
