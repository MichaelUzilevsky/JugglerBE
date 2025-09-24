from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, Enum, String, DateTime, func, Index
from sqlalchemy.orm import relationship

from app.db.sqlalchemy.base import Base
from app.domain.schemas.resource.enums.resource_state import ResourceState


class ResourceStateHistory(Base):
    __tablename__ = "resource_state_history"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("base_resources.id", ondelete="CASCADE"), nullable=False)
    old_state = Column(Enum(ResourceState), nullable=False)
    new_state = Column(Enum(ResourceState), nullable=False)
    description = Column(String)
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(DateTime, default=datetime.now, nullable=False)
    resource = relationship("BaseResource", back_populates="state_history")

    __table_args__ = (
        Index("ix_resource_state_history_resource_changed", "resource_id", "changed_at"),
    )