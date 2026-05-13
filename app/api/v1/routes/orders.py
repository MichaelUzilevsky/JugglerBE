from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Path, HTTPException

from app.api.dependencies.auth import admin_only, get_current_user
from app.api.dependencies.services.orders import get_order_service
from app.domain.schemas.order.enums.order_status import OrderStatus
from app.domain.schemas.order.order import OrderCreate, OrderUpdate, OrderRead
from app.domain.schemas.order.public_order import OrderCreateRequest, OrderUpdateRequest
from app.domain.schemas.resource.resource import ResourceRead
from app.domain.schemas.user.enums.user_role import UserRole
from app.domain.schemas.user.user import UserRead
from app.domain.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=List[OrderRead])
async def list_orders(service: OrderService = Depends(get_order_service)):
    return await service.list_all()


@router.get("/active", response_model=List[OrderRead])
async def get_current_active_orders(service: OrderService = Depends(get_order_service)):
    return await service.get_active_orders_now()


@router.get("/range", response_model=List[OrderRead])
async def get_orders_by_range(
        start: datetime = Query(...),
        end: datetime = Query(...),
        service: OrderService = Depends(get_order_service),
):
    return await service.get_orders_by_time_range(start, end)


@router.get("/user/{user_id}", response_model=List[OrderRead])
async def get_user_orders(
        user_id: int = Path(...),
        service: OrderService = Depends(get_order_service),
        user: UserRead = Depends(get_current_user)
):
    if user.role != UserRole.ADMIN and user.id != user_id:
        raise HTTPException(status_code=403, detail="Can not fetch other users orders.")
    return await service.get_user_orders(user_id)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
        order_id: int = Path(...),
        service: OrderService = Depends(get_order_service),
):
    return await service.get(order_id)


@router.get("/range/resources", response_model=List[ResourceRead])
async def get_active_resources_in_range(
        start: datetime = Query(...),
        end: datetime = Query(...),
        service: OrderService = Depends(get_order_service),
):
    return await service.get_active_resources_in_range(start, end)


@router.post("/", response_model=OrderRead)
async def create_order(
        order_create_request: OrderCreateRequest,
        service: OrderService = Depends(get_order_service),
        _=Depends(get_current_user)
):
    order = OrderCreate.model_validate(order_create_request.model_dump())
    return await service.create_order(order)


@router.patch("/{order_id}", response_model=OrderRead)
async def update_order(
        order_id: int,
        order_update_request: OrderUpdateRequest,
        service: OrderService = Depends(get_order_service),
        user: UserRead = Depends(get_current_user)
):
    order = await service.get(order_id)
    if user.role != UserRole.ADMIN and order.user.id != user.id:
        raise HTTPException(status_code=403, detail="Cannot update orders of other users.")

    update = OrderUpdate.model_validate(order_update_request.model_dump())
    return await service.update_order(order_id, update)


@router.patch("/{order_id}/status", response_model=OrderRead)
async def change_order_status(
        order_id: int,
        new_status: OrderStatus,
        message: Optional[str] = None,
        service: OrderService = Depends(get_order_service),
        user: UserRead = Depends(get_current_user)
):
    order = await service.get(order_id)
    if user.role != UserRole.ADMIN and order.user.id != user.id:
        raise HTTPException(status_code=403, detail="Cannot change status of other users' orders.")

    return await service.change_status(order_id, new_status, changed_by_user_id=user.id, message=message)


@router.delete("/{order_id}")
async def delete_order(
        order_id: int,
        service: OrderService = Depends(get_order_service),
        admin: UserRead = Depends(admin_only)
):
    await service.delete_order(order_id, actor_id=admin.id)
    return {"detail": f"Order {order_id} deleted"}
