# Roadmap

## Should do

- Add auth.
- Decide how to handle secret variables: hide them from list responses, encrypt them, or store only references to a secret manager.
- Connect `lease_token` to a real user or service account.
- Replace `init.sql` with Alembic migrations.
- Add metrics and structured logs.

## Nice To Have

- Add a wait endpoint instead of forcing clients to retry after `204`.
- Add idempotency keys for claim requests.
- Add resource update endpoints: edit name, tags, description, and variables.
- Add admin force-release for stuck resources.
- Add cleanup rules for old history records.

## Not Planned For Now

- gRPC.
- Moving tags into variables.