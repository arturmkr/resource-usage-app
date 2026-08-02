from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.enums import ResourceOperationType, Status


class Variable(BaseModel):
    name: str
    value: str


class ResourceIn(BaseModel):
    resource_name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    tags: list[str] = Field(default_factory=list)
    variables: list[Variable] = Field(default_factory=list)


class ResourceOut(ResourceIn):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: Status = Status.FREE
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ResourceLeaseOut(ResourceOut):
    lease_token: UUID


class ResourcesOut(BaseModel):
    filtered_count: int
    items: list[ResourceOut]


class ResourceOperationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime | None = None
    resource_id: UUID
    operation: ResourceOperationType
    description: str | None = None


class ResourcesOperationsOut(BaseModel):
    filtered_count: int
    items: list[ResourceOperationOut]


class OperationRequest(BaseModel):
    description: str | None = Field(default=None, max_length=255)


class LeaseRequest(OperationRequest):
    lease_owner: str | None = Field(default=None, max_length=255)
    ttl_minutes: int | None = Field(default=None, gt=0)


class ClaimRequest(LeaseRequest):
    tags: list[str] = Field(min_length=1)


class ReleaseRequest(OperationRequest):
    lease_token: UUID


class RenewRequest(OperationRequest):
    lease_token: UUID
    ttl_minutes: int | None = Field(default=None, gt=0)
