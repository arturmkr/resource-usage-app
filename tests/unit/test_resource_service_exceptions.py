# tests/test_resource_service_exceptions.py
from unittest.mock import Mock

import pytest

from exceptions import ResourceNotFoundException
from resource_service import PgResourceService


def test_remove_resource_not_found_exception():
    service = PgResourceService()
    service.resource_repository = Mock()

    service.resource_repository.remove_resource.side_effect = ResourceNotFoundException("1")

    with pytest.raises(ResourceNotFoundException):
        service.remove_resource("1")
