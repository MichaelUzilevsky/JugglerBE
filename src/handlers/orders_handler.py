from typing import List, Optional, Type

from src import logger
from src.db.abstract.icrud import ICrud
from src.exceptions.orders_exceptions.order_conflict_exception import OrderConflictException
from src.exceptions.orders_exceptions.order_not_found_exception import OrderNotFoundException
from src.exceptions.orders_exceptions.resource_not_found_exception import ResourceNotFoundException
from src.exceptions.orders_exceptions.permission_denied_exception import PermissionDeniedException
from src.models.orders.enums.order_status import OrderStatus
from src.models.orders.order import Order
from src.models.resources.abstact.base_resource import BaseResource
from src.handlers.resources_handler import ResourcesHandler
from src.handlers.users_handler import UsersHandler


class OrdersHandler:
    def __init__(self, crud: ICrud[Order], resources_handler: ResourcesHandler, users_handler: UsersHandler):
        self._crud = crud
        self._resources_handler = resources_handler
        self._users_handler = users_handler

    async def get_orders_in_time_range(self, start, end) -> List[Order]:
        orders = await self._crud.get_all({
            "start_time": {"$lt": end},
            "end_time": {"$gt": start},
        })
        logger.info(f"[OrdersHandler] Retrieved {len(orders)} order(s) in time range {start} - {end}")
        return orders

    async def get_users_orders(self, user_id: str) -> List[Order]:
        orders = await self._crud.get_all({"user_id": user_id})
        logger.info(f"[OrdersHandler] Retrieved {len(orders)} order(s) for user '{user_id}'")
        return orders

    async def get_order(self, order_id: str) -> Optional[Order]:
        order = await self._crud.get({"id": order_id})
        if not order:
            logger.warning(f"[OrdersHandler] Order with id '{order_id}' not found")
            raise OrderNotFoundException(order_id)
        logger.info(f"[OrdersHandler] Found order with id '{order_id}'")
        return order

    async def get_all(self) -> List[Order]:
        orders = await self._crud.get_all()
        logger.info(f"[OrdersHandler] Retrieved {len(orders)} total orders")
        return orders

    async def _validate_order_resources(self, order: Order):
        for resource_id in order.resources_ids:
            found = False
            for resource_class in self._resources_handler.class_to_crud.keys():
                resource = await self._resources_handler.get_by_id(resource_class, resource_id)
                if resource:
                    found = True
                    break
            if not found:
                raise ResourceNotFoundException(resource_id)

    async def _check_conflicts(self, order: Order):
        for resource_id in order.resources_ids:
            conflicting_orders = await self._crud.get_all({
                "resources_ids": resource_id,
                "status": OrderStatus.APPROVED,
                "$or": [
                    {"start_time": {"$lt": order.end_time}, "end_time": {"$gt": order.start_time}}
                ]
            })
            if conflicting_orders:
                raise OrderConflictException(resource_id)

    async def create_order(self, order: Order) -> Order:
        await self._validate_order_resources(order)
        await self._check_conflicts(order)

        created = await self._crud.create(order)
        if created:
            logger.info(f"[OrdersHandler] Created order with id '{created.id}'")
        else:
            logger.warning(f"[OrdersHandler] Failed to Create order")
        return created

    async def update_order(self, order: Order) -> bool:
        existing = await self.get_order(order.id)

        if existing.status != OrderStatus.APPROVED:
            await self._validate_order_resources(order)
            await self._check_conflicts(order)

        success = await self._crud.update({"id": order.id}, order)
        if success:
            logger.info(f"[OrdersHandler] Updated order '{order.id}'")
        else:
            logger.warning(f"[OrdersHandler] Failed to update order '{order.id}'")
        return success

    async def approve_order(self, order_id: str, user_id: str) -> bool:
        if not await self._users_handler.is_admin(user_id):
            raise PermissionDeniedException("Only admins can approve orders")

        order = await self.get_order(order_id)
        order.status = OrderStatus.APPROVED
        success = await self._crud.update({"id": order_id}, order)
        if success:
            logger.info(f"[OrdersHandler] Approved order '{order_id}'")
        else:
            logger.warning(f"[OrdersHandler] Failed to approve order '{order_id}'")
        return success

    async def reject_order(self, order_id: str, user_id: str) -> bool:
        if not await self._users_handler.is_admin(user_id):
            raise PermissionDeniedException("Only admins can reject orders")

        order = await self.get_order(order_id)
        order.status = OrderStatus.REJECTED
        success = await self._crud.update({"id": order_id}, order)
        if success:
            logger.info(f"[OrdersHandler] Rejected order '{order_id}'")
        else:
            logger.warning(f"[OrdersHandler] Failed to reject order '{order_id}'")
        return success

    async def move_order_to_pending(self, order_id: str, user_id: str) -> bool:
        if not await self._users_handler.is_admin(user_id):
            raise PermissionDeniedException("Only admins can move orders to pending")

        order = await self.get_order(order_id)
        order.status = OrderStatus.PENDING
        success = await self._crud.update({"id": order_id}, order)
        if success:
            logger.info(f"[OrdersHandler] Moved order '{order_id}' to pending")
        else:
            logger.warning(f"[OrdersHandler] Failed to move order '{order_id}' to pending")
        return success

    async def delete_order(self, order_id: str) -> bool:
        success = await self._crud.delete({"id": order_id})
        if success:
            logger.info(f"[OrdersHandler] Deleted order '{order_id}'")
        else:
            logger.warning(f"[OrdersHandler] Failed to delete order '{order_id}'")
        return success

    async def get_orders_per_resource(self, resource_id: str, start, end) -> List[Order]:
        orders = await self._crud.get_all({
            "resources_ids": resource_id,
            "start_time": {"$lt": end},
            "end_time": {"$gt": start},
        })
        logger.info(f"[OrdersHandler] Retrieved {len(orders)} order(s) for resource '{resource_id}' in range")
        return orders

    async def get_orders_by_resource_class(self, resource_type: Type[BaseResource]) -> List[Order]:
        resources = await self._resources_handler.get_all(resource_type)
        resource_ids = [res.id for res in resources if res.id]
        orders = await self._crud.get_all({"resources_ids": {"$in": resource_ids}})
        logger.info(f"[OrdersHandler] Retrieved {len(orders)} order(s) containing resource type '{resource_type.__name__}'")
        return orders
