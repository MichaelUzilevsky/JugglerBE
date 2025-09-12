from typing import Union, Annotated

from pydantic import Field

from app.db.sqlalchemy.models import (
    BaseResource,
    Rt,
    Station,
    CrawlerRoute,
    PandemicRoute,
)
from app.domain.schemas.resource.resource import RtCreate, StationCreate, CrawlerRouteUpdate, PandemicRouteCreate, \
    CrawlerRouteCreate, PandemicRouteRead, PandemicRouteUpdate, CrawlerRouteRead, StationUpdate, RtUpdate, StationRead, \
    RtRead

ResourceCreateSchema = Union[RtCreate, StationCreate, CrawlerRouteCreate, PandemicRouteCreate]
ResourceUpdateSchema = Union[RtUpdate, StationUpdate, CrawlerRouteUpdate, PandemicRouteUpdate]
ResourceReadSchema = Annotated[
    Union[RtRead, StationRead, CrawlerRouteRead, PandemicRouteRead],
    Field(discriminator="resource_type"),
]

class ResourceMapper:
    # -----------------------
    # ORM ↔ Domain (Create)
    # -----------------------
    @staticmethod
    def to_orm(create_schema: ResourceCreateSchema) -> BaseResource:
        if isinstance(create_schema, RtCreate):
            return Rt(
                name=create_schema.name,
                resource_state=create_schema.resource_state,
                location=create_schema.location,
            )
        elif isinstance(create_schema, StationCreate):
            return Station(
                name=create_schema.name,
                resource_state=create_schema.resource_state,
                version=create_schema.version,
            )
        elif isinstance(create_schema, CrawlerRouteCreate):
            return CrawlerRoute(
                name=create_schema.name,
                resource_state=create_schema.resource_state,
            )
        elif isinstance(create_schema, PandemicRouteCreate):
            return PandemicRoute(
                name=create_schema.name,
                resource_state=create_schema.resource_state,
            )
        else:
            raise ValueError(f"Unsupported create schema type: {type(create_schema)}")

    # -----------------------
    # ORM ↔ Domain (Read)
    # -----------------------
    @staticmethod
    def to_read(resource: BaseResource) -> ResourceReadSchema:
        if isinstance(resource, Rt):
            return RtRead.model_validate(resource)
        elif isinstance(resource, Station):
            return StationRead.model_validate(resource)
        elif isinstance(resource, CrawlerRoute):
            return CrawlerRouteRead.model_validate(resource)
        elif isinstance(resource, PandemicRoute):
            return PandemicRouteRead.model_validate(resource)
        else:
            raise ValueError(f"Unsupported ORM resource type: {type(resource)}")

    # -----------------------
    # ORM ↔ Domain (Update)
    # -----------------------
    @staticmethod
    def update_orm(resource: BaseResource, update_schema: ResourceUpdateSchema) -> BaseResource:
        if update_schema.name is not None:
            resource.name = update_schema.name
        if update_schema.resource_state is not None:
            resource.resource_state = update_schema.resource_state

        # subtype-specific fields
        if isinstance(resource, Rt) and isinstance(update_schema, RtUpdate):
            if update_schema.location is not None:
                resource.location = update_schema.location
        elif isinstance(resource, Station) and isinstance(update_schema, StationUpdate):
            if update_schema.version is not None:
                resource.version = update_schema.version
        # For CrawlerRoute / PandemicRoute → no extra fields yet

        return resource
