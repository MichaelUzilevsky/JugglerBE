from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.sqlalchemy.models import Order, BaseResource, User, OrderStatusHistory
from app.domain.schemas.order.order import OrderCreate, OrderUpdate, OrderRead
from app.infrastructure.mappers.sqlalchemy.order_mapper import OrderMapper
from app.domain.repositories.iorder_repository import IOrderRepository
from app.infrastructure.repositories.sqlalchemy.base_repository import SQLAlchemyBaseRepository


class SQLAlchemyOrderRepository(
    SQLAlchemyBaseRepository[OrderRead, OrderCreate, OrderUpdate, Order],
    IOrderRepository,
):
    """SQLAlchemy repository for Orders, including resources and status history"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Order, OrderMapper)

    async def create(self, order_create: OrderCreate) -> OrderRead:
        orm_order = self.mapper.to_orm(order_create)

        # Attach user
        stmt = select(User).where(User.id == order_create.user_id)
        result = await self.session.execute(stmt)
        orm_order.user = result.scalar_one_or_none()

        # Attach resources
        if order_create.resource_ids:
            stmt = select(BaseResource).where(BaseResource.id.in_(order_create.resource_ids))
            result = await self.session.execute(stmt)
            orm_order.resources = result.scalars().all()

        self.session.add(orm_order)
        await self.session.flush()

        # Create first status history entry
        history = OrderStatusHistory(
            order_id=orm_order.id,
            old_status=order_create.status,
            new_status=order_create.status,
            message=order_create.message or "Order created",
            changed_by=order_create.user_id,
        )
        self.session.add(history)

        await self.session.flush()
        await self.session.refresh(orm_order)
        return self.mapper.to_read(orm_order)

    async def update(self, order_id: int, order_update: OrderUpdate) -> Optional[OrderRead]:
        stmt = select(Order).where(Order.id == order_id).options(
            selectinload(Order.resources),
            selectinload(Order.user),
        )
        result = await self.session.execute(stmt)
        orm_order = result.scalar_one_or_none()
        if not orm_order:
            return None

        old_status = orm_order.status

        # Update simple fields
        self.mapper.update_orm(orm_order, order_update)

        # Update user if provided
        if order_update.user_id is not None:
            stmt = select(User).where(User.id == order_update.user_id)
            result = await self.session.execute(stmt)
            orm_order.user = result.scalar_one_or_none()

        # Update many-to-many resources if provided
        if order_update.resource_ids is not None:
            stmt = select(BaseResource).where(BaseResource.id.in_(order_update.resource_ids))
            result = await self.session.execute(stmt)
            orm_order.resources = result.scalars().all()

        # Always log status history if status or message is provided
        if order_update.status is not None or order_update.message:
            new_status = order_update.status or old_status
            history = OrderStatusHistory(
                order_id=orm_order.id,
                old_status=old_status,
                new_status=new_status,
                message=order_update.message or f"Order status updated to {new_status.value}",
                changed_by=order_update.user_id or orm_order.user_id
            )
            self.session.add(history)

        await self.session.flush()
        await self.session.refresh(orm_order)
        return self.mapper.to_read(orm_order)

    async def get_orders_in_time_range(self, start_time, end_time) -> List[OrderRead]:
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
        return [self.mapper.to_read(o) for o in orm_orders]

    async def get_users_orders(self, user_id: int) -> List[OrderRead]:
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
        return [self.mapper.to_read(o) for o in orm_orders]
