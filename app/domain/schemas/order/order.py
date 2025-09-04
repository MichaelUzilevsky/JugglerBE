from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.domain.schemas.resource.resource import ResourceRead
from app.domain.schemas.user.user import UserRead

from app.domain.schemas.order.enums.order_purpose import OrderPurpose
from app.domain.schemas.order.enums.order_status import OrderStatus


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
    status: OrderStatus = OrderStatus.CREATED
    start_time: datetime
    end_time: datetime
    resource_ids: List[int]
    message: Optional[str] = None

# ----------------- Update -----------------
class OrderUpdate(BaseModel):
    user_id: Optional[int] = None
    purpose: Optional[OrderPurpose] = None
    status: Optional[OrderStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    resource_ids: Optional[List[int]] = None
    message: Optional[str] = None

# ----------------- Read -----------------
class OrderRead(BaseModel):
    id: int
    purpose: OrderPurpose
    status: OrderStatus
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime

    user: Optional[UserRead]
    resources: List[ResourceRead] = []
    status_history: List[OrderStatusHistoryRead] = []

    model_config = {"from_attributes": True}
