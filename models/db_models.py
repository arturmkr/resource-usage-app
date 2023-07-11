from abc import ABC
from datetime import datetime

from sqlalchemy import Column, Enum, DateTime


import json
from typing import Optional

from sqlalchemy import ARRAY, String, TypeDecorator
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import operators

from models.enums import Status

# Base class for declarative models
Base = declarative_base()


class ArrayType(TypeDecorator):
    impl = ARRAY

    def process_bind_param(self, value: Optional[list[str]], dialect: Dialect) -> str:
        return json.dumps(value)

    def process_result_value(self, value: str, dialect: Dialect) -> Optional[list[str]]:
        if value is not None:
            return json.loads(value)

    def coerce_compared_value(self, op, value):
        if op in (
            operators.like_op,
            operators.notlike_op,
            operators.ilike_op,
            operators.notilike_op,
        ):
            return String()
        else:
            return self


class ToDict:
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "_sa_instance_state"}


# Resource model
class Resource(Base, ToDict):
    __tablename__ = 'resource'

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    # tags = Column(ArrayType(String), nullable=True, default=[])
    tags = Column(JSON, nullable=True, default=[])
    status = Column(Enum(Status), default=Status.FREE)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Resource(id={self.id}, name={self.name} status={self.status})>'


