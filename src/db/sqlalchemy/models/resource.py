from sqlalchemy import Column, Integer, String, Enum, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from src.db.sqlalchemy.base import Base
from src.models.resources.enums.resource_state import ResourceState
from src.models.resources.enums.rt_locations import RtLocations


class BaseResource(Base):
    __tablename__ = "base_resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    resource_state = Column(Enum(ResourceState), nullable=False)
    resource_type = Column(String(50), nullable=False)  # discriminator
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __mapper_args__ = {
        "polymorphic_on": resource_type,
        "polymorphic_identity": "base_resource",
    }

    orders = relationship("Order", secondary="order_resources", back_populates="resources")
    state_history = relationship("ResourceStateHistory", back_populates="resource", cascade="all, delete")


class Rt(BaseResource):
    __tablename__ = "rts"

    id = Column(Integer, ForeignKey("base_resources.id", ondelete="CASCADE"), primary_key=True)
    location = Column(Enum(RtLocations), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "rt"}


class Station(BaseResource):
    __tablename__ = "stations"

    id = Column(Integer, ForeignKey("base_resources.id", ondelete="CASCADE"), primary_key=True)
    version = Column(String(50), nullable=False)

    __mapper_args__ = {"polymorphic_identity": "station"}


class CrawlerRoute(BaseResource):
    __tablename__ = "crawler_routes"

    id = Column(Integer, ForeignKey("base_resources.id", ondelete="CASCADE"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "crawler_route"}


class PandemicRoute(BaseResource):
    __tablename__ = "pandemic_routes"

    id = Column(Integer, ForeignKey("base_resources.id", ondelete="CASCADE"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "pandemic_route"}
