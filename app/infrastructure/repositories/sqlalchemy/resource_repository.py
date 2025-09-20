from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import with_polymorphic, contains_eager

from app.db.sqlalchemy.models import BaseResource, Rt, Station, CrawlerRoute, PandemicRoute, ResourceStateHistory
from app.domain.exceptions.repository_exceptions import IntegrityViolationException, NotFoundException
from app.domain.schemas.resource.enums.resource_type import ResourceType
from app.exceptions.resources_exceptions.resource_already_exists_exception import ResourceAlreadyExistsException
from app.infrastructure.mappers.sqlalchemy.resource_mapper import ResourceMapper
from app.domain.repositories.iresource_repository import IResourceRepository
from app.infrastructure.repositories.sqlalchemy.base_repository import SQLAlchemyBaseRepository
from app.infrastructure.mappers.sqlalchemy.resource_mapper import ResourceReadSchema, ResourceCreateSchema, \
    ResourceUpdateSchema


class SQLAlchemyResourceRepository(
    SQLAlchemyBaseRepository[ResourceReadSchema, ResourceCreateSchema, ResourceUpdateSchema, BaseResource],
    IResourceRepository,
):
    """
    Resource repository specialized for SQLAlchemy.
    Works with BaseResource and its polymorphic subclasses.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, BaseResource, ResourceMapper)

    @staticmethod
    def _with_latest_state_query(resource_poly, base_query):
        latest_sub_query = (
            select(
                ResourceStateHistory.resource_id,
                func.max(ResourceStateHistory.changed_at).label("max_changed_at")
            )
            .group_by(ResourceStateHistory.resource_id)
            .subquery()
        )

        latest_history = (
            select(ResourceStateHistory)
            .join(
                latest_sub_query,
                and_(
                    ResourceStateHistory.resource_id == latest_sub_query.c.resource_id,
                    ResourceStateHistory.changed_at == latest_sub_query.c.max_changed_at
                )
            )
            .subquery()
        )

        return (
            base_query
            .join(latest_history, BaseResource.id == latest_history.c.resource_id, isouter=True)
            .options(contains_eager(resource_poly.state_history, alias=latest_history))
        )

    async def get(self, obj_id: int) -> Optional[ResourceReadSchema]:
        resource_poly = with_polymorphic(BaseResource, [Rt, Station, CrawlerRoute, PandemicRoute])
        stmt = select(resource_poly).where(resource_poly.id == obj_id)
        stmt = self._with_latest_state_query(resource_poly, stmt)

        result = await self.session.execute(stmt)
        orm_obj = result.unique().scalar_one_or_none()
        return self.mapper.to_read(orm_obj) if orm_obj else None

    async def list(self) -> List[ResourceReadSchema]:
        resource_poly = with_polymorphic(BaseResource, [Rt, Station, CrawlerRoute, PandemicRoute])
        stmt = select(resource_poly)
        stmt = self._with_latest_state_query(resource_poly, stmt)

        result = await self.session.execute(stmt)
        orm_objs = result.unique().scalars().all()
        return [self.mapper.to_read(o) for o in orm_objs]

    async def list_by_type(self, resource_type: ResourceType) -> List[ResourceReadSchema]:
        resource_poly = with_polymorphic(BaseResource, [Rt, Station, CrawlerRoute, PandemicRoute])
        stmt = select(resource_poly).where(BaseResource.resource_type == resource_type)
        stmt = self._with_latest_state_query(resource_poly, stmt)

        result = await self.session.execute(stmt)
        orm_objs = result.unique().scalars().all()
        return [self.mapper.to_read(obj) for obj in orm_objs]

    async def get_supported_types(self) -> List[str]:
        return [rt for rt in ResourceType]

    async def create(self, create_schema: ResourceCreateSchema, **kwargs) -> ResourceReadSchema:
        changing_user_id = kwargs.get("changing_user_id")
        if changing_user_id is None:
            raise ValueError("changing_user_id is required")
        try:
            # First, create the resource with base logic
            resource = await super().create(create_schema)

            # Always add initial state history (even if no state change)
            history = ResourceStateHistory(
                resource_id=resource.id,
                old_state=resource.resource_state,
                new_state=resource.resource_state,
                description=create_schema.description or "Initial state",
                changed_by=changing_user_id,
            )
            self.session.add(history)
            await self.session.flush()

            return await self.get(resource.id)

        except IntegrityViolationException as e:
            err = str(e).lower()
            if "name" in err:
                raise ResourceAlreadyExistsException("Resource with this name already exists")
            raise

    async def update(self, obj_id: int, update_schema: ResourceUpdateSchema, **kwargs) -> Optional[ResourceReadSchema]:
        changing_user_id = kwargs.get("changing_user_id")
        if changing_user_id is None:
            raise ValueError("changing_user_id is required")

        # Fetch current object first to check state
        stmt = select(BaseResource).where(BaseResource.id == obj_id)
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()
        if not orm_obj:
            raise NotFoundException(f"Resource with id={obj_id} not found")

        old_state = orm_obj.resource_state

        # Run the normal update
        try:
            await super().update(obj_id, update_schema)

            # Log state history if state or description provided
            if update_schema.resource_state is not None or update_schema.description:
                new_state = update_schema.resource_state or old_state
                history = ResourceStateHistory(
                    resource_id=orm_obj.id,
                    old_state=old_state,
                    new_state=new_state,
                    description=update_schema.description or "No description",
                    changed_by=changing_user_id,
                )
                self.session.add(history)
                await self.session.flush()

            return await self.get(obj_id)

        except IntegrityViolationException as e:
            err = str(e).lower()
            if "name" in err:
                raise ResourceAlreadyExistsException("Resource with this name already exists")
            raise

    async def delete(self, obj_id: int) -> bool:
        try:
            return await super().delete(obj_id)
        except NotFoundException:
            raise NotFoundException(f"Resource with id={obj_id} not found")
