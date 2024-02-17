from abc import ABC, abstractmethod
from typing import Optional, List, Type

from sqlalchemy import func
from sqlalchemy.orm import joinedload, Session

from exceptions import ResourceNotFoundException
from models.db_models import Resource
from models.filters import ResourceFilter, PaginationParams


class ResourceRepository(ABC):
    @abstractmethod
    def get_resources(self, session: Session, resource_filter: Optional[ResourceFilter],
                      pagination: PaginationParams) -> List[Resource]:
        raise NotImplementedError()

    @abstractmethod
    def get_resources_count(self, session: Session, resource_filter: Optional[ResourceFilter]) -> int:
        raise NotImplementedError()

    @abstractmethod
    def create_resource(self, session: Session, resource: Resource) -> Resource:
        raise NotImplementedError()

    @abstractmethod
    def update(self, session: Session, resource: Resource) -> None:
        raise NotImplementedError()

    @abstractmethod
    def remove_resource(self, session: Session, resource_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_resource(self, session: Session, resource_id: str) -> Resource:
        raise NotImplementedError()


class ResourceRepositoryPostgreSQL(ResourceRepository):
    @staticmethod
    def _apply_filters(query, resource_filter: Optional[ResourceFilter]):
        if resource_filter:
            if resource_filter.status:
                query = query.filter(Resource.status == resource_filter.status)
            if resource_filter.tags:
                for tag in resource_filter.tags:
                    query = query.filter(Resource.tags.contains([tag]))

        return query

    def get_resources_count(self, session: Session, resource_filter: Optional[ResourceFilter]) -> int:
        query = session.query(func.count(Resource.id))
        query = self._apply_filters(query, resource_filter)
        return query.scalar()

    def get_resources(self, session: Session, resource_filter: Optional[ResourceFilter],
                      pagination: PaginationParams) -> list[Type[Resource]]:
        query = session.query(Resource).options(joinedload(Resource.variables))
        query = self._apply_filters(query, resource_filter)
        return query.offset(pagination.skip).limit(pagination.limit).all()

    def create_resource(self, session: Session, resource: Resource) -> Resource:
        session.add(resource)
        session.flush()
        session.refresh(resource)
        return resource

    def update(self, session: Session, resource: Resource) -> Resource:
        existing_resource = session.query(Resource).filter_by(id=resource.id).first()

        if not existing_resource:
            raise ResourceNotFoundException(str(resource.id))

        for key, value in resource.to_dict().items():
            setattr(existing_resource, key, value)

        return existing_resource

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
        else:
            raise ResourceNotFoundException(resource_id)


def create_resource_repository() -> ResourceRepository:
    return ResourceRepositoryPostgreSQL()
