from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from src.models.db_models import Resource
from src.models.enums import Status
from src.resource_repository import ResourceRepositoryPostgreSQL


def test_claim_locks_and_blocks_one_matching_resource():
    session = MagicMock()
    resource = Resource(id=uuid4(), resource_name="Salesforce", tags=["salesforce"], status=Status.FREE)
    session.execute.return_value.scalar_one_or_none.return_value = resource
    lease_token = uuid4()
    lease_expires_at = datetime.now(UTC) + timedelta(hours=4)

    claimed = ResourceRepositoryPostgreSQL().claim(
        session, ["salesforce"], lease_token, "qa-worker-1", lease_expires_at
    )

    assert claimed is resource
    assert resource.status == Status.BLOCKED
    assert resource.lease_token == lease_token
    assert resource.lease_owner == "qa-worker-1"
    assert resource.lease_expires_at == lease_expires_at
    session.flush.assert_called_once()


def test_block_returns_none_when_resource_is_not_free():
    session = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None

    changed = ResourceRepositoryPostgreSQL().block(
        session,
        uuid4(),
        uuid4(),
        "qa-worker-1",
        datetime.now(UTC) + timedelta(hours=4),
    )

    assert changed is None
