## Comandos con velero

- Install CRDS

```sh
velero install --crds-only
```

- Credenciales
  
```sh
[default]
aws_access_key_id = KVQKn0IQ8uCpvkxaM8Uv
aws_secret_access_key = EVqNUTTjMExvj6r57on8u4CD4izO4tV9sISTmjzW
```

- Crear provider

```sh
velero install \
    --provider aws \
    --plugins velero/velero-plugin-for-aws:v1.2.1 \
    --bucket velero-keycloak-backup \
    --secret-file ./credentials-velero \
    --use-volume-snapshots=false \
    --backup-location-config region=minio,s3ForcePathStyle="true",s3Url=http://minio-s3.minio-s3.svc:9000
```

- Crear backup
  
```sh
velero backup create backup-keycloak-chi \
    --include-namespaces keycloak-chi \
    --snapshot-volumes=true
    --wait
```

- Restore

```sh
velero restore create res-keycloak-chi  \
  --from-backup backup-keycloak-chi \
  --namespace-mappings keycloak-chi:keycloak-chi-res
```

- Desinstalar
  
```sh
velero uninstall
```