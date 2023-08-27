- [ ] check docker dependencies
- [ ] id and created_at generator
- [ ] add auth
- [ ] add gRPC
- [ ] add pagination
- [ ] add description for block operation
- [ ] add foreign keys

==============================================
1. Managing Sessions within Each Method:

class ResourceHistoryRepositoryPostgreSQL(ResourceHistoryRepository):

    def get_history(self, filters: ResourceHistoryFilter) -> List[ResourceHistory]:
        session = session_factory()  # open session here
        try:
            query = session.query(ResourceHistory)

            # ... (rest of your filter logic)

            return query.all()
        finally:
            session.close()  # close session here

==============================================

Centralize Error Handling:

# in rest_api.py
from fastapi import HTTPException, status

@app.exception_handler(ResourceNotFoundException)
def handle_resource_not_found_exception(request: Request, exc: ResourceNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": str(exc)},
    )

@app.exception_handler(ResourceReleaseException)
def handle_resource_release_exception(request: Request, exc: ResourceReleaseException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": str(exc)},
    )

@app.put("/resources/{resource_id}/release", status_code=200)
def release_resource(resource_id: str):
    resource_service.release_resource(resource_id)
    return {"message": f"Resource {resource_id} was released"}

==============================================
1. Implementing Context Manager in Base Class



from sqlalchemy.orm import Session
from abc import ABC, abstractmethod

class ResourceHistoryRepository(ABC):

    def __enter__(self) -> 'ResourceHistoryRepository':
        self.session = session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    @abstractmethod
    def get_history(self, filters: Any) -> List[Any]:
        pass

class ResourceHistoryRepositoryPostgreSQL(ResourceHistoryRepository):

    def get_history(self, filters: Any) -> List[Any]:
        query = self.session.query(ResourceHistory)
        # ... (rest of your filter logic)
        return query.all()


class PgResourceService:

    def __init__(self) -> None:
        self.resource_repo: ResourceRepository = ResourceRepositoryPostgreSQL()
        self.resource_history_repo: ResourceHistoryRepository = ResourceHistoryRepositoryPostgreSQL()

    def get_resources_history(self, filters: Any) -> List[Any]:
        with self.resource_history_repo as repo:
            return repo.get_history(filters)

    # ... other methods ...


==============================================
