from enum import StrEnum


class Status(StrEnum):
    FREE = "FREE"
    BLOCKED = "BLOCKED"


class ResourceOperationType(StrEnum):
    BLOCK = "BLOCK"
    RELEASE = "RELEASE"
    RENEW = "RENEW"
    EXPIRE = "EXPIRE"
