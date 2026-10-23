# README - Despliegue de Apache DevLake (v1.0.3-beta14)

Este repositorio contiene los manifiestos de Kubernetes y la configuración GitOps mediante **Flux CD** (Kustomize + Helm) para el despliegue de **Apache DevLake** en el entorno de Producción (`103-beta-prd`).

---

## 🏗️ Estructura del Proyecto

```text
├── 📁 alerting
│   └── ⚙️ alertmanagerconfig_devlake.yaml
├── 📁 dashboards
│   ├── ⚙️ DORA (Team Jira) - nuam.json
│   ├── ⚙️ GitHub-nuam.json
│   ├── ⚙️ Jira-nuam.json
│   └── ⚙️ devlake-grafana-dashboard-jira-nuam.yaml
├── 📁 db
│   ├── ⚙️ mariadb-backup-cronjob.yaml
│   ├── ⚙️ grafana-datasource-mariadb.yaml
│   ├── ⚙️ mariadb-configmap.yaml
│   ├── ⚙️ mariadb-external-secret.yaml
│   ├── ⚙️ mariadb-secret.yaml
│   ├── ⚙️ mariadb-service.yaml
│   └── ⚙️ mariadb-statefulset.yaml
├── 📝 README.md
├── ⚙️ gw-route-http-redir.yaml
├── ⚙️ gw-route-http.yaml
├── ⚙️ kustomization.yaml
├── ⚙️ namespace.yaml
└── ⚙️ release.yaml
```

---

## 📌 NOTA IMPORTANTE: Gestión de Secretos

> ⚠️ **NOTA DE DEPRECIACIÓN / REFERENCIA:**
> El manifiesto **`db/mariadb-external-secret.yaml`** corresponde a la **configuración anterior** utilizada para la obtención de secretos mediante HashiCorp Vault / External Secrets Operator.
> 
> **Actualmente NO está en uso** en el flujo de reconciliación activo de Kustomize (`kustomization.yaml`), pero **se conserva en el repositorio únicamente como guía/referencia técnica** para futuras migraciones o integraciones con Vault.
> 
> En la arquitectura actual, los secretos son provistos y gestionados a través de **`db/mariadb-secret.yaml`**.

---

## 🚀 Arquitectura y Componentes

1. **Base de Datos (MariaDB):**
   - **Tipo:** `StatefulSet` (`mariadb:10.6`)
   - **Servicio:** `devlake-mariadb.devlake.svc.cluster.local:3306`
   - **Persistencia:** VolumeClaimTemplate de `10Gi` (`ReadWriteOnce`).
   - **Configuración:** Optimizada mediante `mariadb-configmap.yaml` (InnoDB Buffer Pool 1G, max_connections 500, UTF8mb4).

2. **Core DevLake & Dashboard:**
   - Desplegado mediante **Flux HelmRelease** (`version: 1.0.3-beta14`).
   - **Lake Core:** Conectado a la MariaDB externa via `devlake-db-secret`. Incluye initContainer de espera en puerto 3306.
   - **UI (Config UI):** Puerto interno 4000 con autenticación básica habilitada (`devlake-ui-auth`).
   - **Grafana:** Dashboard integrado expuesto bajo el subpath `/grafana`.

3. **Ingreso y Redirección (Gateway API):**
   - **Dominio:** `devlake.nuamexchange.com`
   - **Rutas (HTTPS):**
     - `/` ➡️ `devlake-ui` (Puerto 4000)
     - `/grafana` ➡️ `devlake-grafana` (Puerto 80)
   - Redirección automática de HTTP a HTTPS mediante `HTTPRoute` (`gw-route-http-redir.yaml`).

4. **Alertamiento (Opcional / Integración):**
   - Contiene `AlertmanagerConfig` para enrutamiento de alertas severas (Critical ➡️ Teams & Email; Warning ➡️ Email; Info ➡️ Teams).

5. **Backup de Base de Datos (CronJob):**

- Manifiesto: db/devlake-backup-cronjob.yaml
- Schedule: 0 2 * * 6 (todos los sábados a las 2:00 AM).
- Imagen: mcr.microsoft.com/azure-cli:latest

Flujo:

   1. mariadb-dump con --single-transaction --routines --triggers sobre la base lake.
   2. Compresión gzip del dump (devlake_backup_DD-MM-YYYY.sql.gz).
   3. Upload a Azure Blob Storage (db-backups-prod) bajo el prefijo Devlake/.
   4. Retención: Conserva únicamente los 2 archivos más recientes.

Secretos requeridos:

- mariadb-auth → key mariadb-password
- azure-backup-secret → key connection-string

---

## 🛠️ Despliegue con Flux CD

El despliegue está administrado por Kustomize mediante `kustomization.yaml`.

Para verificar la reconciliación del recurso desde la CLI de Flux:

```bash
flux reconcile kustomization kustom-devlake --with-source
```

Para verificar los pods desplegados en el namespace:

```bash
kubectl get pods -n devlake
```