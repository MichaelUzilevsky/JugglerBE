from enum import Enum


class ResourceEnvironment(str, Enum):
    ZNIF = "Znifim"
    FIVENIVE = "FiveNine"
    PREP = "Prep"
