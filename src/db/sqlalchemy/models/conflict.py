from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, func
from sqlalchemy.orm import relationship
from src.db.sqlalchemy.base import Base

class OrderConflict(Base):
    __tablename__ = "orders_conflict"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    conflicting_order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    resolution = Column(String(50))

    order = relationship("Order", foreign_keys=[order_id], back_populates="conflicts")
