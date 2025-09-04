from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
        orm_obj = self.mapper.to_orm(create_schema)
        self.session.add(orm_obj)
        await self.session.flush()
        await self.session.refresh(orm_obj)
        return self.mapper.to_read(orm_obj)


    async def get(self, obj_id: int) -> Optional[DomainRead]:
        stmt = select(self.orm_model).where(self.orm_model.id == obj_id)
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()
        return self.mapper.to_read(orm_obj) if orm_obj else None


    async def list(self) -> List[DomainRead]:
        stmt = select(self.orm_model)
        result = await self.session.execute(stmt)
        orm_objs = result.scalars().all()
        return [self.mapper.to_read(obj) for obj in orm_objs]


    async def update(self, obj_id: int, update_schema: DomainUpdate) -> Optional[DomainRead]:
        stmt = select(self.orm_model).where(self.orm_model.id == obj_id)
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()
        if not orm_obj:
            return None
        self.mapper.update_orm(orm_obj, update_schema)
        await self.session.flush()
        await self.session.refresh(orm_obj)
        return self.mapper.to_read(orm_obj)


    async def delete(self, obj_id: int) -> bool:
        stmt = select(self.orm_model).where(self.orm_model.id == obj_id)
        result = await self.session.execute(stmt)
        orm_obj = result.scalar_one_or_none()
        if not orm_obj:
            return False
        await self.session.delete(orm_obj)
        return True
