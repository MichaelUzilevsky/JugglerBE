from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.domain.schemas.order.enums.order_purpose import OrderPurpose
from app.domain.schemas.order.enums.order_status import OrderStatus
from app.domain.schemas.resource.resource import ResourceRead
from app.domain.schemas.user.user import UserRead


# ----------------- History -----------------
class OrderStatusHistoryRead(BaseModel):
    id: int
    old_status: Optional[OrderStatus]
    new_status: OrderStatus
    message: Optional[str]
    changed_by: Optional[int]
    changed_at: datetime

    model_config = {"from_attributes": True}


# ----------------- Create -----------------
class OrderCreate(BaseModel):
    user_id: int
    purpose: OrderPurpose
    order_description: str
    status: OrderStatus = OrderStatus.CREATED
    start_time: datetime
    end_time: datetime
    resource_ids: List[int]


# ----------------- Update -----------------
class OrderUpdate(BaseModel):
    user_id: Optional[int] = None
    purpose: Optional[OrderPurpose] = None
    order_description: Optional[str] = None
    status: Optional[OrderStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    resource_ids: Optional[List[int]] = None
    message: Optional[str] = None


# ----------------- Read -----------------
class OrderRead(BaseModel):
    id: int
    purpose: OrderPurpose
    order_description: str
    status: OrderStatus
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime

    user: Optional[UserRead]
    resources: List[ResourceRead] = []
    status_history: List[OrderStatusHistoryRead] = []

    model_config = {"from_attributes": True}
