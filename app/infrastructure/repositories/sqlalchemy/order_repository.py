from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.sqlalchemy.models import Order, BaseResource, User, OrderStatusHistory
from app.domain.exceptions.repository_exceptions import NotFoundException, IntegrityViolationException, \
    RepositoryException
from app.domain.repositories.iorder_repository import IOrderRepository
from app.domain.schemas.order.order import OrderCreate, OrderUpdate, OrderRead
from app.infrastructure.mappers.sqlalchemy.order_mapper import OrderMapper
from app.infrastructure.repositories.sqlalchemy.base_repository import SQLAlchemyBaseRepository


class SQLAlchemyOrderRepository(
    SQLAlchemyBaseRepository[OrderRead, OrderCreate, OrderUpdate, Order],
    IOrderRepository,
):
    """SQLAlchemy repository for Orders, including resources and status history"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Order, OrderMapper)

    async def _get_user(self, user_id: int) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            self._log_warning("order_user_not_found", f"User with id={user_id} not found", {"user_id": user_id})
            raise NotFoundException(f"User with id={user_id} not found")
        return user

    async def _get_resources(self, resource_ids: List[int]) -> List[BaseResource]:
        stmt = select(BaseResource).where(BaseResource.id.in_(resource_ids))
        result = await self.session.execute(stmt)
        resources = result.scalars().all()
        if len(resources) != len(resource_ids):
            self._log_warning(
                "order_resources_not_found",
                "One or more resources not found",
                {"resource_ids": resource_ids},
            )
            raise NotFoundException("One or more resources not found")
        return list(resources)

    def _create_status_history(self, order_id: int, old_status, new_status, message: str, changed_by: int):
        history = OrderStatusHistory(
            order_id=order_id,
            old_status=old_status,
            new_status=new_status,
            message=message,
            changed_by=changed_by,
        )
        self.session.add(history)

    async def create(self, order_create: OrderCreate) -> OrderRead:
        try:
            orm_order = self.mapper.to_orm(order_create)

            orm_order.user = await self._get_user(order_create.user_id)
            if order_create.resource_ids:
                orm_order.resources = await self._get_resources(order_create.resource_ids)

            self.session.add(orm_order)
            await self.session.flush()

            self._create_status_history(
                order_id=orm_order.id,
                old_status=order_create.status,
                new_status=order_create.status,
                message=order_create.message or "Order created",
                changed_by=order_create.user_id,
            )

            await self.session.flush()
            await self.session.refresh(orm_order)

            self._log_info(
                "order_create_success",
                f"Created order id={orm_order.id}",
                {"order_id": orm_order.id, "user_id": order_create.user_id},
            )
            return await self.get(orm_order.id)

        except IntegrityError as e:
            await self._handle_integrity_error("create", e, {"user_id": order_create.user_id,
                                                             "resource_ids": order_create.resource_ids})
        except SQLAlchemyError as e:
            self._log_error("order_create_db_error", "Database error while creating order", {"error": str(e)})
            raise RepositoryException("Database error while creating order")

    async def update(self, order_id: int, order_update: OrderUpdate) -> Optional[OrderRead]:
        try:
            stmt = select(Order).where(Order.id == order_id).options(
                selectinload(Order.resources),
                selectinload(Order.user),
            )
            result = await self.session.execute(stmt)
            orm_order = result.scalar_one_or_none()
            if not orm_order:
                self._log_warning("order_update_not_found", f"Order with id={order_id} not found",
                                  {"order_id": order_id})
                raise NotFoundException(f"Order with id={order_id} not found")

            old_status = orm_order.status
            self.mapper.update_orm(orm_order, order_update)

            if order_update.user_id is not None:
                orm_order.user = await self._get_user(order_update.user_id)

            if order_update.resource_ids is not None:
                orm_order.resources = await self._get_resources(order_update.resource_ids)

            if order_update.status is not None or order_update.message:
                new_status = order_update.status or old_status
                self._create_status_history(
                    order_id=orm_order.id,
                    old_status=old_status,
                    new_status=new_status,
                    message=order_update.message or f"Order status updated to {new_status.value}",
                    changed_by=order_update.user_id or orm_order.user_id,
                )

            await self.session.flush()
            await self.session.refresh(orm_order)

            self._log_info("order_update_success", f"Updated order id={order_id}",
                           {"order_id": order_id, "user_id": order_update.user_id})

            return await self.get(order_id)

        except IntegrityError as e:
            await self._handle_integrity_error("update", e, {"order_id": order_id, "user_id": order_update.user_id})

        except SQLAlchemyError as e:
            self._log_error("order_update_db_error", f"Database error while updating order id={order_id}",
                            {"order_id": order_id, "error": str(e)})
            raise RepositoryException("Database error while updating order")

    async def get_orders_in_time_range(self, start_time, end_time) -> List[OrderRead]:
        try:
            stmt = (
                select(Order)
                .where(
                    and_(
                        Order.start_time <= end_time,
                        Order.end_time >= start_time
                    )
                )
                .options(
                    selectinload(Order.resources),
                    selectinload(Order.user),
                    selectinload(Order.status_history),
                )
            )
            result = await self.session.execute(stmt)
            orm_orders = result.scalars().all()
            self._log_info(
                "order_list_time_range",
                f"Fetched {len(orm_orders)} orders in time range",
                {"count": len(orm_orders), "start_time": str(start_time), "end_time": str(end_time)},
            )
            return [self.mapper.to_read(o) for o in orm_orders]

        except SQLAlchemyError as e:
            self._log_error(
                "order_list_time_range_db_error",
                "Database error while fetching orders in time range",
                {"error": str(e), "start_time": str(start_time), "end_time": str(end_time)},
            )
            raise RepositoryException("Database error while fetching orders in time range")

    async def get_users_orders(self, user_id: int) -> List[OrderRead]:
        try:
            stmt = (
                select(Order)
                .where(Order.user_id == user_id)
                .options(
                    selectinload(Order.resources),
                    selectinload(Order.user),
                    selectinload(Order.status_history),
                )
            )
            result = await self.session.execute(stmt)
            orm_orders = result.scalars().all()
            self._log_info(
                "order_list_by_user",
                f"Fetched {len(orm_orders)} orders for user id={user_id}",
                {"count": len(orm_orders), "user_id": user_id},
            )
            return [self.mapper.to_read(o) for o in orm_orders]

        except SQLAlchemyError as e:
            self._log_error(
                "order_list_by_user_db_error",
                f"Database error while fetching orders for user id={user_id}",
                {"error": str(e), "user_id": user_id},
            )
            raise RepositoryException("Database error while fetching user orders")

    async def _handle_integrity_error(self, action: str, e: IntegrityError, context: dict):
        err = str(e).lower()
        self._log_warning(f"order_{action}_integrity_error", f"Integrity violation during order {action}",
                          {"error": str(e), **context})

        if "foreign key" in err and "user_id" in err:
            raise NotFoundException(f"User with id={context.get('user_id')} not found")
        if "foreign key" in err and "resource" in err:
            raise NotFoundException("One or more resources not found")
        if "null value" in err:
            raise IntegrityViolationException("Missing required order fields")
        raise IntegrityViolationException("Order integrity violation")
