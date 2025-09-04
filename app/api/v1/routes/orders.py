from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import logger
from app.api.dependencies.auth import get_current_user, require_admin
from app.api.dependencies.orders import get_orders_handler
from app.exceptions.orders_exceptions.invalid_order_status_exception import InvalidOrderStatusException
from app.exceptions.orders_exceptions.order_conflict_exception import OrderConflictException
from app.exceptions.orders_exceptions.order_not_found_exception import OrderNotFoundException
from app.exceptions.orders_exceptions.order_update_exception import OrderUpdateException
from app.exceptions.orders_exceptions.resource_not_found_exception import ResourceNotFoundException
from app.exceptions.orders_exceptions.unorderable_resource_exception import UnOrderableResourceException
from app.handlers.orders_handler import OrdersHandler
from app.domain.schemas.order.enums.order_status import OrderStatus
from app.models.orders.order import Order
from app.domain.schemas.user.enums.user_role import UserRole

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=List[Order])
async def get_all_orders(
        handler: OrdersHandler = Depends(get_orders_handler),
        _=Depends(get_current_user)
):
    return await handler.get_all()


@router.get("/active", response_model=List[Order])
async def get_current_orders(
        handler: OrdersHandler = Depends(get_orders_handler),
        _=Depends(get_current_user)
):
    now = datetime.now()
    all_orders = await handler.get_orders_in_time_range(start=now, end=now)
    return [order for order in all_orders if order.status == OrderStatus.APPROVED]


@router.get("/by-time-range", response_model=List[Order])
async def get_orders_in_range(
        start: datetime = Query(...),
        end: datetime = Query(...),
        handler: OrdersHandler = Depends(get_orders_handler),
        _=Depends(get_current_user)
):
    return await handler.get_orders_in_time_range(start=start, end=end)


@router.get("/user/{user_id}", response_model=List[Order])
async def get_user_orders(
        user_id: str,
        handler: OrdersHandler = Depends(get_orders_handler),
        requesting_user=Depends(get_current_user)
):
    if user_id != requesting_user.id and requesting_user.role != UserRole.ADMIN:
        logger.warning(
            f"User with user_id='{requesting_user.id}' tried accessing other user's (user_id='{user_id}') orders")
        raise HTTPException(status_code=403, detail="Not authorized to access this user orders")
    return await handler.get_users_orders(user_id)


@router.post("/", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(
        order: Order,
        handler: OrdersHandler = Depends(get_orders_handler),
        _=Depends(get_current_user)

):
    try:
        return await handler.create_order(order)
    except (OrderConflictException,
            ResourceNotFoundException,
            UnOrderableResourceException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/update", response_model=Order)
async def update_order(
        order: Order,
        handler: OrdersHandler = Depends(get_orders_handler),
        requesting_user=Depends(get_current_user)
):
    if order.user_id != requesting_user.id and requesting_user.role != UserRole.ADMIN:
        logger.warning(
            f"User with user_id='{requesting_user.id}' tried updating other user's (user_id='{order.user_id}') order")
        raise HTTPException(status_code=403, detail="Not authorized to modify this order")
    try:
        existing_order = await handler.get_order(order.id)
        order.status = existing_order.status
        success = await handler.update_order(order)
        if not success:
            raise HTTPException(status_code=500, detail="Order update failed")
        return order
    except (OrderConflictException,
            ResourceNotFoundException,
            OrderNotFoundException,
            UnOrderableResourceException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{order_id}/approve", response_model=Order)
async def approve_order(
        order_id: str,
        handler: OrdersHandler = Depends(get_orders_handler),
        _=Depends(require_admin)
):
    try:
        return await handler.modify_order_status(order_id, OrderStatus.APPROVED)
    except (OrderNotFoundException, OrderConflictException, InvalidOrderStatusException, OrderUpdateException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{order_id}/reject", response_model=Order)
async def reject_order(
        order_id: str,
        handler: OrdersHandler = Depends(get_orders_handler),
        _=Depends(require_admin)
):
    try:
        return await handler.modify_order_status(order_id, OrderStatus.REJECTED)
    except (OrderNotFoundException, InvalidOrderStatusException, OrderUpdateException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{order_id}/pending", response_model=Order)
async def set_order_pending(
        order_id: str,
        handler: OrdersHandler = Depends(get_orders_handler),
        _=Depends(require_admin)

):
    try:
        return await handler.modify_order_status(order_id, OrderStatus.PENDING)
    except (OrderNotFoundException, InvalidOrderStatusException, OrderUpdateException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
        order_id: str,
        handler: OrdersHandler = Depends(get_orders_handler),
        requesting_user=Depends(get_current_user)
):
    order = await handler.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"No order with order_id='{order_id}' was found")

    if order.user_id != requesting_user.id and requesting_user.role != UserRole.ADMIN:
        logger.warning(
            f"User with user_id='{requesting_user.id}' tried deleting other user's (user_id='{order.user_id}') order")
        raise HTTPException(status_code=403, detail="Not authorized to delete this order")

    try:
        deleted = await handler.delete_order(order_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Failed to delete order")
    except OrderNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
