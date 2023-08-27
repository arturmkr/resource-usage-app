from abc import abstractmethod, ABC
from typing import List, Type
from uuid import UUID

from sqlalchemy import func

from db_connection import DbSession
from models.db_models import ResourceHistory
from models.filters import ResourceHistoryFilter, PaginationParams


class ResourceHistoryRepository(DbSession, ABC):
    @abstractmethod
    def get_history(self, filters: ResourceHistoryFilter, pagination: PaginationParams) -> List[ResourceHistory]:
        raise NotImplementedError()

    @abstractmethod
    def add(self, history_entry: ResourceHistory) -> None:
        raise NotImplementedError()

    @abstractmethod
    def get_history_count(self, filters: ResourceHistoryFilter) -> int:
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

    def get_history_count(self, filters: ResourceHistoryFilter) -> int:
        query = self.session.query(func.count(ResourceHistory.id))
        query = self._apply_filters(query, filters)
        return query.scalar()

    def get_history(self, filters: ResourceHistoryFilter, pagination: PaginationParams) -> list[Type[ResourceHistory]]:
        query = self.session.query(ResourceHistory)
        query = self._apply_filters(query, filters)
        return query.offset(pagination.skip).limit(pagination.limit).all()

    def add(self, history_entry: ResourceHistory) -> ResourceHistory:
        self.session.add(history_entry)
        self.session.flush()
        self.session.refresh(history_entry)
        return history_entry


def create_resource_history_repository() -> ResourceHistoryRepository:
    return ResourceHistoryRepositoryPostgreSQL()
