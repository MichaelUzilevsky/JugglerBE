from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import with_polymorphic, contains_eager

from app.db.sqlalchemy.models import BaseResource, Rt, Station, CrawlerRoute, PandemicRoute, ResourceStateHistory
from app.domain.exceptions.repository_exceptions import IntegrityViolationException, NotFoundException, \
    RepositoryException
from app.domain.repositories.iresource_repository import IResourceRepository
from app.domain.schemas.resource.enums.resource_type import ResourceType
from app.exceptions.resources_exceptions.resources_exceptions import ResourceAlreadyExistsException, \
    ResourceNotFoundException
from app.infrastructure.mappers.sqlalchemy.resource_mapper import ResourceMapper
from app.infrastructure.mappers.sqlalchemy.resource_mapper import ResourceReadSchema, ResourceCreateSchema, \
    ResourceUpdateSchema
from app.infrastructure.repositories.sqlalchemy.base_repository import SQLAlchemyBaseRepository


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
        try:
            resource_poly = with_polymorphic(BaseResource, [Rt, Station, CrawlerRoute, PandemicRoute])
            stmt = select(resource_poly).where(resource_poly.id == obj_id)
            stmt = self._with_latest_state_query(resource_poly, stmt)

            result = await self.session.execute(stmt)
            orm_obj = result.unique().scalar_one_or_none()

            if not orm_obj:
                self._log_warning(
                    event="resource_get_not_found",
                    msg=f"Resource not found with id={obj_id}",
                    extra={"resource_id": obj_id}
                )
                raise ResourceNotFoundException(f"Resource with id={obj_id} not found")

            self._log_info(
                event="resource_get_success",
                msg=f"Fetched resource with id={obj_id}",
                extra={"resource_id": obj_id, "resource_type": orm_obj.resource_type.value}
            )
            return self.mapper.to_read(orm_obj)

        except SQLAlchemyError as e:
            self._log_error(
                event="resource_get_db_error",
                msg=f"Database error while fetching resource id={obj_id}",
                extra={"resource_id": obj_id, "error": str(e)}
            )
            raise RepositoryException()

    async def list(self) -> List[ResourceReadSchema]:
        try:
            resource_poly = with_polymorphic(BaseResource, [Rt, Station, CrawlerRoute, PandemicRoute])
            stmt = select(resource_poly)
            stmt = self._with_latest_state_query(resource_poly, stmt)

            result = await self.session.execute(stmt)
            orm_objs = result.unique().scalars().all()

            self._log_info(
                event="resource_list_success",
                msg=f"Fetched list of {len(orm_objs)} resources",
                extra={"count": len(orm_objs)}
            )
            return [self.mapper.to_read(o) for o in orm_objs]

        except SQLAlchemyError as e:
            self._log_error(
                "resource_list_db_error",
                "Database error while listing resources",
                {"error": str(e)}
            )
            raise RepositoryException()

    async def list_by_type(self, resource_type: ResourceType) -> List[ResourceReadSchema]:
        try:
            resource_poly = with_polymorphic(BaseResource, [Rt, Station, CrawlerRoute, PandemicRoute])
            stmt = select(resource_poly).where(BaseResource.resource_type == resource_type)
            stmt = self._with_latest_state_query(resource_poly, stmt)

            result = await self.session.execute(stmt)
            orm_objs = result.unique().scalars().all()

            self._log_info(
                event="resource_list_by_type_success",
                msg=f"Fetched list of {len(orm_objs)} resources of type={resource_type.value}",
                extra={"count": len(orm_objs), "resource_type": resource_type.value}
            )
            return [self.mapper.to_read(obj) for obj in orm_objs]

        except SQLAlchemyError as e:
            self._log_error(
                "resource_list_by_type_db_error",
                f"Database error while listing resources of type={resource_type.value}",
                {"resource_type": resource_type.value, "error": str(e)}
            )
            raise RepositoryException()

    async def get_supported_types(self) -> List[str]:
        types = [rt for rt in ResourceType]
        self._log_info(
            event="resource_get_supported_types",
            msg=f"Supported resource types: {[str(t) for t in types]}",
            extra={"supported_types": types}
        )
        return types

    async def create(self, create_schema: ResourceCreateSchema, **kwargs) -> ResourceReadSchema:
        changing_user_id = kwargs.get("changing_user_id")
        if changing_user_id is None:
            raise ValueError("changing_user_id is required")

        try:
            # Use base create
            resource = await super().create(create_schema)

            # Add initial state history
            history = ResourceStateHistory(
                resource_id=resource.id,
                old_state=resource.resource_state,
                new_state=resource.resource_state,
                description=create_schema.state_change_description or "Initial state",
                changed_by=changing_user_id,
            )
            self.session.add(history)
            await self.session.flush()

            self._log_info(
                event="resource_create_success",
                msg=f"Created resource id={resource.id}",
                extra={"resource_id": resource.id, "resource_type": resource.resource_type, "user_id": changing_user_id}
            )
            return await self.get(resource.id)


        except IntegrityViolationException:
            self._log_warning(
                event="resource_create_integrity_error",
                msg="Resource already exists",
                extra={"name": create_schema.name, "user_id": changing_user_id}
            )
            raise ResourceAlreadyExistsException("Resource with this name already exists")

        except SQLAlchemyError as e:
            self._log_error(
                "resource_create_db_error",
                "Database error during resource create",
                {"error": str(e)}
            )
            raise RepositoryException()

    async def update(self, obj_id: int, update_schema: ResourceUpdateSchema, **kwargs) -> Optional[ResourceReadSchema]:
        changing_user_id = kwargs.get("changing_user_id")
        if changing_user_id is None:
            raise ValueError("changing_user_id is required")

        try:
            stmt = select(BaseResource).where(BaseResource.id == obj_id)
            result = await self.session.execute(stmt)
            orm_obj = result.scalar_one_or_none()
            if not orm_obj:
                self._log_warning("resource_update_not_found", f"Resource with id={obj_id} not found",
                                  {"resource_id": obj_id})
                raise ResourceNotFoundException(f"Resource with id={obj_id} not found")

            old_state = orm_obj.resource_state

            await super().update(obj_id, update_schema)

            if update_schema.resource_state is not None or update_schema.state_change_description:
                new_state = update_schema.resource_state or old_state
                history = ResourceStateHistory(
                    resource_id=orm_obj.id,
                    old_state=old_state,
                    new_state=new_state,
                    description=update_schema.state_change_description or "No description",
                    changed_by=changing_user_id,
                )
                self.session.add(history)
                await self.session.flush()

            self._log_info(
                event="resource_update_success",
                msg=f"Updated resource id={obj_id}",
                extra={"resource_id": obj_id, "user_id": changing_user_id}
            )
            self.session.expire(orm_obj)

            return await self.get(obj_id)

        except IntegrityViolationException:
            self._log_warning(
                "resource_update_integrity_error",
                "Resource already exists (duplicate name)",
                {"resource_id": obj_id, "user_id": changing_user_id}
            )
            raise ResourceAlreadyExistsException("Resource with this name already exists")

        except SQLAlchemyError as e:
            self._log_error("resource_update_db_error", f"Database error while updating resource id={obj_id}",
                            {"resource_id": obj_id, "error": str(e)})
            raise RepositoryException()

    async def delete(self, obj_id: int) -> bool:
        try:
            deleted = await super().delete(obj_id)
            self._log_info(
                event="resource_delete_success",
                msg=f"Deleted resource id={obj_id}",
                extra={"resource_id": obj_id}
            )
            return deleted

        except NotFoundException:
            self._log_warning(
                event="resource_delete_not_found",
                msg=f"Resource with id={obj_id} not found",
                extra={"resource_id": obj_id}
            )
            raise ResourceNotFoundException()

        except SQLAlchemyError as e:
            self._log_error("resource_delete_db_error", f"Database error while deleting resource id={obj_id}",
                            {"resource_id": obj_id, "error": str(e)})
            raise RepositoryException()
