# Roadmap

Items are deliberately prioritized by product risk rather than novelty.

## Before production use

- Add authentication and authorization. Resource variables may contain credentials and must not be returned to every caller.
- Add lease ownership and expiry (`owner_id`, `lease_token`, `expires_at`). Only the owner holding the token should be able to release or renew a resource.
- Replace `init.sql` with versioned Alembic migrations.
- Encrypt secret resource variables at rest or store references to a secrets manager instead of raw values.
- Add metrics, structured logs, tracing, and alerts for lease contention and stale leases.

## Product improvements

- Add a blocking/waiting client or long-poll endpoint with timeout and cancellation. The API currently returns `204` when no resource is available.
- Add idempotency keys for create and claim operations.
- Add resource administration endpoints and audit actor identity.
- Define retention and pagination strategy for resource history.

## Explicitly not planned

- gRPC: add only when a concrete client or performance requirement justifies a second API protocol.
- Moving tags to resource variables: tags are searchable metadata; variables are resource payload and may be secret.
