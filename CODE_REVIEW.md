# Code Review

Review target: portfolio project for a senior platform engineering role.

## Executive summary

The original project communicated a useful idea, but its most important guarantee was not actually enforced: two clients could observe the same free resource and both block it. The updated implementation makes claiming exclusive at the database level and modernizes the project to Python 3.14, uv, current dependencies, reproducible CI, and a non-root runtime container.

The project is now a credible reference implementation. It is not yet a production-ready resource broker because it has no authenticated lease owner, lease expiry, or secret-management boundary.

## Fixed findings

### Critical: non-exclusive resource acquisition

The old flow performed a read followed by an update. Concurrent clients could both read `FREE` before either transaction committed.

`POST /resources/claim` now selects one matching free resource using `FOR UPDATE SKIP LOCKED` and blocks it in the same transaction. Direct block and release operations use conditional updates and return `409 Conflict` when the expected state no longer matches.

### High: obsolete and non-reproducible toolchain

- Replaced Python 3.9 and Pipenv with Python 3.14, `pyproject.toml`, and `uv.lock`.
- Upgraded FastAPI, Pydantic, SQLAlchemy, psycopg, pytest, coverage, and Ruff.
- Added strict linting, formatting, bounded pagination, and Python 3.14 compilation checks.

### High: fragile CI

The old workflow required repository secrets for a disposable test database, installed Pipenv before Python setup, installed a PostgreSQL client, and executed `init.sql` manually.

CI now uses uv caching, Ruff, the complete test suite, coverage, and a container build. Integration tests own an isolated PostgreSQL instance through Testcontainers, so CI no longer contains database credentials, service configuration, or `psql`. The old `psql` step existed solely to create tables before integration tests.

### High: container and local environment drift

- Replaced the floating PostgreSQL image tag with a pinned PostgreSQL image.
- Added a multi-stage Python 3.14 image using uv.
- Runs the application as a non-root user.
- Restored the application service in Compose and added a valid database healthcheck.
- Added `.dockerignore`.

### Medium: API and model correctness

- Added centralized exception handlers.
- Resource IDs are validated as UUIDs at the API boundary.
- State conflicts return `409`; invalid inputs return `422`.
- Create returns `201`.
- Pagination is deterministic and bounded.
- Mutable Pydantic defaults were removed.
- Timestamps are timezone-aware.
- SQLAlchemy models now use typed 2.x mappings and cascading foreign keys.
- Added indexes for free-resource tag lookup and resource history.

### Medium: misleading roadmap

Completed or unjustified items were removed. gRPC is explicitly deferred until a real requirement exists. The roadmap now prioritizes ownership, expiry, auth, secrets, migrations, and observability.

## Remaining production blockers

1. **No lease ownership:** any caller can release a blocked resource. Add an opaque lease token and require it for renew/release.
2. **No expiry or recovery:** a crashed worker can block a resource forever. Add `expires_at`, renewal, and stale-lease recovery.
3. **No authentication or authorization:** resource variables may contain credentials and are currently returned by the API.
4. **No secrets boundary:** values should be encrypted or represented as references to a secrets manager.
5. **No versioned migrations:** `init.sql` is acceptable for the demo but should be replaced by Alembic before schema evolution.
6. **No contention observability:** add structured logs, metrics, traces, and alerts for claim latency, conflicts, and expired leases.
7. **No real waiting contract:** clients currently retry a `204` response. A supported client library or bounded long-poll endpoint should define timeout, cancellation, backoff, and jitter.

## Test assessment

The updated unit suite covers API contracts and atomic repository behavior. Integration coverage includes the main business flow: create, exclusive claim, unavailable response, release, and delete.

A concurrent PostgreSQL integration test runs two workers against one matching resource and proves that exactly one receives the claim.
