from fastapi import APIRouter, Depends

from app.api.dependencies.db import get_db_manager
from app.db.base_manager import AbstractDBManager

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/db")
async def db_health_check(db_manager: AbstractDBManager = Depends(get_db_manager)):
    is_connected = await db_manager.check_connection()
    return {"database_connected": is_connected}
