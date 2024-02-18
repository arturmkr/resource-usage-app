from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, Enum, DateTime, ForeignKey
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import declarative_base, relationship

from src.models.enums import Status, ResourceOperationType

Base = declarative_base()


class ToDict:
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "_sa_instance_state"}


class Resource(Base, ToDict):
    __tablename__ = 'resource'

    id = Column(UUID, primary_key=True)
    resource_name = Column(String(100), nullable=False)
    description = Column(String(255))
    tags = Column(ARRAY(String))
    status = Column(Enum(Status), default=Status.FREE)
    created_at = Column(DateTime, default=datetime.utcnow)

    variables = relationship("ResourceVariable", back_populates="resource")

    def __repr__(self):
        return f'<Resource(id={self.id}, name={self.resource_name} status={self.status})>'


class ResourceHistory(Base, ToDict):
    __tablename__ = 'resource_history'

    id = Column(UUID, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resource_id = Column(UUID, ForeignKey('resource.id'))
    operation = Column(Enum(ResourceOperationType))
    description = Column(String(255))


class ResourceVariable(Base, ToDict):
    __tablename__ = 'resource_variables'

    id = Column(UUID, primary_key=True, default=uuid4)
    resource_id = Column(UUID, ForeignKey('resource.id'))  # This is the change
    name = Column(String(255))
    value = Column(String(255))

    resource = relationship("Resource", back_populates="variables")
