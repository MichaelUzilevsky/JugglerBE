from typing import Generic, TypeVar, Type, List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app import logger
from app.domain.exceptions.repository_exceptions import IntegrityViolationException, RepositoryException, \
    NotFoundException

DomainRead = TypeVar("DomainRead")
DomainCreate = TypeVar("DomainCreate")
DomainUpdate = TypeVar("DomainUpdate")
ORMModel = TypeVar("ORMModel")
Mapper = TypeVar("Mapper")


class SQLAlchemyBaseRepository(Generic[DomainRead, DomainCreate, DomainUpdate, ORMModel]):
    """
        Base SQLAlchemy repository with generic CRUD methods and structured logging.
    """

    def __init__(self, session: AsyncSession, orm_model: Type[ORMModel], mapper: Mapper):
        self.session = session
        self.orm_model = orm_model
        self.mapper = mapper

    @staticmethod
    def _log_info(event: str, msg: str = None, extra: dict = None):
        logger.info(msg or event, extra={"event": event, **(extra or {})})

    @staticmethod
    def _log_warning(event: str, msg: str = None, extra: dict = None):
        logger.warning(msg or event, extra={"event": event, **(extra or {})})

    @staticmethod
    def _log_error(event: str, msg: str = None, extra: dict = None):
        logger.error(msg or event, exc_info=True, extra={"event": event, **(extra or {})})

    async def create(self, create_schema: DomainCreate) -> DomainRead:
        try:
            orm_obj = self.mapper.to_orm(create_schema)
            self.session.add(orm_obj)
            await self.session.flush()
            await self.session.refresh(orm_obj)

            self._log_info(
                event="create_success",
                msg=f"Created object with id={orm_obj.id}",
                extra={"id": orm_obj.id}
            )
            return self.mapper.to_read(orm_obj)

        except IntegrityError as e:
            self._log_warning(
                event="create_integrity_error",
                msg="Integrity violation during create",
                extra={"error": str(e), "schema": getattr(create_schema, "model_dump", lambda: str(create_schema))()}
            )
            raise IntegrityViolationException()

        except SQLAlchemyError as e:
            self._log_error(
                event="create_db_error",
                msg="Database error during create",
                extra={"error": str(e)}
            )
            raise RepositoryException()

    async def get(self, obj_id: int | str) -> Optional[DomainRead]:
        try:
            stmt = select(self.orm_model).where(self.orm_model.id == obj_id)
            result = await self.session.execute(stmt)
            orm_obj = result.scalar_one_or_none()

            if orm_obj:
                self._log_info(
                    event="get_success",
                    msg=f"Fetched object with id={obj_id}",
                    extra={"id": obj_id}
                )
            else:
                self._log_warning(
                    event="get_not_found",
                    msg=f"No object found with id={obj_id}",
                    extra={"id": obj_id}
                )
                raise NotFoundException(f"Item with id={obj_id} not found")

            return self.mapper.to_read(orm_obj) if orm_obj else None

        except SQLAlchemyError as e:
            self._log_error(
                event="get_db_error",
                msg=f"Database error while fetching object with id={obj_id}",
                extra={"id": obj_id, "error": str(e)}
            )
            raise RepositoryException()

    async def list(self) -> List[DomainRead]:
        try:
            stmt = select(self.orm_model)
            result = await self.session.execute(stmt)
            orm_objs = result.scalars().all()

            self._log_info(
                event="list_success",
                msg=f"Fetched list of {len(orm_objs)} objects",
                extra={"count": len(orm_objs)}
            )
            return [self.mapper.to_read(obj) for obj in orm_objs]

        except SQLAlchemyError as e:
            self._log_error(
                event="list_db_error",
                msg="Database error while fetching list",
                extra={"error": str(e)}
            )
            raise RepositoryException()

    async def update(self, obj_id: int | str, update_schema: DomainUpdate) -> Optional[DomainRead]:
        try:
            stmt = select(self.orm_model).where(self.orm_model.id == obj_id)
            result = await self.session.execute(stmt)
            orm_obj = result.scalar_one_or_none()

            if not orm_obj:
                self._log_warning(
                    event="update_not_found",
                    msg=f"No object found with id={obj_id} to update",
                    extra={"id": obj_id}
                )
                raise NotFoundException(f"Item with id={obj_id} not found")

            self.mapper.update_orm(orm_obj, update_schema)
            await self.session.flush()
            await self.session.refresh(orm_obj)

            self._log_info(
                event="update_success",
                msg=f"Updated object with id={obj_id}",
                extra={"id": obj_id}
            )
            return self.mapper.to_read(orm_obj)

        except IntegrityError as e:
            self._log_warning(
                event="update_integrity_error",
                msg=f"Integrity error while updating object id={obj_id}",
                extra={"id": obj_id, "error": str(e)}
            )
            raise IntegrityViolationException(str(e))

        except SQLAlchemyError as e:
            self._log_error(
                event="update_db_error",
                msg=f"Database error while updating object id={obj_id}",
                extra={"id": obj_id, "error": str(e)}
            )
            raise RepositoryException()

    async def delete(self, obj_id: int) -> bool:
        try:
            stmt = select(self.orm_model).where(self.orm_model.id == obj_id)
            result = await self.session.execute(stmt)
            orm_obj = result.scalar_one_or_none()

            if not orm_obj:
                self._log_warning(
                    event="delete_not_found",
                    msg=f"No object found with id={obj_id} to delete",
                    extra={"id": obj_id}
                )
                raise NotFoundException(f"Item with id={obj_id} not found")

            await self.session.delete(orm_obj)

            self._log_info(
                event="delete_success",
                msg=f"Deleted object with id={obj_id}",
                extra={"id": obj_id}
            )
            return True

        except SQLAlchemyError as e:
            self._log_error(
                event="delete_db_error",
                msg=f"Database error while deleting object id={obj_id}",
                extra={"id": obj_id, "error": str(e)}
            )
            raise RepositoryException()
