import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from db_connection import get_db_session
from exceptions import ResourceNotFoundException, ResourceBlockException, ResourceReleaseException
from models.db_models import ResourceHistory
from models.enums import Status, ResourceOperationType
from models.filters import ResourceFilter, ResourceHistoryFilter, PaginationParams
from models.pydantic_models import ResourceIn, ResourceOut, ResourcesOut, ResourceOperationOut, ResourcesOperationsOut, \
    OperationRequest
from models.transformers import resource_db_model_to_pydantic, resource_pydantic_to_db_model
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
    def block_resource(self, resource_id: str, block_request: OperationRequest) -> None:
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
        with get_db_session() as session:
            total_filtered_records = self.resource_repository.get_resources_count(session, resource_filter)
            resources_db = self.resource_repository.get_resources(session, resource_filter, pagination)
            resources_out = [resource_db_model_to_pydantic(resource) for resource in resources_db]
            return ResourcesOut(filtered_count=total_filtered_records, items=resources_out)

    def create_resource(self, resource_in: ResourceIn) -> ResourceOut:
        with get_db_session() as session:
            resource_out: ResourceOut = ResourceOut(
                id=uuid.uuid4(),
                created_at=datetime.now(),
                **resource_in.dict()
            )

            resource_db_to_save = resource_pydantic_to_db_model(resource_out)
            resource_db_saved = self.resource_repository.create_resource(session, resource_db_to_save)
            return resource_db_model_to_pydantic(resource_db_saved)

    def remove_resource(self, resource_id: str) -> None:
        with get_db_session() as session:
            self.resource_repository.remove_resource(session, resource_id)

    def get_resource(self, resource_id: str) -> ResourceOut:
        with get_db_session() as session:
            resource_db = self.resource_repository.get_resource(session, resource_id)
            return resource_db_model_to_pydantic(resource_db)

    def block_resource(self, resource_id: str, block_request: OperationRequest) -> None:
        with get_db_session() as session:
            resource = self.resource_repository.get_resource(session, resource_id)

            if not resource:
                raise ResourceNotFoundException(resource_id)
            if resource.status != Status.FREE:
                raise ResourceBlockException(resource_id)

            resource.status = Status.BLOCKED
            self.resource_repository.update(session, resource)

            history_entry = ResourceOperationOut(id=uuid.uuid4(),
                                                 resource_id=uuid.UUID(resource_id),
                                                 operation=ResourceOperationType.BLOCK,
                                                 description=block_request.description
                                                 )

            resource_history_db_to_save = ResourceHistory(**history_entry.dict())
            self.resource_history_repository.add(session, resource_history_db_to_save)

    def release_resource(self, resource_id: str) -> None:
        with get_db_session() as session:
            resource = self.resource_repository.get_resource(session, resource_id)

            if not resource:
                raise ResourceNotFoundException(resource_id)
            if resource.status != Status.BLOCKED:
                raise ResourceReleaseException(resource_id)

            resource.status = Status.FREE
            self.resource_repository.update(session, resource)

            history_entry = ResourceOperationOut(id=uuid.uuid4(),
                                                 resource_id=uuid.UUID(resource_id),
                                                 operation=ResourceOperationType.RELEASE)

            resource_history_db_to_save = ResourceHistory(**history_entry.dict())
            self.resource_history_repository.add(session, resource_history_db_to_save)

    def get_resources_history(self, filters: ResourceHistoryFilter,
                              pagination: PaginationParams) -> ResourcesOperationsOut:
        with get_db_session() as session:
            total_filtered_records = self.resource_history_repository.get_history_count(session, filters)
            resources_history = self.resource_history_repository.get_history(session, filters, pagination)
            resource_history_out = [ResourceOperationOut(**history_record.to_dict()) for history_record in
                                    resources_history]
            return ResourcesOperationsOut(filtered_count=total_filtered_records, items=resource_history_out)


def create_resource_service() -> ResourceService:
    return PgResourceService()
