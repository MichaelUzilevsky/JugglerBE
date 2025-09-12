from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sqlalchemy.manager import SQLAlchemyManager

db_manager = SQLAlchemyManager()

async def get_session() -> AsyncSession:
    async with db_manager.get_session() as session:
        try:
            yield session
            await session.commit()  # commit if no exception
        except:
            await session.rollback()
            raise
