from typing import List, Optional
from datetime import datetime
from abc import ABC, abstractmethod
from app.domain.schemas.order.order import OrderCreate, OrderUpdate, OrderRead

class IOrderRepository(ABC):
    @abstractmethod
    async def create(self, order_create: OrderCreate) -> OrderRead:
        pass

    @abstractmethod
    async def get(self, order_id: int) -> Optional[OrderRead]:
        pass

    @abstractmethod
    async def list(self) -> List[OrderRead]:
        pass

    @abstractmethod
    async def update(self, order_id: int, order_update: OrderUpdate) -> Optional[OrderRead]:
        pass

    @abstractmethod
    async def delete(self, order_id: int) -> bool:
        pass

    @abstractmethod
    async def get_orders_in_time_range(self, start_time: datetime, end_time: datetime) -> List[OrderRead]:
        pass

    @abstractmethod
    async def get_users_orders(self, user_id: int) -> List[OrderRead]:
        pass
