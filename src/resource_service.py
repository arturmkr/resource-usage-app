import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.config.default import get_settings
from src.db_connection import get_db_session
from src.exceptions import (
    ResourceBlockException,
    ResourceLeaseValidationException,
    ResourceReleaseException,
    ResourceRenewException,
)
from src.models.db_models import ResourceHistory
from src.models.enums import ResourceOperationType
from src.models.filters import PaginationParams, ResourceFilter, ResourceHistoryFilter
from src.models.pydantic_models import (
    ClaimRequest,
    LeaseRequest,
    ReleaseRequest,
    RenewRequest,
    ResourceIn,
    ResourceLeaseOut,
    ResourceOperationOut,
    ResourceOut,
    ResourcesOperationsOut,
    ResourcesOut,
)
from src.models.transformers import (
    resource_db_model_to_lease_pydantic,
    resource_db_model_to_pydantic,
    resource_pydantic_to_db_model,
)
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
    def block_resource(self, resource_id: UUID, block_request: LeaseRequest) -> ResourceLeaseOut:
        raise NotImplementedError()

    @abstractmethod
    def release_resource(self, resource_id: UUID, release_request: ReleaseRequest) -> None:
        raise NotImplementedError()

    @abstractmethod
    def renew_resource(self, resource_id: UUID, renew_request: RenewRequest) -> ResourceLeaseOut:
        raise NotImplementedError()

    @abstractmethod
    def claim_resource(self, claim_request: ClaimRequest) -> ResourceLeaseOut | None:
        raise NotImplementedError()

    @abstractmethod
    def get_resources_history(
        self, filters: ResourceHistoryFilter, pagination: PaginationParams
    ) -> ResourcesOperationsOut:
        raise NotImplementedError()

    @abstractmethod
    def release_expired_leases(self) -> int:
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

    def block_resource(self, resource_id: UUID, block_request: LeaseRequest) -> ResourceLeaseOut:
        lease_token, lease_expires_at = self._create_lease(block_request.ttl_minutes)
        with get_db_session() as session:
            resource = self.resource_repository.block(
                session,
                resource_id,
                lease_token,
                block_request.lease_owner,
                lease_expires_at,
            )
            if resource is None:
                self._raise_status_change_error(session, resource_id, ResourceBlockException)
            self._add_history(session, resource_id, ResourceOperationType.BLOCK, block_request.description)
            return resource_db_model_to_lease_pydantic(resource)

    def release_resource(self, resource_id: UUID, release_request: ReleaseRequest) -> None:
        with get_db_session() as session:
            resource = self.resource_repository.release(session, resource_id, release_request.lease_token)
            if resource is None:
                self._raise_status_change_error(session, resource_id, ResourceReleaseException)
            self._add_history(session, resource_id, ResourceOperationType.RELEASE, release_request.description)

    def renew_resource(self, resource_id: UUID, renew_request: RenewRequest) -> ResourceLeaseOut:
        _, lease_expires_at = self._create_lease(renew_request.ttl_minutes)
        with get_db_session() as session:
            resource = self.resource_repository.renew(session, resource_id, renew_request.lease_token, lease_expires_at)
            if resource is None:
                self._raise_status_change_error(session, resource_id, ResourceRenewException)
            self._add_history(session, resource_id, ResourceOperationType.RENEW, renew_request.description)
            return resource_db_model_to_lease_pydantic(resource)

    def claim_resource(self, claim_request: ClaimRequest) -> ResourceLeaseOut | None:
        lease_token, lease_expires_at = self._create_lease(claim_request.ttl_minutes)
        with get_db_session() as session:
            resource = self.resource_repository.claim(
                session,
                claim_request.tags,
                lease_token,
                claim_request.lease_owner,
                lease_expires_at,
            )
            if resource is None:
                return None
            self._add_history(session, resource.id, ResourceOperationType.BLOCK, claim_request.description)
            return resource_db_model_to_lease_pydantic(resource)

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

    def _create_lease(self, ttl_minutes: int | None) -> tuple[UUID, datetime]:
        settings = get_settings()
        ttl = ttl_minutes or settings.app_default_lease_ttl_minutes
        if ttl < 1 or ttl > settings.app_max_lease_ttl_minutes:
            raise ResourceLeaseValidationException(
                f"Lease ttl must be between 1 and {settings.app_max_lease_ttl_minutes} minutes"
            )
        return uuid.uuid4(), datetime.now(UTC) + timedelta(minutes=ttl)

    def release_expired_leases(self) -> int:
        with get_db_session() as session:
            expired_resources = self.resource_repository.release_expired_leases(session, datetime.now(UTC))
            for resource in expired_resources:
                self._add_history(session, resource.id, ResourceOperationType.EXPIRE)
            return len(expired_resources)

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
