from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, joinedload

from src.exceptions import ResourceNotFoundException
from src.models.db_models import Resource
from src.models.enums import Status
from src.models.filters import PaginationParams, ResourceFilter


class ResourceRepository(ABC):
    @abstractmethod
    def get_resources(
        self, session: Session, resource_filter: ResourceFilter | None, pagination: PaginationParams
    ) -> list[Resource]:
        raise NotImplementedError()

    @abstractmethod
    def get_resources_count(self, session: Session, resource_filter: ResourceFilter | None) -> int:
        raise NotImplementedError()

    @abstractmethod
    def create_resource(self, session: Session, resource: Resource) -> Resource:
        raise NotImplementedError()

    @abstractmethod
    def remove_resource(self, session: Session, resource_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_resource(self, session: Session, resource_id: str) -> Resource:
        raise NotImplementedError()

    @abstractmethod
    def change_status(self, session: Session, resource_id: UUID, expected: Status, new: Status) -> Resource | None:
        raise NotImplementedError()

    @abstractmethod
    def claim(self, session: Session, tags: list[str]) -> Resource | None:
        raise NotImplementedError()


class ResourceRepositoryPostgreSQL(ResourceRepository):
    @staticmethod
    def _apply_filters(query, resource_filter: ResourceFilter | None):
        if resource_filter:
            if resource_filter.status:
                query = query.filter(Resource.status == resource_filter.status)
            if resource_filter.tags:
                for tag in resource_filter.tags:
                    query = query.filter(Resource.tags.contains([tag]))

        return query

    def get_resources_count(self, session: Session, resource_filter: ResourceFilter | None) -> int:
        query = session.query(func.count(Resource.id))
        query = self._apply_filters(query, resource_filter)
        return query.scalar()

    def get_resources(
        self, session: Session, resource_filter: ResourceFilter | None, pagination: PaginationParams
    ) -> list[Resource]:
        query = session.query(Resource).options(joinedload(Resource.variables))
        query = self._apply_filters(query, resource_filter)
        return query.order_by(Resource.created_at, Resource.id).offset(pagination.skip).limit(pagination.limit).all()

    def create_resource(self, session: Session, resource: Resource) -> Resource:
        session.add(resource)
        session.flush()
        session.refresh(resource)
        return resource

    def remove_resource(self, session: Session, resource_id: str):
        existing_resource = session.query(Resource).filter_by(id=resource_id).first()
        if existing_resource:
            session.delete(existing_resource)
        else:
            raise ResourceNotFoundException(str(resource_id))

    def get_resource(self, session: Session, resource_id: str) -> Resource:
        resource = session.query(Resource).options(joinedload(Resource.variables)).filter_by(id=resource_id).first()
        if resource:
            return resource
        raise ResourceNotFoundException(resource_id)

    def change_status(self, session: Session, resource_id: UUID, expected: Status, new: Status) -> Resource | None:
        statement = (
            update(Resource)
            .where(Resource.id == resource_id, Resource.status == expected)
            .values(status=new)
            .returning(Resource)
        )
        return session.execute(statement).scalar_one_or_none()

    def claim(self, session: Session, tags: list[str]) -> Resource | None:
        statement = (
            select(Resource)
            .where(Resource.status == Status.FREE, Resource.tags.contains(tags))
            .order_by(Resource.created_at, Resource.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        resource = session.execute(statement).scalar_one_or_none()
        if resource:
            resource.status = Status.BLOCKED
            session.flush()
        return resource


def create_resource_repository() -> ResourceRepository:
    return ResourceRepositoryPostgreSQL()
