from fastapi import Request, Depends

from app.db.base_manager import AbstractDBManager


async def get_db_manager(request: Request) -> AbstractDBManager:
    return request.app.state.db_manager


async def get_connection(db_manager: AbstractDBManager = Depends(get_db_manager)):
    async with db_manager.get_connection() as conn:
        async with db_manager.transaction(conn) as tx_conn:
            yield tx_conn
