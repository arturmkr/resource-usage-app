# resource-coordinator Helm Chart

This chart deploys the resource-coordinator application only. It does not install PostgreSQL.

## Install

Create the Secret containing the external database password:

```bash
kubectl create secret generic resource-coordinator-database \
  --from-literal=password='<database-password>'
```

Install the chart:

```bash
helm upgrade --install resource-coordinator ./charts/resource-coordinator \
  --set image.repository='<dockerhub-user>/resource-coordinator' \
  --set database.hostname='<postgres-host>'
```

Use a values file instead of command-line overrides for a real environment. Keep passwords out of values files and provide them through `database.existingSecret`.

Lease settings can be changed in `values.yaml`:

```yaml
lease:
  defaultTtlMinutes: 240
  maxTtlMinutes: 480
  cleanupIntervalMinutes: 10
  cleanupEnabled: true
```
