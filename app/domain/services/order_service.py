from datetime import datetime
from typing import List, Optional

from app import logger
from app.domain.exceptions.repository_exceptions import IntegrityViolationException, RepositoryException, \
    NotFoundException
from app.domain.repositories.iorder_repository import IOrderRepository
from app.domain.schemas.order.enums.order_purpose import OrderPurpose
from app.domain.schemas.order.enums.order_status import OrderStatus
from app.domain.schemas.order.legal_order_status_transitions import legal_transitions
from app.domain.schemas.order.order import OrderCreate, OrderUpdate, OrderRead
from app.domain.schemas.order.purpose_to_allowed_states import PURPOSE_TO_ALLOWED_STATES
from app.domain.schemas.resource.resource import ResourceRead
from app.domain.services.resource_service import ResourceService
from app.domain.services.user_service import UserService
from app.exceptions.orders_exceptions.orders_exceptions import OrderValidationException, OrderNotFoundException, \
    OrderConflictException
from app.exceptions.resources_exceptions.resources_exceptions import ResourceNotFoundException
from app.exceptions.users_exceptions.users_exceptions import UserNotFoundException


class OrderService:
    """
    Order service: validates inputs (user/resource existence, time ranges),
    orchestrates across user/resource services and the order repository,
    and translates repository exceptions into domain exceptions.
    """

    def __init__(
            self,
            order_repo: IOrderRepository,
            user_service: UserService,
            resource_service: ResourceService,
    ):
        self.order_repo = order_repo
        self.user_service = user_service
        self.resource_service = resource_service

    async def list_all(self) -> List[OrderRead]:
        try:
            orders = await self.order_repo.list()
            logger.info(
                "order_list_all_success",
                extra={"count": len(orders), "description": f"Fetched all orders, count={len(orders)}"}
            )
            return orders
        except RepositoryException as e:
            logger.error(
                "order_list_all_db_error",
                exc_info=True,
                extra={"description": "Failed to list all orders", "error": str(e)}
            )
            raise

    async def get_active_orders_now(self) -> List[OrderRead]:
        now = datetime.now()
        try:
            orders = await self.order_repo.get_orders_in_time_range(now, now)
            active_orders = [o for o in orders if o.status == OrderStatus.APPROVED]
            logger.info(
                "order_list_active_now_success",
                extra={"count": len(active_orders),
                       "description": f"Fetched {len(active_orders)} active approved orders"}
            )
            return active_orders
        except RepositoryException as e:
            logger.error(
                "order_list_active_now_db_error",
                exc_info=True,
                extra={"description": "Failed to fetch active orders", "error": str(e)}
            )
            raise

    async def get_orders_by_time_range(self, start: datetime, end: datetime) -> List[OrderRead]:
        if start >= end:
            raise OrderValidationException("Start time must be before end time")
        try:
            orders = await self.order_repo.get_orders_in_time_range(start, end)
            logger.info(
                "order_list_time_range_success",
                extra={"count": len(orders), "description": f"Fetched {len(orders)} orders between {start} and {end}"}
            )
            return orders
        except RepositoryException as e:
            logger.error(
                "order_list_time_range_db_error",
                exc_info=True,
                extra={"description": f"Failed to fetch orders between {start} and {end}", "error": str(e)}
            )
            raise

    async def get_user_orders(self, user_id: int) -> List[OrderRead]:
        try:
            await self.user_service.user_repo.get(user_id)
            orders = await self.order_repo.get_users_orders(user_id)
            logger.info(
                "order_list_by_user_success",
                extra={"count": len(orders), "user_id": user_id,
                       "description": f"Fetched {len(orders)} orders for user_id={user_id}"}
            )
            return orders

        except NotFoundException:
            logger.warning(
                "order_list_by_user_not_found",
                extra={"user_id": user_id, "description": f"User with id={user_id} not found"}
            )
            raise UserNotFoundException(f"User with id={user_id} not found")

        except RepositoryException as e:
            logger.error(
                "order_list_by_user_db_error",
                exc_info=True,
                extra={"user_id": user_id, "description": "Failed to fetch orders for user", "error": str(e)}
            )
            raise

    async def get(self, order_id: int) -> OrderRead:
        try:
            order = await self.order_repo.get(order_id)
            logger.info(
                "order_get_success",
                extra={"order_id": order_id, "description": f"Fetched order id={order_id}"}
            )
            return order

        except NotFoundException:
            logger.warning(
                "order_get_not_found",
                extra={"order_id": order_id, "description": f"Order with id={order_id} not found"}
            )
            raise OrderNotFoundException(f"Order with id={order_id} not found")

    async def get_active_resources_in_range(self, start: datetime, end: datetime) -> List[ResourceRead]:
        """Return resources that belong to approved orders overlapping a given time range."""
        if start >= end:
            raise OrderValidationException("Start time must be before end time")
        orders = await self.order_repo.get_orders_in_time_range(start, end)
        active_orders = [o for o in orders if o.status == OrderStatus.APPROVED]
        resources = []
        seen_ids = set()
        for order in active_orders:
            for resource in order.resources:
                if resource.id not in seen_ids:
                    seen_ids.add(resource.id)
                    resources.append(resource)
        logger.info(
            "order_active_resources_in_range_success",
            extra={"count": len(resources),
                   "description": f"Fetched {len(resources)} active resources in range {start} - {end}"}
        )
        return resources

    async def _validate_resources_for_purpose(self, purpose: OrderPurpose, resource_ids: List[int]) -> None:
        """Ensure all resources exist and match allowed states for the order purpose."""
        allowed_states = PURPOSE_TO_ALLOWED_STATES[purpose]

        for rid in resource_ids:
            try:
                resource_with_state = await self.resource_service.get(rid)
            except ResourceNotFoundException:
                logger.warning(
                    "order_resource_not_found",
                    extra={"resource_id": rid, "description": f"Resource with id={rid} not found"}
                )
                raise ResourceNotFoundException(f"Resource with id={rid} not found")

            state = resource_with_state.resource_state if resource_with_state else None

            if state not in allowed_states:
                logger.warning(
                    "order_resource_invalid_state",
                    extra={"resource_id": rid,
                           "description": f"Resource id={rid} in state={state} not allowed for purpose={purpose}"}
                )
                raise OrderValidationException(
                    f"Resource id={rid} in state={state} "
                    f"is not allowed for order purpose={purpose}"
                )

    async def create_order(self, order_create: OrderCreate) -> OrderRead:
        try:
            await self.user_service.user_repo.get(order_create.user_id)

            if order_create.start_time >= order_create.end_time:
                raise OrderValidationException("Start time must be before end time")

            await self._validate_resources_for_purpose(order_create.purpose, order_create.resource_ids)

            created = await self.order_repo.create(order_create)

            logger.info(
                "order_create_success",
                extra={"order_id": created.id, "user_id": order_create.user_id,
                       "description": f"Created order id={created.id}"}
            )

            return created

        except NotFoundException:
            logger.warning(
                "order_create_user_not_found",
                extra={"user_id": order_create.user_id, "description": f"User with id={order_create.user_id} not found"}
            )
            raise UserNotFoundException(f"User with id={order_create.user_id} not found")

        except IntegrityViolationException as e:
            logger.warning(
                "order_create_integrity_error",
                exc_info=True,
                extra={"user_id": order_create.user_id, "resource_ids": order_create.resource_ids,
                       "description": "Integrity violation during order creation", "error": str(e)}
            )
            raise OrderValidationException("Order failed integrity checks")

        except RepositoryException as e:
            logger.error(
                "order_create_db_error",
                exc_info=True,
                extra={"user_id": order_create.user_id, "description": "Database error while creating order",
                       "error": str(e)}
            )
            raise

    async def update_order(self, order_id: int, update: OrderUpdate) -> OrderRead:
        try:
            if update.user_id is not None:
                await self.user_service.user_repo.get(update.user_id)

            # validate times
            if update.start_time and update.end_time:
                if update.start_time >= update.end_time:
                    raise OrderValidationException("Start time must be before end time")

            if update.resource_ids is not None:
                purpose = update.purpose
                if purpose is None:
                    existing_order = await self.order_repo.get(order_id)
                    purpose = existing_order.purpose
                await self._validate_resources_for_purpose(purpose, update.resource_ids)

            updated = await self.order_repo.update(order_id, update)

            # if the order was approved, editing moves it back to pending
            if updated.status == OrderStatus.APPROVED:
                logger.info(f"Order id={order_id} was approved but got updated, moving to Pending")
                updated = await self.order_repo.update(
                    order_id,
                    OrderUpdate(status=OrderStatus.PENDING, message="Edited after approval, requires re-approval")
                )

            logger.info(
                "order_update_success",
                extra={"order_id": order_id, "user_id": update.user_id, "description": f"Updated order id={order_id}"}
            )
            return updated

        except NotFoundException as e:
            if str(order_id) in str(e):
                logger.warning(
                    "order_update_not_found",
                    extra={"order_id": order_id, "description": f"Order with id={order_id} not found"}
                )
                raise OrderNotFoundException(f"Order with id={order_id} not found")
            elif str(update.user_id) in str(e):
                logger.warning(
                    "order_create_user_not_found",
                    extra={"user_id": update.user_id, "description": f"User with id={update.user_id} not found"}
                )
                raise UserNotFoundException(f"User with id={update.user_id} not found")

        except IntegrityViolationException as e:
            logger.warning(f"Order update integrity error for id={order_id}: {e}")
            raise OrderValidationException("Order update failed integrity checks")

    async def _check_conflicts(self, order: OrderRead) -> None:
        """Ensure no conflicting approved orders overlap in time with shared resources."""
        overlapping_orders = await self.order_repo.get_orders_in_time_range(order.start_time, order.end_time)
        for other in overlapping_orders:
            if other.id == order.id or other.status != OrderStatus.APPROVED:
                continue
            # check resource intersection
            shared = {r.id for r in order.resources} & {r.id for r in other.resources}
            if shared:
                logger.warning(
                    "order_conflict_detected",
                    extra={
                        "order_id": order.id,
                        "conflicting_order_id": other.id,
                        "shared_resources": list(shared),
                        "description": f"Order id={order.id} conflicts with order id={other.id} "
                                       f"overlapping resources: {list(shared)}"
                    }
                )
                raise OrderConflictException(
                    f"Conflict with order id={other.id}, overlapping resources {list(shared)}"
                )

    async def change_status(
            self, order_id: int, new_status: OrderStatus, changed_by_user_id: int, message: Optional[str] = None
    ) -> OrderRead:
        try:
            order = await self.order_repo.get(order_id)

            await self.user_service.user_repo.get(changed_by_user_id)

            if new_status not in legal_transitions.get(order.status, []):
                logger.warning(
                    "order_status_change_illegal",
                    extra={"order_id": order_id, "old_status": order.status, "new_status": new_status,
                           "description": f"Illegal status transition {order.status} -> {new_status}"}
                )
                raise OrderValidationException(f"Illegal status transition from {order.status} to {new_status}")

            if new_status == OrderStatus.APPROVED:
                await self._check_conflicts(order)

            updated = await self.order_repo.update(
                order_id,
                OrderUpdate(status=new_status, message=message, user_id=changed_by_user_id)
            )

            logger.info(
                "order_status_change_success",
                extra={"order_id": order_id, "old_status": order.status, "new_status": new_status,
                       "changed_by": changed_by_user_id,
                       "description": f"Order id={order_id} status changed {order.status} -> {new_status}"}
            )
            return updated

        except NotFoundException as e:
            if str(order_id) in str(e):
                logger.warning(
                    "order_update_not_found",
                    extra={"order_id": order_id, "description": f"Order with id={order_id} not found"}
                )
                raise OrderNotFoundException(f"Order with id={order_id} not found")
            elif str(changed_by_user_id) in str(e):
                logger.warning(
                    "order_create_user_not_found",
                    extra={"user_id": changed_by_user_id, "description": f"User with id={changed_by_user_id} not found"}
                )
                raise UserNotFoundException(f"User with id={changed_by_user_id} not found")

    async def delete_order(self, order_id: int) -> None:
        try:
            deleted = await self.order_repo.delete(order_id)
            if not deleted:
                logger.warning(
                    "order_delete_not_found",
                    extra={"order_id": order_id, "description": f"Order with id={order_id} not found"}
                )
                raise OrderNotFoundException(f"Order with id={order_id} not found")
            logger.info(
                "order_delete_success",
                extra={"order_id": order_id, "description": f"Deleted order id={order_id}"}
            )
        except RepositoryException as e:
            logger.error(
                "order_delete_db_error",
                extra={"order_id": order_id, "description": "Database error while deleting order", "error": str(e)}
            )
            raise
