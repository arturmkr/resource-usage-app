import uuid

import docker
import pytest
from docker.errors import DockerException
from testcontainers.postgres import PostgresContainer

from src.db_connection import configure_database, get_db_session, get_engine, reset_database_configuration
from src.models.db_models import Base, Resource


@pytest.fixture(scope="session", autouse=True)
def postgres():
    try:
        docker.from_env().ping()
    except DockerException as exc:
        pytest.skip(f"Docker daemon is required for integration tests: {exc}")

    with PostgresContainer("postgres:17.6-alpine", driver="psycopg") as container:
        configure_database(container.get_connection_url())
        engine = get_engine()
        Base.metadata.create_all(engine)
        yield container
        Base.metadata.drop_all(engine)
        reset_database_configuration()


@pytest.fixture
def create_test_resource_for_update(postgres):
    with get_db_session() as db:
        test_resource = Resource(id=uuid.uuid4(), resource_name="Test Resource", description="Original description")
        db.add(test_resource)
        db.commit()

        yield test_resource.id

        resource = db.get(Resource, test_resource.id)
        if resource:
            db.delete(resource)
