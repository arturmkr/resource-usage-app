from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from models.enums import Status


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
