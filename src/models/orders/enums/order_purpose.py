from enum import Enum


class OrderPurpose(str, Enum):
    Production = "Production"
    TEST = "Test"
    EXPERIMENT = "Experiment"
    Fix = "Fix"
