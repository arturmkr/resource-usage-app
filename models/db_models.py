from datetime import datetime

from sqlalchemy import Column, Enum, DateTime
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base

from models.enums import Status, ResourceOperationType

Base = declarative_base()


class ToDict:
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "_sa_instance_state"}


class Resource(Base, ToDict):
    __tablename__ = 'resource'

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    tags = Column(ARRAY(String))
    status = Column(Enum(Status), default=Status.FREE)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Resource(id={self.id}, name={self.name} status={self.status})>'


class ResourceHistory(Base, ToDict):
    __tablename__ = 'resource_history'

    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resource_id = Column(String(36))
    operation = Column(Enum(ResourceOperationType))
    user_agent = Column(String(255))
    ip_address = Column(String(30))
    description = Column(String(255))

