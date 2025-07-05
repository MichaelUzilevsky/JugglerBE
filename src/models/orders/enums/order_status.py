from enum import Enum


class OrderStatus(str, Enum):
    CREATED = "Created"
    PENDING = "Pending"
    REJECTED = "Rejected"
    APPROVED = "Approved"
