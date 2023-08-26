from abc import abstractmethod, ABC
from typing import List

from db_connection import session_factory
from models.db_models import ResourceHistory
from models.filters import ResourceHistoryFilter


class ResourceHistoryRepository(ABC):
    @abstractmethod
    def get_history(self, filters: ResourceHistoryFilter) -> List[ResourceHistory]:
        raise NotImplementedError()


class ResourceHistoryRepositoryPostgreSQL(ResourceHistoryRepository):
    def __init__(self) -> None:
        self.session = session_factory()

    def get_history(self, filters: ResourceHistoryFilter) -> List[ResourceHistory]:
        query = self.session.query(ResourceHistory)

        if filters.resource_id:
            query = query.filter(ResourceHistory.resource_id == filters.resource_id)

        if filters.operation:
            query = query.filter(ResourceHistory.operation == filters.operation)

        if filters.start_date:
            query = query.filter(ResourceHistory.created_at >= filters.start_date)

        if filters.end_date:
            query = query.filter(ResourceHistory.created_at <= filters.end_date)

        return query.all()


def create_resource_history_repository() -> ResourceHistoryRepository:
    return ResourceHistoryRepositoryPostgreSQL()
