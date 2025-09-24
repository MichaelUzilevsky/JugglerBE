from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.domain.schemas.order.enums.order_purpose import OrderPurpose


class OrderCreateRequest(BaseModel):
    user_id: int
    purpose: OrderPurpose
    order_description: str
    start_time: datetime
    end_time: datetime
    resource_ids: List[int]


class OrderUpdateRequest(BaseModel):
    user_id: Optional[int] = None
    purpose: Optional[OrderPurpose] = None
    order_description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    resource_ids: Optional[List[int]] = None
    message: Optional[str] = None
