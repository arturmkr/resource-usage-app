from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_claim_is_exclusive_until_resource_is_released():
    create_response = client.post(
        "/resources",
        json={"resource_name": "Salesforce QA", "tags": ["salesforce", "qa"]},
    )
    assert create_response.status_code == 201
    resource_id = create_response.json()["id"]

    first_claim = client.post("/resources/claim", json={"tags": ["salesforce"]})
    second_claim = client.post("/resources/claim", json={"tags": ["salesforce"]})

    assert first_claim.status_code == 200
    assert first_claim.json()["id"] == resource_id
    assert second_claim.status_code == 204

    assert client.put(f"/resources/{resource_id}/release").status_code == 200
    assert client.delete(f"/resources/{resource_id}").status_code == 200


def test_concurrent_workers_cannot_claim_the_same_resource():
    unique_tag = str(uuid4())
    create_response = client.post(
        "/resources",
        json={"resource_name": "Contended Salesforce QA", "tags": [unique_tag]},
    )
    resource_id = create_response.json()["id"]

    def claim():
        with TestClient(app) as worker_client:
            return worker_client.post("/resources/claim", json={"tags": [unique_tag]})

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: claim(), range(2)))

    assert sorted(response.status_code for response in responses) == [200, 204]

    assert client.put(f"/resources/{resource_id}/release").status_code == 200
    assert client.delete(f"/resources/{resource_id}").status_code == 200
