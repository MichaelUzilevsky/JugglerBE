from typing import List

from app.db.sqlalchemy.models import Order, BaseResource
from app.domain.schemas.order.order import OrderCreate, OrderRead, OrderUpdate


class OrderMapper:
    @staticmethod
    def to_orm(order_create: OrderCreate) -> Order:
        """
        Map OrderCreate schema → ORM Order object.
        Note: This only creates the Order itself; related resources
        must be associated after creation using order.resources.
        """
        return Order(
            user_id=order_create.user_id,
            purpose=order_create.purpose,
            status=order_create.status,
            start_time=order_create.start_time,
            end_time=order_create.end_time,
        )

    @staticmethod
    def to_read(order: Order) -> OrderRead:
        """
        Map ORM Order → OrderRead schema, including relationships.
        """
        return OrderRead.model_validate(order)

    @staticmethod
    def update_orm(order: Order, order_update: OrderUpdate, resources: List[BaseResource] = None) -> Order:
        """
        Apply OrderUpdate schema → existing ORM Order object.
        Optionally update many-to-many resources.
        """
        if order_update.user_id is not None:
            order.user_id = order_update.user_id
        if order_update.purpose is not None:
            order.purpose = order_update.purpose
        if order_update.status is not None:
            order.status = order_update.status
        if order_update.start_time is not None:
            order.start_time = order_update.start_time
        if order_update.end_time is not None:
            order.end_time = order_update.end_time

        if resources is not None:
            order.resources = resources

        return order
