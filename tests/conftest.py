import uuid

import pytest

from src.db_connection import get_db_session
from src.models.db_models import Resource


@pytest.fixture
def create_test_resource_for_update():
    with get_db_session() as db:
        # Create an instance of the Resource model
        test_resource = Resource(
            id=uuid.uuid4(),
            resource_name="Test Resource",
            description="Original description"
        )
        db.add(test_resource)
        db.commit()

        yield test_resource.id

        # Cleanup after test
        db.delete(test_resource)
        db.commit()


@pytest.fixture
def simple_fixture():
    return "simple_value"
