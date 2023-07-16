import uuid
from datetime import datetime
from typing import Optional

from config.default import INIT_DB
from db_connection import Session, engine
from exceptions import ResourceNotFoundException, ResourceBlockException, ResourceReleaseException
from models.db_models import Resource, ResourceHistory
from models.enums import Status, ResourceOperationType
from models.pydantic_models import ResourceOut, ResourcesOut, ResourceIn, ResourceOperation


class ResourceService:

    def __init__(self) -> None:
        self.session = Session()

    def get_resources(self, status: Optional[Status], tags: Optional[list[str]]) -> ResourcesOut:
        query = self.session.query(Resource)

        if status:
            query = query.filter(Resource.status == status)
        if tags:
            query = query.filter(Resource.tags.contains(tags))

        resources = query.all()
        resources_out = [ResourceOut(**resource.to_dict()) for resource in resources]

        return ResourcesOut(resources_count=len(resources), resources=resources_out)

    def create_resource(self, resource_in: ResourceIn) -> ResourceOut:
        resource_out: ResourceOut = ResourceOut(
            id=uuid.uuid4(),
            created_at=datetime.now(),
            **resource_in.dict()
        )
        resource = Resource(**resource_out.dict())

        self.session.add(resource)
        self.session.commit()
        return resource

    def remove_resource(self, resource_id: str):
        existing_resource = self.session.query(Resource).filter_by(id=resource_id).first()
        if existing_resource:
            self.session.delete(existing_resource)
            self.session.commit()
        else:
            raise ResourceNotFoundException(str(resource_id))

    def get_resource(self, resource_id: str) -> ResourceOut:
        resource = self.session.query(Resource).filter_by(id=resource_id).first()
        if resource:
            return ResourceOut(**resource.to_dict())
        else:
            raise ResourceNotFoundException(resource_id)

    def block_resource(self, resource_id: str):
        resource = self.session.query(Resource).filter_by(id=str(resource_id)).first()
        if resource:
            if resource.status == Status.FREE:
                resource.status = Status.BLOCKED

                resource_operation = ResourceOperation(id=uuid.uuid4(),
                                                       resource_id=uuid.UUID(resource_id),
                                                       operation=ResourceOperationType.BLOCK)
                self.session.add(ResourceHistory(**resource_operation.dict()))
                self.session.commit()
            else:
                raise ResourceBlockException(str(resource_id))
        else:
            raise ResourceNotFoundException(str(resource_id))

    def release_resource(self, resource_id: str):
        resource = self.session.query(Resource).filter_by(id=resource_id).first()
        if resource:
            if resource.status == Status.BLOCKED:
                resource.status = Status.FREE
                resource_operation = ResourceOperation(id=uuid.uuid4(),
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
