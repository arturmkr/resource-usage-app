from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from models.enums import Status, ResourceOperationType


class Variable(BaseModel):
    name: str
    value: str


class ResourceIn(BaseModel):
    resource_name: str
    description: Optional[str]
    tags: Optional[list[str]]
    variables: Optional[list[Variable]]


class ResourceOut(ResourceIn):
    id: UUID
    status: Status = Status.FREE
    created_at: datetime


class ResourcesOut(BaseModel):
    filtered_count: int
    items: list[ResourceOut]


class ResourceOperationOut(BaseModel):
    id: UUID
    created_at: Optional[datetime]
    resource_id: UUID
    operation: ResourceOperationType
    description: Optional[str]


class ResourcesOperationsOut(BaseModel):
    filtered_count: int
    items: list[ResourceOperationOut]


class OperationRequest(BaseModel):
    description: Optional[str]
