from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.domain.schemas.order.enums.order_purpose import OrderPurpose


class OrderCreateRequest(BaseModel):
    user_id: int
    purpose: OrderPurpose
    start_time: datetime
    end_time: datetime
    resource_ids: List[int]
    message: Optional[str] = None


class OrderUpdateRequest(BaseModel):
    user_id: Optional[int] = None
    purpose: Optional[OrderPurpose] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    resource_ids: Optional[List[int]] = None
    message: Optional[str] = None
