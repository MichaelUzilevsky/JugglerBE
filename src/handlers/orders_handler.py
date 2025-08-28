from typing import List, Optional, Type

from src import logger
from src.db.abstract.icrud import ICrud
from src.exceptions.orders_exceptions.invalid_order_status_exception import InvalidOrderStatusException
from src.exceptions.orders_exceptions.order_conflict_exception import OrderConflictException
from src.exceptions.orders_exceptions.order_not_found_exception import OrderNotFoundException
from src.exceptions.orders_exceptions.order_update_exception import OrderUpdateException
from src.exceptions.orders_exceptions.resource_not_found_exception import ResourceNotFoundException
from src.exceptions.orders_exceptions.unorderable_resource_exception import UnOrderableResourceException
from src.handlers.resources_handler import ResourcesHandler
from src.handlers.users_handler import UsersHandler
from src.models.orders.enums.order_status import OrderStatus
from src.models.orders.order import Order
from src.models.orders.rules import ORDER_PURPOSE_RULES
from src.models.resources.abstract.base_resource import BaseResource


class OrdersHandler:
    def __init__(self, crud: ICrud[Order], resources_handler: ResourcesHandler, users_handler: UsersHandler):
        """
        Initialize OrdersHandler with CRUD, resources handler, and users handler.
        """
        self._crud = crud
        self._resources_handler = resources_handler
        self._users_handler = users_handler

    async def get_orders_in_time_range(self, start, end) -> List[Order]:
        """
        Get all orders that overlap with a given time range.
        """
        orders = await self._crud.get_all({
            "start_time": {"$lt": end},
            "end_time": {"$gt": start},
        })
        logger.debug(f"[OrdersHandler] Retrieved {len(orders)} order(s) in time range {start} - {end}")
        return orders

    async def get_users_orders(self, user_id: str) -> List[Order]:
        """
        Get all orders for a specific user.
        """
        orders = await self._crud.get_all({"user_id": user_id})
        logger.debug(f"[OrdersHandler] Retrieved {len(orders)} order(s) for user '{user_id}'")
        return orders

    async def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get a single order by its ID. Raises OrderNotFoundException if not found.
        """
        order = await self._crud.get({"id": order_id})
        if not order:
            logger.error(f"[OrdersHandler] Order with id '{order_id}' not found")
            raise OrderNotFoundException(f"No Order found with '{order_id}'")
        logger.info(f"[OrdersHandler] Found order with id '{order_id}'")
        return order

    async def get_all(self) -> List[Order]:
        """
        Get all orders in the system.
        """
        orders = await self._crud.get_all()
        logger.debug(f"[OrdersHandler] Retrieved {len(orders)} total orders")
        return orders

    async def _validate_order_resources(self, order: Order):
        """
        Ensure all resources in the order exist, and can be ordered. Raises ResourceNotFoundException if not found.
        """
        for resource_id in order.resources_ids:
            resource, resource_type = await self._resources_handler.get_by_id(resource_id)

            if not resource:
                logger.error(f"[OrdersHandler] Missing resource with id '{resource_id}' in order '{order.id}'")
                raise ResourceNotFoundException(f"No Resource records found with id={resource_id}")
            allowed_states = ORDER_PURPOSE_RULES.get(order.purpose, [])
            if resource.resource_state not in allowed_states:
                raise UnOrderableResourceException(
                    f"Resource {resource.id} is in '{resource.resource_state.value}' state, "
                    f"which is not allowed for '{order.purpose.value}' purpose. "
                    f"Allowed states: {[state.value for state in allowed_states]}"
                )

    async def _check_conflicts(self, order: Order) -> List[str]:
        """
        Check for conflicting approved orders for the same resources and time range.
        return list of conflicting order ids, or [] in no conflicts found
        """
        for resource_id in order.resources_ids:
            conflicting_orders = await self._crud.get_all({
                "resources_ids": resource_id,
                "status": OrderStatus.APPROVED,
                "id": {"$ne": order.id},
                "$or": [
                    {"start_time": {"$lt": order.end_time}, "end_time": {"$gt": order.start_time}}
                ]
            })
            if conflicting_orders:
                logger.warning(f"[OrdersHandler] Conflict detected for order '{order.id}' on resource '{resource_id}'")
                return [order.id for order in conflicting_orders]
            logger.debug(f"[OrdersHandler] No conflicts detected for order '{order.id}'")
            return []

    async def create_order(self, order: Order) -> Order:
        """
        Validate and create a new order. Raises on conflict or missing resources.
        """
        await self._validate_order_resources(order)
        conflicting_orders = await self._check_conflicts(order)

        if conflicting_orders:
            order.conflicts_with = conflicting_orders

        created = await self._crud.create(order)
        if created:
            logger.info(f"[OrdersHandler] Created order with id '{created.id}'")
        else:
            logger.error(f"[OrdersHandler] Failed to create order")
        return created

    async def update_order(self, order: Order) -> bool:
        """
        Update an existing order. Validates resources and conflicts. If order in final state brings it back to pending
        """
        existing = await self.get_order(order.id)

        await self._validate_order_resources(order)

        conflicting_orders = await self._check_conflicts(order)

        if conflicting_orders:
            order.conflicts_with = conflicting_orders

        if existing.status == OrderStatus.APPROVED or existing.status == OrderStatus.REJECTED:
            order.status = OrderStatus.PENDING

        success = await self._crud.update({"id": order.id}, order)
        if success:
            logger.info(f"[OrdersHandler] Updated order '{order.id}'")
        else:
            logger.error(f"[OrdersHandler] Failed to update order '{order.id}'")
        return success

    async def modify_order_status(self, order_id: str, new_status: OrderStatus) -> Order:
        """
        Modify the status of an order. Only allowed statuses: APPROVED, REJECTED, PENDING.
        Assumes admin check was done earlier in the call stack.
        """
        order = await self.get_order(order_id)

        if new_status == OrderStatus.APPROVED:
            conflicting_orders = await self._check_conflicts(order)
            if conflicting_orders:
                raise OrderConflictException(
                    f"Cannot approve order '{order_id}'. Conflicts with already approved orders: "
                    f"{conflicting_orders}"
                )

        if new_status not in (OrderStatus.APPROVED, OrderStatus.REJECTED, OrderStatus.PENDING):
            logger.warning(f"[OrdersHandler] Unsupported status '{new_status}' for order '{order_id}'")
            raise InvalidOrderStatusException(f"Unsupported status: {new_status}")

        order.status = new_status
        success = await self._crud.update({"id": order_id}, order)

        if not success:
            logger.error(f"[OrdersHandler] Failed to update order '{order_id}' to status '{new_status}'")
            raise OrderUpdateException("Failed to update order status")

        logger.info(f"[OrdersHandler] Order '{order_id}' status updated to '{new_status}'")
        return order

    async def delete_order(self, order_id: str) -> bool:
        """
        Delete an order by its ID.
        """
        success = await self._crud.delete({"id": order_id})
        if success:
            logger.info(f"[OrdersHandler] Deleted order '{order_id}'")
        else:
            logger.error(f"[OrdersHandler] Failed to delete order '{order_id}'")
        return success

    async def get_orders_per_resource(self, resource_id: str, start, end) -> List[Order]:
        """
        Get all orders for a specific resource within a time range.
        """
        orders = await self._crud.get_all({
            "resources_ids": resource_id,
            "start_time": {"$lt": end},
            "end_time": {"$gt": start},
        })
        logger.debug(f"[OrdersHandler] Retrieved {len(orders)} order(s) for resource '{resource_id}' in range")
        return orders

    async def get_orders_by_resource_class(self, resource_type: Type[BaseResource]) -> List[Order]:
        """
        Get all orders that contain resources of a specific class/type.
        """
        resources = await self._resources_handler.get_all_by_resource_class(resource_type)
        resource_ids = [res.id for res in resources if res.id]
        orders = await self._crud.get_all({"resources_ids": {"$in": resource_ids}})
        logger.debug(f"[OrdersHandler] Retrieved {len(orders)} order(s) containing resource type "
                     f"'{resource_type.__name__}'")
        return orders
