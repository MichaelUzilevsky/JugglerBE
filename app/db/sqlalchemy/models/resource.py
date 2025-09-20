from datetime import datetime

from sqlalchemy import Column, Integer, String, Enum, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db.sqlalchemy.base import Base
from app.db.sqlalchemy.models import order_resources
from app.domain.schemas.resource.enums.resource_environment import ResourceEnvironment
from app.domain.schemas.resource.enums.resource_state import ResourceState
from app.domain.schemas.resource.enums.resource_type import ResourceType
from app.domain.schemas.resource.enums.rt_locations import RtLocations

resource_environment_enum = Enum(
    ResourceEnvironment,
    name="resource_environment"
)

class BaseResource(Base):
    __tablename__ = "base_resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    resource_state = Column(Enum(ResourceState), nullable=False)
    resource_type = Column(Enum(ResourceType), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    __mapper_args__ = {
        "polymorphic_on": resource_type,
        # "polymorphic_identity": ResourceType.BASE.value,
    }

    orders = relationship("Order", secondary=order_resources, back_populates="resources")
    state_history = relationship("ResourceStateHistory", back_populates="resource",
                                 cascade="all, delete", lazy="selectin")


class Rt(BaseResource):
    __tablename__ = "rts"

    id = Column(Integer, ForeignKey("base_resources.id", ondelete="CASCADE"), primary_key=True)
    location = Column(Enum(RtLocations), nullable=False)

    __mapper_args__ = {"polymorphic_identity": ResourceType.RT.value}


class Station(BaseResource):
    __tablename__ = "stations"

    id = Column(Integer, ForeignKey("base_resources.id", ondelete="CASCADE"), primary_key=True)
    environment = Column(resource_environment_enum, nullable=False)
    version = Column(String(50), nullable=False)

    __mapper_args__ = {"polymorphic_identity": ResourceType.STATION.value}


class CrawlerRoute(BaseResource):
    __tablename__ = "crawler_routes"

    id = Column(Integer, ForeignKey("base_resources.id", ondelete="CASCADE"), primary_key=True)
    environment =Column(resource_environment_enum, nullable=False)
    horizon_route = Column(Integer)

    __mapper_args__ = {"polymorphic_identity": ResourceType.CRAWLER_ROUTE.value}


class PandemicRoute(BaseResource):
    __tablename__ = "pandemic_routes"

    id = Column(Integer, ForeignKey("base_resources.id", ondelete="CASCADE"), primary_key=True)
    environment = Column(resource_environment_enum, nullable=False)

    __mapper_args__ = {"polymorphic_identity": ResourceType.PANDEMIC_ROUTE.value}
