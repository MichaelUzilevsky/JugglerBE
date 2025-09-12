from typing import List, Optional
from datetime import datetime

from app import logger
from app.domain.schemas.order.enums.order_purpose import OrderPurpose
from app.domain.schemas.order.legal_order_status_transitions import legal_transitions
from app.domain.schemas.order.order import OrderCreate, OrderUpdate, OrderRead
from app.domain.schemas.order.enums.order_status import OrderStatus
from app.domain.repositories.iorder_repository import IOrderRepository
from app.domain.schemas.order.purpose_to_allowed_states import PURPOSE_TO_ALLOWED_STATES
from app.domain.schemas.resource.resource import ResourceRead
from app.domain.services.resource_service import ResourceService
from app.domain.services.user_service import UserService
from app.exceptions.orders_exceptions.order_conflict_exception import OrderConflictException

from app.exceptions.orders_exceptions.order_not_found_exception import OrderNotFoundException
from app.exceptions.orders_exceptions.order_validation_exception import OrderValidationException
from app.exceptions.orders_exceptions.resource_not_found_exception import ResourceNotFoundException
from app.exceptions.users_exceptions.user_not_found_exception import UserNotFoundException

from app.infrastructure.exceptions.exceptions import IntegrityViolationException, RepositoryException


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
        return await self.order_repo.list()

    async def get_active_orders_now(self) -> List[OrderRead]:
        """Return orders whose timeframe includes now AND have status APPROVED."""
        now = datetime.now()
        # repo returns orders overlapping the time range
        orders = await self.order_repo.get_orders_in_time_range(now, now)
        return [o for o in orders if o.status == OrderStatus.APPROVED]

    async def get_orders_by_time_range(self, start: datetime, end: datetime) -> List[OrderRead]:
        if start >= end:
            raise OrderValidationException("Start time must be before end time")
        return await self.order_repo.get_orders_in_time_range(start, end)

    async def get_user_orders(self, user_id: int) -> List[OrderRead]:
        # validate user exists (use repo.get to avoid coupling to orm)
        user = await self.user_service.user_repo.get(user_id)
        if not user:
            raise UserNotFoundException(f"User with id={user_id} not found")
        return await self.order_repo.get_users_orders(user_id)

    async def get(self, order_id: int) -> OrderRead:
        order = await self.order_repo.get(order_id)
        if not order:
            raise OrderNotFoundException(f"Order with id={order_id} not found")
        return order

    async def get_active_resources_in_range(
            self, start: datetime, end: datetime
    ) -> List[ResourceRead]:
        """Return resources that belong to approved orders overlapping a given time range."""
        if start >= end:
            raise OrderValidationException("Start time must be before end time")

        orders = await self.order_repo.get_orders_in_time_range(start, end)
        active_orders = [o for o in orders if o.status == OrderStatus.APPROVED]

        # Flatten resources from all active orders
        resources = []
        seen_ids = set()
        for order in active_orders:
            for resource in order.resources:
                if resource.id not in seen_ids:
                    seen_ids.add(resource.id)
                    resources.append(resource)

        return resources

    async def _validate_resources_for_purpose(self, purpose: OrderPurpose, resource_ids: List[int]) -> None:
        """Ensure all resources exist and match allowed states for the order purpose."""
        allowed_states = PURPOSE_TO_ALLOWED_STATES[purpose]

        for rid in resource_ids:
            try:
                resource = await self.resource_service.get(rid)
            except ResourceNotFoundException:
                raise ResourceNotFoundException(f"Resource with id={rid} not found")

            # use latest state
            resource_with_state = await self.resource_service.get_with_latest_state(rid)
            state = resource_with_state.resource_state if resource_with_state else None

            if state not in allowed_states:
                raise OrderValidationException(
                    f"Resource id={rid} in state={state} "
                    f"is not allowed for order purpose={purpose}"
                )

    async def create_order(self, order_create: OrderCreate) -> OrderRead:
        # validate user exists
        user = await self.user_service.user_repo.get(order_create.user_id)
        if not user:
            raise UserNotFoundException(f"User with id={order_create.user_id} not found")

        # validate time window
        if order_create.start_time >= order_create.end_time:
            raise OrderValidationException("Start time must be before end time")

        # validate resources
        await self._validate_resources_for_purpose(order_create.purpose, order_create.resource_ids)

        try:
            created = await self.order_repo.create(order_create)
            logger.info(f"Order created id={created.id}, user_id={order_create.user_id}")
            return created
        except IntegrityViolationException as e:
            logger.warning(f"Order create integrity error: {e}")
            raise OrderValidationException("Order failed integrity checks")
        except RepositoryException as e:
            logger.error(f"Order create repository error: {e}")
            raise

    async def update_order(self, order_id: int, update: OrderUpdate) -> OrderRead:
        # validate user (if being changed)
        if update.user_id is not None:
            user = await self.user_service.user_repo.get(update.user_id)
            if not user:
                raise UserNotFoundException(f"User with id={update.user_id} not found")

        # validate times
        if update.start_time and update.end_time:
            if update.start_time >= update.end_time:
                raise OrderValidationException("Start time must be before end time")

        # validate resources (if being changed)
        if update.resource_ids is not None and update.purpose is not None:
            await self._validate_resources_for_purpose(update.purpose, update.resource_ids)
        elif update.resource_ids is not None:
            # fetch order to check its current purpose
            existing_order = await self.order_repo.get(order_id)
            if not existing_order:
                raise OrderNotFoundException(f"Order with id={order_id} not found")
            await self._validate_resources_for_purpose(existing_order.purpose, update.resource_ids)

        try:
            updated = await self.order_repo.update(order_id, update)

            if not updated:
                raise OrderNotFoundException(f"Order with id={order_id} not found")

            # if the order was approved, editing moves it back to pending
            if updated.status == OrderStatus.APPROVED:
                logger.info(f"Order id={order_id} was approved but got updated, moving to Pending")
                updated = await self.order_repo.update(
                    order_id,
                    OrderUpdate(status=OrderStatus.PENDING, message="Edited after approval, requires re-approval")
                )
        except IntegrityViolationException as e:
            logger.warning(f"Order update integrity error for id={order_id}: {e}")
            raise OrderValidationException("Order update failed integrity checks")
        except RepositoryException:
            raise

        logger.info(f"Order id={order_id} updated")
        return updated

    async def _check_conflicts(self, order: OrderRead) -> None:
        """Ensure no conflicting approved orders overlap in time with shared resources."""
        overlapping_orders = await self.order_repo.get_orders_in_time_range(order.start_time, order.end_time)
        for other in overlapping_orders:
            if other.id == order.id or other.status != OrderStatus.APPROVED:
                continue
            # check resource intersection
            shared = {r.id for r in order.resources} & {r.id for r in other.resources}
            if shared:
                raise OrderConflictException(
                    f"Conflict with order id={other.id}, overlapping resources {list(shared)}"
                )

    async def change_status(
            self, order_id: int, new_status: OrderStatus, changed_by_user_id: int, message: Optional[str] = None
    ) -> OrderRead:

        # ensure order exists
        order = await self.order_repo.get(order_id)
        if not order:
            raise OrderNotFoundException(f"Order with id={order_id} not found")

        # ensure user exists
        user = await self.user_service.user_repo.get(changed_by_user_id)
        if not user:
            raise UserNotFoundException(f"User with id={changed_by_user_id} not found")

        if new_status not in legal_transitions.get(order.status, []):
            raise OrderValidationException(f"Illegal status transition from {order.status} to {new_status}")

        # check conflicts if moving to approved
        if new_status == OrderStatus.APPROVED:
            await self._check_conflicts(order)

        updated = await self.order_repo.update(
            order_id,
            OrderUpdate(status=new_status, message=message, user_id=changed_by_user_id)
        )
        if not updated:
            raise OrderNotFoundException(f"Order with id={order_id} not found")

        logger.info(f"Order id={order_id} status changed {order.status} -> {new_status}")
        return updated

    async def delete_order(self, order_id: int) -> None:
        try:
            deleted = await self.order_repo.delete(order_id)
        except RepositoryException:
            raise

        if not deleted:
            raise OrderNotFoundException(f"Order with id={order_id} not found")

        logger.info(f"Order id={order_id} deleted")
