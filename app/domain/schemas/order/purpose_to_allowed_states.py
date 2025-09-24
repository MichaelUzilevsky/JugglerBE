from app.domain.schemas.order.enums.order_purpose import OrderPurpose
from app.domain.schemas.resource.enums.resource_state import ResourceState

PURPOSE_TO_ALLOWED_STATES = {
        OrderPurpose.Production: [ResourceState.PRODUCTION],
        OrderPurpose.TEST: [ResourceState.DEVELOPMENT, ResourceState.PRODUCTION],
        OrderPurpose.EXPERIMENT: [ResourceState.DEVELOPMENT, ResourceState.PRODUCTION],
        OrderPurpose.MAINTENANCE: [
            ResourceState.PRODUCTION,
            ResourceState.DEVELOPMENT,
            ResourceState.NOT_USABLE,
        ],
    }
