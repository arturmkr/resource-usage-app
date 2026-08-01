from unittest.mock import MagicMock
from uuid import uuid4

from src.models.db_models import Resource
from src.models.enums import Status
from src.resource_repository import ResourceRepositoryPostgreSQL


def test_claim_locks_and_blocks_one_matching_resource():
    session = MagicMock()
    resource = Resource(id=uuid4(), resource_name="Salesforce", tags=["salesforce"], status=Status.FREE)
    session.execute.return_value.scalar_one_or_none.return_value = resource

    claimed = ResourceRepositoryPostgreSQL().claim(session, ["salesforce"])

    assert claimed is resource
    assert resource.status == Status.BLOCKED
    session.flush.assert_called_once()


def test_change_status_returns_none_when_expected_status_does_not_match():
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None

    changed = ResourceRepositoryPostgreSQL().change_status(session, uuid4(), Status.FREE, Status.BLOCKED)

    assert changed is None
