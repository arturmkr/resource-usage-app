from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from src.models.enums import ResourceOperationType, Status


class ResourceFilter(BaseModel):
    status: Status | None = None
    tags: list[str] = Field(default_factory=list)


class ResourceHistoryFilter(BaseModel):
    resource_id: str | None = None
    operation: ResourceOperationType | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


DEFAULT_PAGE_SIZE = 10


class PaginationParams(BaseModel):
    skip: Annotated[int, Field(ge=0)] = 0
    limit: Annotated[int, Field(ge=1, le=100)] = DEFAULT_PAGE_SIZE
