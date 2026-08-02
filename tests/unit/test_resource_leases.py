from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.exceptions import ResourceLeaseValidationException
from src.models.db_models import Resource
from src.models.enums import ResourceOperationType, Status
from src.models.pydantic_models import LeaseRequest, ReleaseRequest, RenewRequest
from src.resource_service import PgResourceService


@contextmanager
def fake_session():
    yield Mock()


def test_lease_ttl_cannot_exceed_configured_maximum(monkeypatch):
    service = PgResourceService()
    monkeypatch.setattr(
        "src.resource_service.get_settings",
        lambda: SimpleNamespace(app_default_lease_ttl_minutes=240, app_max_lease_ttl_minutes=480),
    )

    with pytest.raises(ResourceLeaseValidationException, match="480 minutes"):
        service._create_lease(481)


def test_block_resource_returns_lease_token_and_writes_history(monkeypatch):
    service = PgResourceService()
    service.resource_repository = Mock()
    service.resource_history_repository = Mock()
    resource_id = uuid4()

    def block(_session, _resource_id, lease_token, lease_owner, lease_expires_at):
        return Resource(
            id=resource_id,
            resource_name="Salesforce QA",
            tags=["salesforce"],
            status=Status.BLOCKED,
            lease_token=lease_token,
            lease_owner=lease_owner,
            lease_expires_at=lease_expires_at,
        )

    service.resource_repository.block.side_effect = block
    monkeypatch.setattr("src.resource_service.get_db_session", fake_session)

    result = service.block_resource(resource_id, LeaseRequest(lease_owner="qa-user-1", ttl_minutes=120))

    assert result.id == resource_id
    assert result.lease_token
    assert result.lease_owner == "qa-user-1"
    service.resource_history_repository.add.assert_called_once()
    history_entry = service.resource_history_repository.add.call_args.args[1]
    assert history_entry.operation == ResourceOperationType.BLOCK


def test_release_resource_requires_matching_lease_token(monkeypatch):
    service = PgResourceService()
    service.resource_repository = Mock()
    service.resource_history_repository = Mock()
    resource_id = uuid4()
    lease_token = uuid4()
    released_resource = Resource(
        id=resource_id,
        resource_name="Salesforce QA",
        tags=["salesforce"],
        status=Status.FREE,
    )
    service.resource_repository.release.return_value = released_resource
    monkeypatch.setattr("src.resource_service.get_db_session", fake_session)

    service.release_resource(resource_id, ReleaseRequest(lease_token=lease_token))

    service.resource_repository.release.assert_called_once()
    assert service.resource_repository.release.call_args.args[2] == lease_token
    history_entry = service.resource_history_repository.add.call_args.args[1]
    assert history_entry.operation == ResourceOperationType.RELEASE


def test_renew_resource_extends_existing_lease(monkeypatch):
    service = PgResourceService()
    service.resource_repository = Mock()
    service.resource_history_repository = Mock()
    resource_id = uuid4()
    lease_token = uuid4()

    def renew(_session, _resource_id, _lease_token, lease_expires_at):
        return Resource(
            id=resource_id,
            resource_name="Salesforce QA",
            tags=["salesforce"],
            status=Status.BLOCKED,
            lease_token=lease_token,
            lease_expires_at=lease_expires_at,
        )

    service.resource_repository.renew.side_effect = renew
    monkeypatch.setattr("src.resource_service.get_db_session", fake_session)

    result = service.renew_resource(resource_id, RenewRequest(lease_token=lease_token, ttl_minutes=60))

    assert result.lease_token == lease_token
    assert result.lease_expires_at > datetime.now(UTC)
    history_entry = service.resource_history_repository.add.call_args.args[1]
    assert history_entry.operation == ResourceOperationType.RENEW


def test_cleanup_releases_expired_leases_and_writes_history(monkeypatch):
    service = PgResourceService()
    service.resource_repository = Mock()
    service.resource_history_repository = Mock()
    expired_resource = Resource(
        id=uuid4(),
        resource_name="Salesforce QA",
        tags=["salesforce"],
        status=Status.FREE,
        lease_expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    service.resource_repository.release_expired_leases.return_value = [expired_resource]
    monkeypatch.setattr("src.resource_service.get_db_session", fake_session)

    released_count = service.release_expired_leases()

    assert released_count == 1
    history_entry = service.resource_history_repository.add.call_args.args[1]
    assert history_entry.operation == ResourceOperationType.EXPIRE
