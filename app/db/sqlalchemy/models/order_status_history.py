from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, Enum, String, DateTime, func, Index
from sqlalchemy.orm import relationship

from app.db.sqlalchemy.base import Base
from app.domain.schemas.order.enums.order_status import OrderStatus


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    old_status = Column(Enum(OrderStatus), nullable=False)
    new_status = Column(Enum(OrderStatus), nullable=False)
    message = Column(String)
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


    order = relationship("Order", back_populates="status_history")

    __table_args__ = (
        Index("ix_order_status_history_order_changed", "order_id", "changed_at"),
    )
