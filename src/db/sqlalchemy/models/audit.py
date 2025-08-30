from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, func
from src.db.sqlalchemy.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"))
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
