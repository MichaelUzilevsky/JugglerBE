from typing import Generic, TypeVar, Type, List, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app import logger
from app.infrastructure.exceptions.exceptions import IntegrityViolationException, RepositoryException, NotFoundException

DomainRead = TypeVar("DomainRead")
DomainCreate = TypeVar("DomainCreate")
DomainUpdate = TypeVar("DomainUpdate")
ORMModel = TypeVar("ORMModel")
Mapper = TypeVar("Mapper")


class SQLAlchemyBaseRepository(Generic[DomainRead, DomainCreate, DomainUpdate, ORMModel]):
    """
    Base SQLAlchemy repository with generic CRUD methods.
    """

    def __init__(self, session: AsyncSession, orm_model: Type[ORMModel], mapper: Mapper):
        self.session = session
        self.orm_model = orm_model
        self.mapper = mapper

    async def create(self, create_schema: DomainCreate) -> DomainRead:
        try:
            orm_obj = self.mapper.to_orm(create_schema)
            self.session.add(orm_obj)
            await self.session.flush()
            await self.session.refresh(orm_obj)
            return self.mapper.to_read(orm_obj)

        except IntegrityError as e:
            logger.warning(f"Integrity error during create. {str(e)}")
            raise IntegrityViolationException(str(e))

        except SQLAlchemyError as e:
            logger.error(f"DB error during create. {str(e)}")
            raise RepositoryException("Database error")


    async def get(self, obj_id: int) -> Optional[DomainRead]:
        try:
            stmt = select(self.orm_model).where(self.orm_model.id == obj_id)
            result = await self.session.execute(stmt)
            orm_obj = result.scalar_one_or_none()
            return self.mapper.to_read(orm_obj) if orm_obj else None

        except SQLAlchemyError as e:
            logger.error(f"DB error during get. id='{obj_id}' error='{str(e)}'")
            raise RepositoryException("Database error")


    async def list(self) -> List[DomainRead]:
        try:
            stmt = select(self.orm_model)
            result = await self.session.execute(stmt)
            orm_objs = result.scalars().all()
            return [self.mapper.to_read(obj) for obj in orm_objs]

        except SQLAlchemyError as e:
            logger.error(f"DB error during list. error='{str(e)}'")
            raise RepositoryException("Database error")



    async def update(self, obj_id: int, update_schema: DomainUpdate) -> Optional[DomainRead]:
        try:
            stmt = select(self.orm_model).where(self.orm_model.id == obj_id)
            result = await self.session.execute(stmt)
            orm_obj = result.scalar_one_or_none()
            if not orm_obj:
                return None
            self.mapper.update_orm(orm_obj, update_schema)
            await self.session.flush()
            await self.session.refresh(orm_obj)
            return self.mapper.to_read(orm_obj)

        except IntegrityError as e:
            logger.warning(f"Integrity error during update. id='{obj_id}' error='{str(e)}'")
            raise IntegrityViolationException(str(e))

        except SQLAlchemyError as e:
            logger.error(f"DB error during update. id='{obj_id}' error='{str(e)}'")
            raise RepositoryException("Database error")


    async def delete(self, obj_id: int) -> bool:
        try:
            stmt = select(self.orm_model).where(self.orm_model.id == obj_id)
            result = await self.session.execute(stmt)
            orm_obj = result.scalar_one_or_none()
            if not orm_obj:
                raise NotFoundException(f"{self.orm_model} with id {obj_id} not found")
            await self.session.delete(orm_obj)
            return True

        except SQLAlchemyError as e:
            logger.error(f"DB error during delete. id='{obj_id}' error='{str(e)}'")
            raise RepositoryException("Database error")