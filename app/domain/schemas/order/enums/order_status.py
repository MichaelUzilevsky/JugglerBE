from enum import Enum


class OrderStatus(str, Enum):
    CREATED = "Created"
    PENDING = "Pending"
    CANCELED = "Canceled"
    REJECTED = "Rejected"
    APPROVED = "Approved"
