# resource-coordinator

`resource-coordinator` is a service for reserving shared resources that must be used by only one client at a time.

It can be used by people, CI jobs, or automation scripts.

Good examples are test accounts, shared environments, devices, demo tenants, bastion hosts, or migration windows.

## Main Idea

A resource has tags and a status:

- `FREE`
- `BLOCKED`

There are two ways to take a resource:

- list free resources by tags and block the exact resource you want;
- claim any free resource by tags and let the backend choose one.

This keeps both use cases:

- a person can choose a concrete resource;
- an automation job can say "give me any free resource with these tags".

Example: a QA team can share expensive Salesforce accounts. The same pattern also works for shared environments, devices, demo tenants, or internal tools.

## Why The Locking Is Important

When several clients ask for the same type of resource at the same time, PostgreSQL row locking makes sure that only one client gets each resource.

Direct block and release operations are also conditional. A resource can be blocked only if it is currently `FREE`, and released only with the correct lease token.

Technical detail: `claim` uses `SELECT ... FOR UPDATE SKIP LOCKED`, so concurrent workers do not block each other and do not receive the same database row.

## Lease Logic

When a client blocks or claims a resource, the API returns:

- `lease_token`
- `lease_owner`
- `lease_expires_at`

The `lease_token` is needed for release and renew. It is not returned from normal `GET /resources` responses, because other clients should not be able to release someone else's resource just by reading the list.

Default lease settings:

```env
APP_DEFAULT_LEASE_TTL_MINUTES=240
APP_MAX_LEASE_TTL_MINUTES=480
APP_LEASE_CLEANUP_INTERVAL_MINUTES=10
```

So by default a resource is booked for 4 hours, and the maximum is 8 hours. Expired leases are cleaned by a background task every 10 minutes.

## API Examples

Create a resource:

```bash
curl -X POST http://localhost:10700/resources \
  -H 'content-type: application/json' \
  -d '{"resource_name":"Salesforce QA","tags":["salesforce","qa"],"variables":[]}'
```

Find free resources by tag:

```bash
curl 'http://localhost:10700/resources?status=FREE&tags=salesforce'
```

Block exact resource:

```bash
curl -X PUT http://localhost:10700/resources/<resource-id>/block \
  -H 'content-type: application/json' \
  -d '{"lease_owner":"qa-user-1","ttl_minutes":240,"description":"manual testing"}'
```

Claim any matching resource:

```bash
curl -X POST http://localhost:10700/resources/claim \
  -H 'content-type: application/json' \
  -d '{"tags":["salesforce"],"lease_owner":"ci-run-123","ttl_minutes":240}'
```

Release resource:

```bash
curl -X PUT http://localhost:10700/resources/<resource-id>/release \
  -H 'content-type: application/json' \
  -d '{"lease_token":"<lease-token>"}'
```

Renew resource:

```bash
curl -X PUT http://localhost:10700/resources/<resource-id>/renew \
  -H 'content-type: application/json' \
  -d '{"lease_token":"<lease-token>","ttl_minutes":240}'
```

`POST /resources/claim` returns `204 No Content` when no matching resource is free. The client can wait and retry.

## Run Locally

Requirements: Docker Compose, or Python 3.14 with `uv`.

```bash
docker compose up --build
```

The API is available at `http://localhost:10700`.

OpenAPI docs:

```text
http://localhost:10700/docs
```

For local development:

```bash
docker compose up -d db
uv sync --all-groups
uv run python -m src.app
```

## Quality Checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov
docker build .
```

Integration tests use Testcontainers. They start their own PostgreSQL container, so Docker must be running.

## CI And Delivery

GitHub Actions runs:

- linting;
- unit and integration tests;
- coverage;
- JUnit test report;
- Helm chart validation;
- Docker image build.

After tests pass, the build job can push the image to Docker Hub.

Required GitHub repository secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

## Helm

The chart is in `charts/resource-coordinator`.

It deploys only the application. PostgreSQL should already exist.

Example:

```bash
kubectl create secret generic resource-coordinator-database \
  --from-literal=password='<database-password>'

helm upgrade --install resource-coordinator charts/resource-coordinator \
  --set image.repository='<dockerhub-user>/resource-coordinator' \
  --set database.hostname='<postgres-host>'
```
