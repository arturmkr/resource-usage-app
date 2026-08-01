# UserHub Helm Chart

This chart deploys the UserHub application only. It does not install PostgreSQL.

## Install

Create the Secret containing the external database password:

```bash
kubectl create secret generic userhub-database \
  --from-literal=password='<database-password>'
```

Install the chart:

```bash
helm upgrade --install userhub ./charts/userhub \
  --set image.repository='<dockerhub-user>/userhub' \
  --set database.hostname='<postgres-host>'
```

Use a values file instead of command-line overrides for a real environment. Keep passwords out of values files and provide them through `database.existingSecret`.
