from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from models.enums import Status, ResourceOperationType


class ResourceIn(BaseModel):
    name: str
    description: Optional[str]
    tags: Optional[list[str]]


class ResourceOut(ResourceIn):
    id: UUID
    status: Status = Status.FREE
    created_at: datetime


class ResourcesOut(BaseModel):
    resources_count: int
    resources: list[ResourceOut]


class ResourceFilter(BaseModel):
    status: Optional[Status] = None
    tags: Optional[list[str]] = None


class ResourceOperation(BaseModel):
    id: UUID
    created_at: Optional[datetime]
    resource_id: UUID
    operation: ResourceOperationType
    user_agent: Optional[str]
    ip_address: Optional[str]
    description: Optional[str]
