from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models.db_models import ResourceHistory
from src.models.filters import PaginationParams, ResourceHistoryFilter


class ResourceHistoryRepository(ABC):
    @abstractmethod
    def get_history(
        self, session: Session, filters: ResourceHistoryFilter, pagination: PaginationParams
    ) -> list[ResourceHistory]:
        raise NotImplementedError()

    @abstractmethod
    def add(self, session: Session, history_entry: ResourceHistory) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_history_count(self, session: Session, filters: ResourceHistoryFilter) -> int:
        raise NotImplementedError()


class ResourceHistoryRepositoryPostgreSQL(ResourceHistoryRepository):
    @staticmethod
    def _apply_filters(query, filters: ResourceHistoryFilter):
        if filters.resource_id:
            query = query.filter(ResourceHistory.resource_id == UUID(filters.resource_id))

        if filters.operation:
            query = query.filter(ResourceHistory.operation == filters.operation)

        if filters.start_date:
            query = query.filter(ResourceHistory.created_at >= filters.start_date)

        if filters.end_date:
            query = query.filter(ResourceHistory.created_at <= filters.end_date)

        return query

    def get_history_count(self, session: Session, filters: ResourceHistoryFilter) -> int:
        query = session.query(func.count(ResourceHistory.id))
        query = self._apply_filters(query, filters)
        return query.scalar()

    def get_history(
        self, session: Session, filters: ResourceHistoryFilter, pagination: PaginationParams
    ) -> list[ResourceHistory]:
        query = session.query(ResourceHistory)
        query = self._apply_filters(query, filters)
        return query.order_by(ResourceHistory.created_at.desc()).offset(pagination.skip).limit(pagination.limit).all()

    def add(self, session: Session, history_entry: ResourceHistory) -> ResourceHistory:
        session.add(history_entry)
        session.flush()
        session.refresh(history_entry)
        return history_entry


def create_resource_history_repository() -> ResourceHistoryRepository:
    return ResourceHistoryRepositoryPostgreSQL()
