# resource-usage-app Helm Chart

This chart deploys the resource-usage-app application only. It does not install PostgreSQL.

## Install

Create the Secret containing the external database password:

```bash
kubectl create secret generic resource-usage-app-database \
  --from-literal=password='<database-password>'
```

Install the chart:

```bash
helm upgrade --install resource-usage-app ./charts/resource-usage-app \
  --set image.repository='<dockerhub-user>/resource-usage-app' \
  --set database.hostname='<postgres-host>'
```

Use a values file instead of command-line overrides for a real environment. Keep passwords out of values files and provide them through `database.existingSecret`.
