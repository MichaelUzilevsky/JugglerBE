from app.domain.schemas.order.enums.order_status import OrderStatus

legal_transitions = {
            OrderStatus.CREATED: [OrderStatus.PENDING, OrderStatus.CANCELED],
            OrderStatus.PENDING: [OrderStatus.APPROVED, OrderStatus.REJECTED, OrderStatus.CANCELED],
            OrderStatus.APPROVED: [OrderStatus.PENDING, OrderStatus.CANCELED],
            OrderStatus.REJECTED: [OrderStatus.PENDING, OrderStatus.CANCELED],
            OrderStatus.CANCELED: []
        }
