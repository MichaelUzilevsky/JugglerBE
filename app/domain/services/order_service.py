from datetime import datetime
from typing import List, Optional

from app import logger
from app.domain.exceptions.repository_exceptions import IntegrityViolationException, NotFoundException
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
        orders = await self.order_repo.list()
        logger.info(
            f"Fetched all orders, count={len(orders)}",
            extra={"event": "order_list_all_success", "count": len(orders)}
        )
        return orders

    async def get_active_orders_now(self) -> List[OrderRead]:
        now = datetime.now()
        orders = await self.order_repo.get_orders_in_time_range(now, now)
        active_orders = [o for o in orders if o.status == OrderStatus.APPROVED]
        logger.info(
            f"Fetched {len(active_orders)} active approved orders",
            extra={"event": "order_list_active_now_success", "count": len(active_orders)}
        )
        return active_orders

    async def get_orders_by_time_range(self, start: datetime, end: datetime) -> List[OrderRead]:
        if start >= end:
            raise OrderValidationException("Start time must be before end time")
        orders = await self.order_repo.get_orders_in_time_range(start, end)
        logger.info(
            f"Fetched {len(orders)} orders between {start} and {end}",
            extra={"event": "order_list_time_range_success", "count": len(orders),
                   "start_time": str(start), "end_time": str(end)}
        )
        return orders

    async def get_user_orders(self, user_id: int) -> List[OrderRead]:
        try:
            await self.user_service.user_repo.get(user_id)
            orders = await self.order_repo.get_users_orders(user_id)
            logger.info(
                f"Fetched {len(orders)} orders for user_id={user_id}",
                extra={"event": "order_list_by_user_success", "count": len(orders), "user_id": user_id}
            )
            return orders

        except NotFoundException:
            logger.warning(
                f"Cannot list orders: user_id={user_id} not found",
                extra={"event": "order_list_by_user_not_found", "user_id": user_id}
            )
            raise UserNotFoundException(f"User with id={user_id} not found")

    async def get(self, order_id: int) -> OrderRead:
        try:
            order = await self.order_repo.get(order_id)
            logger.info(
                f"Fetched order id={order_id}",
                extra={"event": "order_get_success", "order_id": order_id}
            )
            return order

        except NotFoundException:
            logger.warning(
                f"Order id={order_id} not found",
                extra={"event": "order_get_not_found", "order_id": order_id}
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
            f"Fetched {len(resources)} active resources in range {start} - {end}",
            extra={"event": "order_active_resources_in_range_success", "count": len(resources),
                   "start_time": str(start), "end_time": str(end)}
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
                    f"Order validation failed: resource id={rid} not found",
                    extra={"event": "order_resource_not_found", "resource_id": rid}
                )
                raise ResourceNotFoundException(f"Resource with id={rid} not found")

            state = resource_with_state.resource_state if resource_with_state else None

            if state not in allowed_states:
                logger.warning(
                    f"Order validation failed: resource id={rid} state='{state}' not allowed for purpose='{purpose}'",
                    extra={"event": "order_resource_invalid_state", "resource_id": rid,
                           "resource_state": str(state), "order_purpose": str(purpose),
                           "allowed_states": [str(s) for s in allowed_states]}
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
                f"Order id={created.id} created for user_id={order_create.user_id}",
                extra={"event": "order_create_success", "order_id": created.id, "user_id": order_create.user_id,
                       "purpose": order_create.purpose.value, "resource_ids": order_create.resource_ids}
            )

            return created

        except NotFoundException:
            logger.warning(
                f"Order creation failed: user_id={order_create.user_id} not found",
                extra={"event": "order_create_user_not_found", "user_id": order_create.user_id}
            )
            raise UserNotFoundException(f"User with id={order_create.user_id} not found")

        except IntegrityViolationException as e:
            logger.warning(
                f"Order creation failed: integrity violation for user_id={order_create.user_id}",
                extra={"event": "order_create_integrity_error", "user_id": order_create.user_id,
                       "resource_ids": order_create.resource_ids, "error": str(e)}
            )
            raise OrderValidationException("Order failed integrity checks")

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
                logger.info(
                    f"Order id={order_id} was approved but got updated, moving to Pending",
                    extra={"event": "order_status_auto_pending", "order_id": order_id,
                           "reason": "edited_after_approval"}
                )
                updated = await self.order_repo.update(
                    order_id,
                    OrderUpdate(status=OrderStatus.PENDING, message="Edited after approval, requires re-approval")
                )

            logger.info(
                f"Order id={order_id} updated",
                extra={"event": "order_update_success", "order_id": order_id, "user_id": update.user_id}
            )
            return updated

        except NotFoundException as e:
            if str(order_id) in str(e):
                logger.warning(
                    f"Order update failed: order id={order_id} not found",
                    extra={"event": "order_update_not_found", "order_id": order_id}
                )
                raise OrderNotFoundException(f"Order with id={order_id} not found")
            elif str(update.user_id) in str(e):
                logger.warning(
                    f"Order update failed: user_id={update.user_id} not found",
                    extra={"event": "order_update_user_not_found", "user_id": update.user_id}
                )
                raise UserNotFoundException(f"User with id={update.user_id} not found")

        except IntegrityViolationException as e:
            logger.warning(
                f"Order update integrity error for id={order_id}",
                extra={"event": "order_update_integrity_error", "order_id": order_id, "error": str(e)}
            )
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
                    f"Order id={order.id} conflicts with order id={other.id}, "
                    f"shared resources: {list(shared)}",
                    extra={
                        "event": "order_conflict_detected",
                        "order_id": order.id,
                        "conflicting_order_id": other.id,
                        "shared_resource_ids": list(shared),
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
                    f"Illegal status transition for order id={order_id}: "
                    f"{order.status.value} -> {new_status.value}",
                    extra={"event": "order_status_change_illegal", "order_id": order_id,
                           "old_status": order.status.value, "new_status": new_status.value,
                           "actor_id": changed_by_user_id}
                )
                raise OrderValidationException(f"Illegal status transition from {order.status} to {new_status}")

            if new_status == OrderStatus.APPROVED:
                await self._check_conflicts(order)

            updated = await self.order_repo.update(
                order_id,
                OrderUpdate(status=new_status, message=message, user_id=changed_by_user_id)
            )

            logger.info(
                f"Order id={order_id} status changed: {order.status.value} -> {new_status.value}",
                extra={"event": "order_status_change_success", "order_id": order_id,
                       "old_status": order.status.value, "new_status": new_status.value,
                       "actor_id": changed_by_user_id}
            )
            return updated

        except NotFoundException as e:
            if str(order_id) in str(e):
                logger.warning(
                    f"Status change failed: order id={order_id} not found",
                    extra={"event": "order_status_change_not_found", "order_id": order_id}
                )
                raise OrderNotFoundException(f"Order with id={order_id} not found")
            elif str(changed_by_user_id) in str(e):
                logger.warning(
                    f"Status change failed: user_id={changed_by_user_id} not found",
                    extra={"event": "order_status_change_user_not_found", "user_id": changed_by_user_id}
                )
                raise UserNotFoundException(f"User with id={changed_by_user_id} not found")

    async def delete_order(self, order_id: int, actor_id: int = None) -> None:
        try:
            deleted = await self.order_repo.delete(order_id)
            if not deleted:
                logger.warning(
                    f"Order delete failed: order id={order_id} not found",
                    extra={"event": "order_delete_not_found", "order_id": order_id, "actor_id": actor_id}
                )
                raise OrderNotFoundException(f"Order with id={order_id} not found")
            logger.info(
                f"Order id={order_id} deleted",
                extra={"event": "order_delete_success", "order_id": order_id, "actor_id": actor_id}
            )
        except NotFoundException:
            logger.warning(
                f"Order delete failed: order id={order_id} not found",
                extra={"event": "order_delete_not_found", "order_id": order_id, "actor_id": actor_id}
            )
            raise OrderNotFoundException(f"Order with id={order_id} not found")
