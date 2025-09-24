from enum import Enum


class OrderPurpose(str, Enum):
    Production = "Production"
    TEST = "Test"
    EXPERIMENT = "Experiment"
    MAINTENANCE = "Maintenance"

ORDER_PURPOSE_DESCRIPTIONS = {
    OrderPurpose.Production: "Requesting live production resources.",
    OrderPurpose.TEST: "Testing using simulated or recorded data.",
    OrderPurpose.EXPERIMENT: "Experimenting under development conditions.",
    OrderPurpose.MAINTENANCE: "Fixing or repairing broken resources.",
}