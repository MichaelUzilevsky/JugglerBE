from enum import Enum


class OrderPurpose(str, Enum):
    TEST = "Test"
    EXPERIMENT = "Experiment"
