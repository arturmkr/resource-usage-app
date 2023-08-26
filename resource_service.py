import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from models.db_models import Resource
from models.filters import ResourceFilter, ResourceHistoryFilter
from models.pydantic_models import ResourceIn, ResourceOut, ResourcesOut, ResourceOperationOut, ResourcesOperationsOut
from resource_history_repository import create_resource_history_repository, ResourceHistoryRepository
from resource_repository import ResourceRepository, create_resource_repository


class ResourceService(ABC):

    @abstractmethod
    def get_resources(self, resource_filter: Optional[ResourceFilter]) -> ResourcesOut:
        raise NotImplementedError()

    @abstractmethod
    def create_resource(self, resource_in: ResourceIn) -> ResourceOut:
        raise NotImplementedError()

    @abstractmethod
    def remove_resource(self, resource_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_resource(self, resource_id: str) -> ResourceOut:
        raise NotImplementedError()

    @abstractmethod
    def block_resource(self, resource_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def release_resource(self, resource_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_resources_history(self, filters: ResourceHistoryFilter) -> ResourcesOperationsOut:
        raise NotImplementedError()


class PgResourceService(ResourceService):

    def __init__(self) -> None:
        super().__init__()
        self.resource_repository: ResourceRepository = create_resource_repository()
        self.resource_history_repository: ResourceHistoryRepository = create_resource_history_repository()

    def get_resources(self, resource_filter: Optional[ResourceFilter]) -> ResourcesOut:
        resources_db = self.resource_repository.get_resources(resource_filter)
        resources_out = [ResourceOut(**resource.to_dict()) for resource in resources_db]
        return ResourcesOut(resources_count=len(resources_out), resources=resources_out)

    def create_resource(self, resource_in: ResourceIn) -> ResourceOut:
        resource_out: ResourceOut = ResourceOut(
            id=uuid.uuid4(),
            created_at=datetime.now(),
            **resource_in.dict()
        )
        resource_db_to_save = Resource(**resource_out.dict())
        resource_db_saved = self.resource_repository.create_resource(resource_db_to_save)
        resource_out = ResourceOut(**resource_db_saved.to_dict())
        return resource_out

    def remove_resource(self, resource_id: str) -> None:
        self.resource_repository.remove_resource(resource_id)

    def get_resource(self, resource_id: str) -> ResourceOut:
        resource_db = self.resource_repository.get_resource(resource_id)
        return ResourceOut(**resource_db.to_dict())

    def block_resource(self, resource_id: str) -> None:
        self.resource_repository.block_resource(resource_id)

    def release_resource(self, resource_id: str) -> None:
        self.resource_repository.release_resource(resource_id)

    def get_resources_history(self, filters: ResourceHistoryFilter) -> ResourcesOperationsOut:
        resources_history = self.resource_history_repository.get_history(filters)
        resource_history_out = [ResourceOperationOut(**history_record.to_dict()) for history_record in resources_history]
        return ResourcesOperationsOut(records_count=len(resource_history_out), history_records=resource_history_out)


def create_resource_service() -> ResourceService:
    return PgResourceService()
