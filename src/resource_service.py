import uuid
from abc import ABC, abstractmethod
from uuid import UUID

from src.db_connection import get_db_session
from src.exceptions import ResourceBlockException, ResourceReleaseException
from src.models.db_models import ResourceHistory
from src.models.enums import ResourceOperationType, Status
from src.models.filters import PaginationParams, ResourceFilter, ResourceHistoryFilter
from src.models.pydantic_models import (
    ClaimRequest,
    OperationRequest,
    ResourceIn,
    ResourceOperationOut,
    ResourceOut,
    ResourcesOperationsOut,
    ResourcesOut,
)
from src.models.transformers import resource_db_model_to_pydantic, resource_pydantic_to_db_model
from src.resource_history_repository import ResourceHistoryRepository, create_resource_history_repository
from src.resource_repository import ResourceRepository, create_resource_repository


class ResourceService(ABC):
    @abstractmethod
    def get_resources(self, resource_filter: ResourceFilter | None, pagination: PaginationParams) -> ResourcesOut:
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
    def block_resource(self, resource_id: UUID, block_request: OperationRequest) -> None:
        raise NotImplementedError()

    @abstractmethod
    def release_resource(self, resource_id: UUID) -> None:
        raise NotImplementedError()

    @abstractmethod
    def claim_resource(self, claim_request: ClaimRequest) -> ResourceOut | None:
        raise NotImplementedError()

    @abstractmethod
    def get_resources_history(
        self, filters: ResourceHistoryFilter, pagination: PaginationParams
    ) -> ResourcesOperationsOut:
        raise NotImplementedError()


class PgResourceService(ResourceService):
    def __init__(self) -> None:
        super().__init__()
        self.resource_repository: ResourceRepository = create_resource_repository()
        self.resource_history_repository: ResourceHistoryRepository = create_resource_history_repository()

    def get_resources(self, resource_filter: ResourceFilter | None, pagination: PaginationParams) -> ResourcesOut:
        with get_db_session() as session:
            total_filtered_records = self.resource_repository.get_resources_count(session, resource_filter)
            resources_db = self.resource_repository.get_resources(session, resource_filter, pagination)
            resources_out = [resource_db_model_to_pydantic(resource) for resource in resources_db]
            return ResourcesOut(filtered_count=total_filtered_records, items=resources_out)

    def create_resource(self, resource_in: ResourceIn) -> ResourceOut:
        with get_db_session() as session:
            resource_out: ResourceOut = ResourceOut(id=uuid.uuid4(), **resource_in.model_dump())

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

    def block_resource(self, resource_id: UUID, block_request: OperationRequest) -> None:
        with get_db_session() as session:
            resource = self.resource_repository.change_status(session, resource_id, Status.FREE, Status.BLOCKED)
            if resource is None:
                self._raise_status_change_error(session, resource_id, ResourceBlockException)
            self._add_history(session, resource_id, ResourceOperationType.BLOCK, block_request.description)

    def release_resource(self, resource_id: UUID) -> None:
        with get_db_session() as session:
            resource = self.resource_repository.change_status(session, resource_id, Status.BLOCKED, Status.FREE)
            if resource is None:
                self._raise_status_change_error(session, resource_id, ResourceReleaseException)
            self._add_history(session, resource_id, ResourceOperationType.RELEASE)

    def claim_resource(self, claim_request: ClaimRequest) -> ResourceOut | None:
        with get_db_session() as session:
            resource = self.resource_repository.claim(session, claim_request.tags)
            if resource is None:
                return None
            self._add_history(session, resource.id, ResourceOperationType.BLOCK, claim_request.description)
            return resource_db_model_to_pydantic(resource)

    def _raise_status_change_error(self, session, resource_id: UUID, operation_exception: type[Exception]) -> None:
        self.resource_repository.get_resource(session, str(resource_id))
        raise operation_exception(str(resource_id))

    def _add_history(
        self,
        session,
        resource_id: UUID,
        operation: ResourceOperationType,
        description: str | None = None,
    ) -> None:
        history_entry = ResourceHistory(
            id=uuid.uuid4(), resource_id=resource_id, operation=operation, description=description
        )
        self.resource_history_repository.add(session, history_entry)

    def get_resources_history(
        self, filters: ResourceHistoryFilter, pagination: PaginationParams
    ) -> ResourcesOperationsOut:
        with get_db_session() as session:
            total_filtered_records = self.resource_history_repository.get_history_count(session, filters)
            resources_history = self.resource_history_repository.get_history(session, filters, pagination)
            resource_history_out = [ResourceOperationOut.model_validate(record) for record in resources_history]
            return ResourcesOperationsOut(filtered_count=total_filtered_records, items=resource_history_out)


def create_resource_service() -> ResourceService:
    return PgResourceService()
