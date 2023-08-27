import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from exceptions import ResourceNotFoundException, ResourceBlockException, ResourceReleaseException
from models.db_models import Resource, ResourceHistory
from models.enums import Status, ResourceOperationType
from models.filters import ResourceFilter, ResourceHistoryFilter, PaginationParams
from models.pydantic_models import ResourceIn, ResourceOut, ResourcesOut, ResourceOperationOut, ResourcesOperationsOut
from resource_history_repository import create_resource_history_repository, ResourceHistoryRepository
from resource_repository import ResourceRepository, create_resource_repository


class ResourceService(ABC):

    @abstractmethod
    def get_resources(self, resource_filter: Optional[ResourceFilter], pagination: PaginationParams) -> ResourcesOut:
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
    def get_resources_history(self, filters: ResourceHistoryFilter,
                              pagination: PaginationParams) -> ResourcesOperationsOut:
        raise NotImplementedError()


class PgResourceService(ResourceService):

    def __init__(self) -> None:
        super().__init__()
        self.resource_repository: ResourceRepository = create_resource_repository()
        self.resource_history_repository: ResourceHistoryRepository = create_resource_history_repository()

    def get_resources(self, resource_filter: Optional[ResourceFilter], pagination: PaginationParams) -> ResourcesOut:
        with self.resource_repository as resource_repo:
            total_filtered_records = resource_repo.get_resources_count(resource_filter)
            resources_db = resource_repo.get_resources(resource_filter, pagination)
            resources_out = [ResourceOut(**resource.to_dict()) for resource in resources_db]
            return ResourcesOut(filtered_count=total_filtered_records, items=resources_out)

    def create_resource(self, resource_in: ResourceIn) -> ResourceOut:
        with self.resource_repository as resource_repo:
            resource_out: ResourceOut = ResourceOut(
                id=uuid.uuid4(),
                created_at=datetime.now(),
                **resource_in.dict()
            )
            resource_db_to_save = Resource(**resource_out.dict())
            resource_db_saved = resource_repo.create_resource(resource_db_to_save)
            resource_out = ResourceOut(**resource_db_saved.to_dict())
            return resource_out

    def remove_resource(self, resource_id: str) -> None:
        with self.resource_repository as resource_repo:
            resource_repo.remove_resource(resource_id)

    def get_resource(self, resource_id: str) -> ResourceOut:
        with self.resource_repository as resource_repo:
            resource_db = resource_repo.get_resource(resource_id)
            return ResourceOut(**resource_db.to_dict())

    def block_resource(self, resource_id: str) -> None:
        with self.resource_repository as resource_repo, self.resource_history_repository as history_repo:
            resource = resource_repo.get_resource(resource_id)

            if not resource:
                raise ResourceNotFoundException(resource_id)
            if resource.status != Status.FREE:
                raise ResourceBlockException(resource_id)

            resource.status = Status.BLOCKED
            resource_repo.update(resource)

            history_entry = ResourceOperationOut(id=uuid.uuid4(),
                                                 resource_id=uuid.UUID(resource_id),
                                                 operation=ResourceOperationType.BLOCK)

            resource_history_db_to_save = ResourceHistory(**history_entry.dict())
            history_repo.add(resource_history_db_to_save)

    def release_resource(self, resource_id: str) -> None:
        with self.resource_repository as resource_repo, self.resource_history_repository as history_repo:
            resource = resource_repo.get_resource(resource_id)

            if not resource:
                raise ResourceNotFoundException(resource_id)
            if resource.status != Status.BLOCKED:
                raise ResourceReleaseException(resource_id)

            resource.status = Status.FREE
            resource_repo.update(resource)

            history_entry = ResourceOperationOut(id=uuid.uuid4(),
                                                 resource_id=uuid.UUID(resource_id),
                                                 operation=ResourceOperationType.RELEASE)

            resource_history_db_to_save = ResourceHistory(**history_entry.dict())
            history_repo.add(resource_history_db_to_save)

    def get_resources_history(self, filters: ResourceHistoryFilter,
                              pagination: PaginationParams) -> ResourcesOperationsOut:
        with self.resource_history_repository as history_repo:
            total_filtered_records = history_repo.get_history_count(filters)
            resources_history = history_repo.get_history(filters, pagination)
            resource_history_out = [ResourceOperationOut(**history_record.to_dict()) for history_record in
                                    resources_history]
            return ResourcesOperationsOut(filtered_count=total_filtered_records, items=resource_history_out)


def create_resource_service() -> ResourceService:
    return PgResourceService()
