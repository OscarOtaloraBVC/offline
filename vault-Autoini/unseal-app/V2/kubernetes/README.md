# Vault Unseal Automation — Despliegue Kubernetes

## 1. Descripción

Este repositorio contiene los manifiestos Kubernetes (gestionados con **Kustomize**) para el despliegue de la solución de **auto-unseal de HashiCorp Vault**, compuesta por dos componentes:

- **Backend** (`vault-unseal-backend`): API que expone la lógica de automatización del proceso de unseal de Vault. Se autentica ante la API de Kubernetes mediante un `ServiceAccount` con permisos RBAC específicos para monitorear, listar y reiniciar (`delete`/`exec`) los pods de Vault que se encuentren en estado *sealed*.
- **Frontend** (`vault-unseal-frontend`): interfaz web que consume la API del backend para visualizar el estado del unseal y permitir su operación manual cuando se requiera.

La solución se despliega en el namespace **`vault`** y persiste su estado operativo (claves/tokens fragmentados) en una base de datos SQLite almacenada en un `PersistentVolumeClaim`.

> ⚠️ Este proyecto corresponde al método de auto-unseal **nativo/simple** (control de pods vía API de Kubernetes), una de las alternativas evaluadas frente a los enfoques basados en AWS KMS / IAM Roles Anywhere.

---

## 2. Arquitectura / Diagrama

```
                                    Namespace: vault
        ┌───────────────────────────────────────────────────────────────────────────────────────────┐
        │                                                                                           │
        │   ┌───────────────┐        HTTP :80         ┌──────────────────────────┐                  │
Usuario │   │   frontend-    │◄───────────────────────┤   vault-unseal-          │                  │
 ───────┼──►│   service      │                        │   frontend (Pod)         │                  │
        │   │ (ClusterIP:80) │───────────────────────►│  rbac-registry/          │                  │
        │   └───────────────┘   sirve la SPA          │  vault-autoini-front     │                  │
        │                                             └──────────┬───────────────┘                  │
        │                                                        │ BACKEND_URL                      │
        │                                                        │ (http:8000)                      │
        │                                                        ▼                                  │
        │   ┌───────────────┐        HTTP :8000       ┌──────────────────────────┐                  │
        │   │  backend-      │◄───────────────────────┤   vault-unseal-          │                  │
        │   │  service       │                        │   backend (Pod)          │                  │
        │   │ (ClusterIP:8000)│──────────────────────►│  rbac-registry/          │                  │
        │   └───────────────┘                          │  vault-autoini-back     │                  │
        │                                              │                         │                  │
        │                                              │  ServiceAccount:        │                  │
        │                                              │  vault-unseal-manager   │                  │
        │                                              └───┬────────────┬────────┘                  │
        │                                                  │            │                           │
        │                              ConfigMap           │            │  Secret                   │
        │                       vault-unseal-config ───────┘            └──── vault-unseal-secrets  │
        │                        (ALGORITHM, VAULT_ADDR,                 (jwt-secret, admin-*,      │
        │                         DATABASE_URL, LOG_LEVEL...)             vault-unseal-password)    │
        │                                                  │                                        │
        │                                                  │ mount /data                            │
        │                                                  ▼                                        │
        │                                          ┌────────────────────┐                           │
        │                                          │  PVC:              │                           │
        │                                          │  vault-unseal-data │                           │
        │                                          │  (1Gi, local-path) │                           │
        │                                          └────────────────────┘                           │
        │                                                  │                                        │
        │                        API Kubernetes (get/list/delete pods,                              │
        │                        pods/exec create, pods/log get)                                    │
        │                                                  │                                        │
        │                                                  ▼                                        │
        │                                          ┌────────────────────┐                           │
        │                                          │  Pods de Vault     │                           │
        │                                          │  (namespace vault) │                           │
        │                                          └────────────────────┘                           │
        │                                                  │                                        │
        │                                                  ▼                                        │
        │                                          Vault API                                        │
        │                                          http://vault.vault:8200                          │  
        └───────────────────────────────────────────────────────────────────────────────────────────┘
```

**Flujo resumido:**
1. El usuario accede al frontend a través del `Service` `vault-unseal-frontend` (puerto 80).
2. El frontend consume la API del backend usando la variable `BACKEND_URL` (`vault-unseal-backend.vault.svc.cluster.local:8000`).
3. El backend, autenticado con el `ServiceAccount` `vault-unseal-manager`, consulta el estado de los pods de Vault y ejecuta acciones de remediación (`delete`/`exec`) usando los permisos RBAC definidos en `rbac.yaml`.
4. El backend obtiene su configuración desde el `ConfigMap` `vault-unseal-config` y sus credenciales sensibles desde el `Secret` `vault-unseal-secrets`.
5. El estado persistente (base de datos SQLite) se almacena en el `PersistentVolumeClaim` `vault-unseal-data`.

---

## 3. Prerrequisitos

- Clúster Kubernetes operativo (v1.24+) con acceso administrativo al namespace `vault`.
- `kubectl` configurado apuntando al clúster destino.
- `kustomize` (incluido en `kubectl apply -k` desde la v1.14+).
- Acceso al registro de contenedores interno `rbac-registry:5000` desde los nodos del clúster, con las imágenes:
  - `rbac-registry:5000/vault-autoini-back:1.0`
  - `rbac-registry:5000/vault-autoini-front:1.0`
- `StorageClass` `local-path` disponible en el clúster (o ajustar `pvc.yaml` a la StorageClass correspondiente).
- Instancia de HashiCorp Vault accesible en `http://vault.vault:8200` (o la URL que se configure en el `ConfigMap`).
- Namespace `vault` creado previamente (`kubectl create namespace vault`).

---

## 4. Instalación / Configuración

### 4.1 Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd <directorio-del-repositorio>/kubernetes
```

### 4.2 Configurar credenciales (obligatorio antes de desplegar)

El archivo `secret.yaml` contiene valores de **ejemplo** codificados en base64. **Deben reemplazarse antes de cualquier despliegue distinto a un entorno local de pruebas**:

```bash
echo -n "<valor-real>" | base64
```

Claves a actualizar en `secret.yaml`:
- `jwt-secret`
- `admin-username`
- `admin-password`
- `vault-unseal-password`

> 🔒 **Recomendación de gobierno de seguridad:** este `Secret` se gestiona actualmente como manifiesto plano dentro del repositorio. Se recomienda migrar la gestión de estos valores a una herramienta de secret management (p. ej. Sealed Secrets, External Secrets Operator o inyección directa desde Vault) para evitar el versionamiento de credenciales, incluso codificadas en base64.

### 4.3 Ajustar configuración no sensible

Editar `configmap.yaml` según el entorno (dirección de Vault, nivel de log, intervalo de monitoreo, etc. — ver sección [Variables de Entorno](#6-variables-de-entorno--configuración)).

### 4.4 Revisar RBAC

`rbac.yaml` otorga al `ServiceAccount` `vault-unseal-manager` permisos de **clúster** (`ClusterRole`/`ClusterRoleBinding`) sobre `pods`, `pods/exec` y `pods/log`. Validar que estos permisos cumplan con la política de mínimo privilegio de la organización antes de desplegar en producción; de ser necesario, restringir a un `Role`/`RoleBinding` a nivel de namespace.

---

## 5. Uso / Ejecución

### 5.1 Despliegue con Kustomize

```bash
kubectl apply -k kubernetes/
```

Esto crea, en el orden declarado en `kustomization.yaml`:
`Secret` → `ConfigMap` → `RBAC (ServiceAccount, ClusterRole, ClusterRoleBinding)` → `PVC` → `Deployment backend` → `Service backend` → `Deployment frontend` → `Service frontend`.

### 5.2 Verificación del despliegue

```bash
kubectl get all -n vault -l app=vault-unseal-backend
kubectl get all -n vault -l app=vault-unseal-frontend
kubectl get pvc -n vault vault-unseal-data
kubectl rollout status deployment/vault-unseal-backend -n vault
kubectl rollout status deployment/vault-unseal-frontend -n vault
```

### 5.3 Acceso a la aplicación

Por defecto, ambos `Service` son de tipo `ClusterIP` (sin exposición externa). Para acceso local de validación:

```bash
kubectl port-forward -n vault svc/vault-unseal-frontend 8080:80
```

Y abrir `http://localhost:8080`.

> Para exponer el servicio de forma permanente (Ingress, LoadBalancer, etc.) debe agregarse el manifiesto correspondiente; actualmente no forma parte de este repositorio.

### 5.4 Verificación de salud del backend

```bash
kubectl exec -n vault deploy/vault-unseal-backend -- curl -s localhost:8000/api/health/live
kubectl exec -n vault deploy/vault-unseal-backend -- curl -s localhost:8000/api/health/ready
```

---

## 6. Estructura del Repositorio

```
kubernetes/
├── backend-deployment.yaml   # Deployment del backend (API de automatización de unseal)
├── backend-service.yaml      # Service ClusterIP del backend (puerto 8000)
├── configmap.yaml             # Configuración no sensible (ALGORITHM, VAULT_ADDR, etc.)
├── frontend-deployment.yaml  # Deployment del frontend (SPA de administración)
├── frontend-service.yaml     # Service ClusterIP del frontend (puerto 80)
├── kustomization.yaml        # Orquestador Kustomize (orden de aplicación de recursos)
├── pvc.yaml                   # PersistentVolumeClaim para persistencia SQLite (1Gi)
├── rbac.yaml                  # ServiceAccount + ClusterRole + ClusterRoleBinding
└── secret.yaml                 # Credenciales sensibles (JWT, admin, unseal password)
```

---

## 7. Variables de Entorno / Configuración

### 7.1 Desde `ConfigMap` (`vault-unseal-config`) — no sensibles

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `ALGORITHM` | `HS256` | Algoritmo de firma para los tokens JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Minutos de expiración del token de acceso |
| `VAULT_ADDR` | `http://vault.vault:8200` | Endpoint de la API de Vault a monitorear |
| `DATABASE_URL` | `sqlite+aiosqlite:////data/keys.db` | Cadena de conexión a la base de datos SQLite local |
| `LOG_LEVEL` | `INFO` | Nivel de verbosidad de logs |
| `KUBERNETES_NAMESPACE` | `vault` | Namespace donde se monitorean los pods de Vault |
| `CONTAINER_NAME` | `vault` | Nombre del contenedor objetivo dentro del pod de Vault |
| `MONITOR_INTERVAL` | `30` | Intervalo (segundos) del ciclo de monitoreo/unseal |

### 7.2 Desde `Secret` (`vault-unseal-secrets`) — sensibles

| Variable | Origen (key) | Requerida | Descripción |
|---|---|---|---|
| `VAULT_UNSEAL_PASSWORD` | `vault-unseal-password` | Sí | Contraseña usada para descifrar las llaves de unseal (uso del worker) |
| `SECRET_KEY` | `jwt-secret` | Sí | Clave usada para firmar los tokens JWT |
| `ADMIN_USERNAME` | `admin-username` | No (default `admin`) | Usuario administrador de la aplicación |
| `ADMIN_PASSWORD` | `admin-password` | Sí | Contraseña del usuario administrador |

### 7.3 Variables adicionales del frontend

| Variable | Valor | Descripción |
|---|---|---|
| `BACKEND_URL` | `http://vault-unseal-backend.vault.svc.cluster.local:8000` | URL interna del backend consumida por el frontend |

---

## 8. Pruebas

Este repositorio contiene únicamente manifiestos de despliegue (no incluye código fuente de aplicación ni suite de pruebas). Se recomienda:

- Validar sintaxis de los manifiestos antes de aplicar: `kubectl apply -k kubernetes/ --dry-run=client`.
- Ejecutar `kubectl apply -k kubernetes/ --dry-run=server` contra un clúster de pruebas para validar admisión (RBAC, cuotas, políticas de seguridad).
- Verificar los *probes* (`livenessProbe`/`readinessProbe`) tras el despliegue en un entorno de pre-producción antes de promover a producción.
- Las pruebas funcionales del proceso de auto-unseal (simulación de sellado de Vault y verificación de remediación automática) deben ejecutarse en un entorno controlado, dado que el `ServiceAccount` de la solución tiene permisos para eliminar pods de Vault.

---

## 9. Despliegue

Comando de despliegue estándar (todos los entornos, ajustando previamente `configmap.yaml`/`secret.yaml` según overlay):

```bash
kubectl apply -k kubernetes/
```

Para eliminar el despliegue:

```bash
kubectl delete -k kubernetes/
```
