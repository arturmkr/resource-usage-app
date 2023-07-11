import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import ARRAY, func, cast, String

from db_connection import Session
from models.db_models import Resource
from models.pydantic_models import ResourceOut, ResourcesOut, ResourceIn, Status

app = FastAPI(title="resource-usage-app")

# Create a shared session
session = Session()


@app.get("/healthcheck", status_code=200)
async def healthcheck():
    return "OK"


@app.get("/resources", status_code=200)
def get_resources(status: Optional[Status] = Query(None, description="Filter resources by status"),
                  tags: Optional[List[str]] = Query(None, description="Filter resources by tags")) -> ResourcesOut:

    query = session.query(Resource)

    if status:
        query = query.filter(Resource.status == status)
    if tags:
        # query = query.filter(func.json_contains(Resource.tags, tags))
        query = query.filter(
            cast(Resource.tags, String).contains(cast(tags, String))
        )

    resources = query.all()
    resources_out = [ResourceOut(**resource.to_dict()) for resource in resources]

    session.close()

    return ResourcesOut(resources_count=len(resources), resources=resources_out)


@app.post("/resources", status_code=200)
def create_resource(resource_in: ResourceIn) -> ResourceOut:
    resource_out: ResourceOut = ResourceOut(
        id=uuid.uuid4(),
        created_at=datetime.now(),
        **resource_in.dict()
    )
    resource = Resource(**resource_out.dict())

    session.add(resource)
    session.commit()
    return resource


@app.delete("/resources/{resource_id}", status_code=200)
def remove_resource(resource_id: uuid.UUID):
    existing_resource = session.query(Resource).filter_by(id=resource_id).first()
    if existing_resource:
        session.delete(existing_resource)
        session.commit()
        return {"message": "Resource removed"}
    else:
        raise HTTPException(status_code=404, detail="Resource not found")


@app.get("/resources/{resource_id}", status_code=200)
def get_resource(resource_id: uuid.UUID) -> ResourceOut:
    resource = session.query(Resource).filter_by(id=str(resource_id)).first()
    if resource:
        return ResourceOut(**resource.to_dict())
    else:
        raise HTTPException(status_code=404, detail="Resource not found")


@app.put("/resources/{resource_id}/block", status_code=200)
def block_resource(resource_id: str):
    resource = session.query(Resource).filter_by(id=str(resource_id)).first()
    if resource:
        if resource.status == Status.FREE:
            resource.status = Status.BLOCKED
            session.commit()
            session.close()
            return {"message": "Resource blocked"}
        else:
            raise HTTPException(status_code=400, detail="Resource cannot be blocked")
    else:
        raise HTTPException(status_code=404, detail="Resource not found")


@app.put("/resources/{resource_id}/release", status_code=200)
def release_resource(resource_id: str):
    resource = session.query(Resource).filter_by(id=resource_id).first()
    if resource:
        if resource.status == Status.BLOCKED:
            resource.status = Status.FREE
            session.commit()
            return {"message": "Resource released"}
        else:
            raise HTTPException(status_code=400, detail="Resource cannot be released")
    else:
        raise HTTPException(status_code=404, detail="Resource not found")


@app.on_event("shutdown")
def shutdown_event():
    # Close the shared session on application shutdown
    session.close()

# @app.on_event("startup")
# def startup_event():
#     # Create tables if they don't exist on application startup
#     Resource.__table__.create(bind=engine, checkfirst=True)
