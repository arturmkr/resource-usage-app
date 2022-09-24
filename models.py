from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ResourceStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ResourceOperation(str, Enum):
    BLOCK = "BLOCK"
    RELEASE = "RELEASE"


class Resource(BaseModel):
    name: str
    description: Optional[str]
    tags: Optional[list[str]]
    status: Optional[ResourceStatus]


class ResourceOut(Resource):
    id: UUID
    created_at: Optional[datetime]
    is_deleted: Optional[bool]


class ResourceUsageHistory(BaseModel):
    resource_id: UUID
    agent: Optional[str]
    operation: Optional[ResourceOperation]
    description: Optional[str]


class ResourceUsageHistoryOut(ResourceUsageHistory):
    id: UUID
    created_at: Optional[datetime]
