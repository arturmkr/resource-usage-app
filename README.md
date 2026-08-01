# resource-usage-app

resource-usage-app coordinates exclusive access to scarce shared resources: test accounts, integration environments, bastion hosts, devices, or anything else that must be used by only one worker at a time.

Resources have searchable tags and a `FREE` or `BLOCKED` status. A client can atomically claim one free resource matching a set of tags, use it, and release it. Every state transition is recorded in an audit history.

## Why it is not just CRUD

Claiming is implemented with a PostgreSQL row lock and `SKIP LOCKED`. Concurrent workers cannot successfully claim the same resource. Direct block and release operations are conditional updates, so a stale client cannot overwrite a newer state.

This project is still a portfolio/reference implementation, not a production secrets broker. See [ToDo.md](ToDo.md) for the security and lease-management work required before production use.

## Run locally

Requirements: Docker Compose, or Python 3.14 plus [uv](https://docs.astral.sh/uv/).

```bash
docker compose up --build
```

The API is available at `http://localhost:10700`; OpenAPI documentation is at `http://localhost:10700/docs`.

For local development:

```bash
docker compose up -d db
uv sync --all-groups
uv run python -m src.app
```

## API workflow

Create a resource:

```bash
curl -X POST http://localhost:10700/resources \
  -H 'content-type: application/json' \
  -d '{"resource_name":"Salesforce QA","tags":["salesforce","qa"],"variables":[]}'
```

Atomically claim one matching resource:

```bash
curl -X POST http://localhost:10700/resources/claim \
  -H 'content-type: application/json' \
  -d '{"tags":["salesforce","qa"],"description":"CI run 123"}'
```

Release it:

```bash
curl -X PUT http://localhost:10700/resources/<resource-id>/release
```

`POST /resources/claim` returns `204 No Content` when no matching resource is currently available. Clients should retry with bounded exponential backoff and jitter.

## Quality checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov
docker build .
```

Integration tests use Testcontainers and require a running Docker daemon. They create and remove their own isolated PostgreSQL container; no manually managed test database is required. If Docker is not running locally, integration tests are skipped.

## Delivery

GitHub Actions runs linting, Helm validation, Testcontainers integration tests, coverage, and publishes a JUnit test report. After a successful `test` job, pull requests build the container without pushing it; pushes and manual runs publish SHA and default-branch `latest` tags to Docker Hub.

Configure these GitHub repository secrets:

- `DOCKERHUB_USERNAME`: Docker Hub account or organization.
- `DOCKERHUB_TOKEN`: Docker Hub access token with permission to push `resource-usage-app`.

Pull requests run tests but do not push images.

## Helm deployment

The chart in `charts/resource-usage-app` deploys only the application. PostgreSQL must already exist, and its password must be stored in a Kubernetes Secret:

```bash
kubectl create secret generic resource-usage-app-database \
  --from-literal=password='<database-password>'

helm upgrade --install resource-usage-app charts/resource-usage-app \
  --set image.repository='<dockerhub-user>/resource-usage-app' \
  --set database.hostname='<postgres-host>'
```

Review `charts/resource-usage-app/values.yaml` for ingress, autoscaling, resources, and external database settings.
