from enum import Enum


class OrderPurpose(str, Enum):
    Production = "Production"
    TEST = "Test"
    EXPERIMENT = "Experiment"
    Fix = "Fix"

ORDER_PURPOSE_DESCRIPTIONS = {
    OrderPurpose.Production: "Requesting live production resources.",
    OrderPurpose.TEST: "Testing using simulated or recorded data.",
    OrderPurpose.EXPERIMENT: "Experimenting under development conditions.",
    OrderPurpose.Fix: "Fixing or repairing broken resources.",
}