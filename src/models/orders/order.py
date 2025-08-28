from datetime import datetime
from typing import List, Optional

from pydantic import Field

from src.models.abstract.base_data import BaseData
from src.models.orders.enums.order_purpose import OrderPurpose
from src.models.orders.enums.order_status import OrderStatus


class Order(BaseData):
    user_id: str
    resources_ids: List[str] = Field(min_length=1)
    purpose: OrderPurpose
    status: OrderStatus = OrderStatus.CREATED
    start_time: datetime
    end_time: datetime
    conflicts_with: Optional[List[str]] = []
