import pytest

from src.rest_api import app


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def simple_fixture():
    return "simple_value"
