# README - Despliegue de Apache DevLake (v1.0.3-beta14)

Este repositorio contiene los manifiestos de Kubernetes y la configuración GitOps mediante **Flux CD** (Kustomize + Helm) para el despliegue de **Apache DevLake** en el entorno de Producción (`103-beta-prd`).

---

## 🏗️ Estructura del Proyecto

```text
📂 103-beta-prd/
├── alerting/
│   └── alertmanagerconfig_devlake.yaml  # Configuración de alertas para Alertmanager (Teams / Email)
├── db/
│   ├── mariadb-configmap.yaml           # Parámetros de rendimiento e InnoDB para MariaDB
│   ├── mariadb-external-secret.yaml    # ⚠️ CONFIGURACIÓN ANTERIOR (ExternalSecret / Vault) - NO EN USO
│   ├── mariadb-secret.yaml             # Secretos y ConfigMaps locales activos para la base de datos y UI
│   ├── mariadb-service.yaml            # Servicio interno ClusterIP para MariaDB (puerto 3306)
│   └── mariadb-statefulset.yaml        # StatefulSet para MariaDB (10.6) con PVC de 10Gi
├── gw-route-http.yaml                   # HTTPRoute (Gateway API) para enrutar `/` (UI) y `/grafana`
├── gw-route-http-redir.yaml             # HTTPRoute para redirección HTTP -> HTTPS (301)
├── helmrepo.yaml                        # Repositorio Helm oficial de Apache DevLake
├── kustomization.yaml                   # Manifiesto principal de Kustomize
├── namespace.yaml                       # Definición del Namespace `devlake`
└── release.yaml                         # HelmRelease de Flux CD (DevLake, UI, Grafana)
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

kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.1/standard-install.yaml
kubectl apply -f https://apache.github.io/devlake-helm-chart 

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