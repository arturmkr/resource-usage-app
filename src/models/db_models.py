from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.models.enums import ResourceOperationType, Status


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class ToDict:
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "_sa_instance_state"}


class Resource(Base, ToDict):
    __tablename__ = "resource"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    resource_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.FREE)
    lease_token: Mapped[UUID | None] = mapped_column(unique=True)
    lease_owner: Mapped[str | None] = mapped_column(String(255))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    variables: Mapped[list[ResourceVariable]] = relationship(
        back_populates="resource", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self):
        return f"<Resource(id={self.id}, name={self.resource_name} status={self.status})>"


class ResourceHistory(Base, ToDict):
    __tablename__ = "resource_history"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    resource_id: Mapped[UUID] = mapped_column(ForeignKey("resource.id", ondelete="CASCADE"), index=True)
    operation: Mapped[ResourceOperationType] = mapped_column(Enum(ResourceOperationType))
    description: Mapped[str | None] = mapped_column(String(255))


class ResourceVariable(Base, ToDict):
    __tablename__ = "resource_variables"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    resource_id: Mapped[UUID] = mapped_column(ForeignKey("resource.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    value: Mapped[str] = mapped_column(String(255))

    resource: Mapped[Resource] = relationship(back_populates="variables")
