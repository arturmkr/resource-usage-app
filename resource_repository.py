import uuid
from abc import ABC, abstractmethod
from typing import Optional, List

from config.default import INIT_DB
from db_connection import session_factory
from exceptions import ResourceNotFoundException, ResourceBlockException, ResourceReleaseException
from models.db_models import Resource, ResourceHistory
from models.enums import Status, ResourceOperationType
from models.filters import ResourceFilter
from models.pydantic_models import ResourceOperationOut


class ResourceRepository(ABC):
    @abstractmethod
    def get_resources(self, resource_filter: Optional[ResourceFilter]) -> List[Resource]:
        raise NotImplementedError()

    @abstractmethod
    def create_resource(self, resource: Resource) -> Resource:
        raise NotImplementedError()

    @abstractmethod
    def remove_resource(self, resource_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_resource(self, resource_id: str) -> Resource:
        raise NotImplementedError()

    @abstractmethod
    def block_resource(self, resource_id: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def release_resource(self, resource_id: str) -> None:
        raise NotImplementedError()


class ResourceRepositoryPostgreSQL(ResourceRepository):

    def __init__(self) -> None:
        self.session = session_factory()

    def get_resources(self, resource_filter: Optional[ResourceFilter]) -> List[Resource]:
        query = self.session.query(Resource)

        if resource_filter.status:
            query = query.filter(Resource.status == resource_filter.status)
        if resource_filter.tags:
            for tag in resource_filter.tags:
                query = query.filter(Resource.tags.contains([tag]))

        resources = query.all()

        return resources

    def create_resource(self, resource: Resource) -> Resource:
        self.session.add(resource)
        self.session.commit()
        self.session.refresh(resource)
        return resource

    def remove_resource(self, resource_id: str):
        existing_resource = self.session.query(Resource).filter_by(id=resource_id).first()
        if existing_resource:
            self.session.delete(existing_resource)
            self.session.commit()
        else:
            raise ResourceNotFoundException(str(resource_id))

    def get_resource(self, resource_id: str) -> Resource:
        resource = self.session.query(Resource).filter_by(id=resource_id).first()
        if resource:
            return resource
        else:
            raise ResourceNotFoundException(resource_id)

    def block_resource(self, resource_id: str) -> None:
        resource = self.session.query(Resource).filter_by(id=str(resource_id)).first()
        if resource:
            if resource.status == Status.FREE:
                resource.status = Status.BLOCKED

                resource_operation = ResourceOperationOut(id=uuid.uuid4(),
                                                          resource_id=uuid.UUID(resource_id),
                                                          operation=ResourceOperationType.BLOCK)
                self.session.add(ResourceHistory(**resource_operation.dict()))
                self.session.commit()
            else:
                raise ResourceBlockException(str(resource_id))
        else:
            raise ResourceNotFoundException(str(resource_id))

    def release_resource(self, resource_id: str) -> None:
        resource = self.session.query(Resource).filter_by(id=resource_id).first()
        if resource:
            if resource.status == Status.BLOCKED:
                resource.status = Status.FREE
                resource_operation = ResourceOperationOut(id=uuid.uuid4(),
                                                          resource_id=uuid.UUID(resource_id),
                                                          operation=ResourceOperationType.RELEASE)
                self.session.add(ResourceHistory(**resource_operation.dict()))
                self.session.commit()
            else:
                raise ResourceReleaseException(str(resource_id))
        else:
            raise ResourceNotFoundException(str(resource_id))

    def close_connection(self):
        self.session.close()

    def init_db(self):
        if INIT_DB:
            Resource.__table__.create(bind=engine, checkfirst=True)


def create_resource_repository() -> ResourceRepository:
    return ResourceRepositoryPostgreSQL()
