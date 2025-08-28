from src.models.orders.enums.order_purpose import OrderPurpose
from src.models.resources.enums.resource_state import ResourceState


ORDER_PURPOSE_RULES = {
    OrderPurpose.Fix: [
        ResourceState.PRODUCTION,
        ResourceState.DEVELOPMENT,
        ResourceState.NOT_USABLE,
    ],
    OrderPurpose.EXPERIMENT: [
        ResourceState.DEVELOPMENT,
        ResourceState.PRODUCTION,
    ],
    OrderPurpose.TEST: [
        ResourceState.DEVELOPMENT,
        ResourceState.PRODUCTION,
    ],
    OrderPurpose.Production: [
        ResourceState.PRODUCTION,
    ],
}
