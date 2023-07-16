from enum import Enum


class Status(str, Enum):
    FREE = "FREE"
    BLOCKED = "BLOCKED"


class ResourceOperationType(str, Enum):
    BLOCK = "BLOCK"
    RELEASE = "RELEASE"
