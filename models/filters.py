from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from models.enums import Status, ResourceOperationType


class ResourceFilter(BaseModel):
    status: Optional[Status] = None
    tags: Optional[List[str]] = []


class ResourceHistoryFilter(BaseModel):
    resource_id: Optional[str] = None
    operation: Optional[ResourceOperationType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
