from datetime import datetime

from sqlalchemy import Column, String, Enum, Integer, DateTime, func
from sqlalchemy.orm import relationship
from app.db.sqlalchemy.base import Base
from app.domain.schemas.user.enums.user_role import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    orders = relationship("Order", back_populates="user", cascade="all, delete")
