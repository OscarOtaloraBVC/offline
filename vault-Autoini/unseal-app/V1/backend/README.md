# Vault Unseal Manager – Backend

## Descripción

**Vault Unseal Manager** es un backend desarrollado en **Python** con **FastAPI** que automatiza el proceso de *unseal* (desellado) de instancias de **HashiCorp Vault** desplegadas en **Kubernetes**.

El sistema expone una API REST que permite:

- Autenticar usuarios administradores mediante **JWT**.
- Almacenar de forma segura las llaves de unseal (cifradas con **AES-256-GCM**, derivación de clave con **PBKDF2-HMAC-SHA256**) en una base de datos SQLite.
- Monitorear el estado (`sealed`/`unsealed`) de los pods de Vault en un namespace de Kubernetes mediante un *worker* asíncrono en segundo plano.
- Ejecutar automáticamente el comando de unseal sobre los pods sellados, respetando el umbral (*threshold*) de llaves requeridas.
- Exponer endpoints de *health check* (`liveness`/`readiness`) para su integración con Kubernetes.

Este backend es consumido por un frontend web (fuera del alcance de este repositorio) y se despliega como contenedor dentro del clúster de Kubernetes que aloja Vault.

## Arquitectura / Diagrama

Flujo general del sistema:

```
┌─────────────┐      HTTPS/JWT      ┌─────────────────────┐
│  Frontend   │ ──────────────────▶ │   FastAPI Backend  │
│  (Web UI)   │ ◀────────────────── │   (main.py + api/) │
└─────────────┘                     └─────────┬───────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
            ┌────────────────┐        ┌─────────────────┐        ┌──────────────────┐
            │ SecureKeyStore │        │  MonitorWorker  │        │ KubernetesService│
            │ (SQLite + AES) │        │ (asyncio loop)  │        │ (client k8s API) │
            └────────────────┘        └────────┬────────┘        └─────────┬────────┘
                                               │                           │
                                               ▼                           ▼
                                        UnsealService  ─────────────▶  Pods de Vault
                                                                     (exec vault operator unseal)
```

**Componentes principales:**

| Componente | Responsabilidad |
|---|---|
| `api/` | Routers de FastAPI (`auth`, `keys`, `monitor`, `settings`) |
| `core/` | Cifrado (`crypto.py`), acceso a base de datos (`database.py`) y utilidades de seguridad (`security.py`) |
| `services/` | Lógica de negocio: interacción con Kubernetes (`k8s_service.py`), gestión de llaves (`key_service.py`) y orquestación de unseal (`unseal_service.py`) |
| `worker/` | Tarea en segundo plano (`monitor_worker.py`) que monitorea y desella los pods de forma periódica |
| `models/` | Modelos Pydantic de request/response |

## Prerrequisitos

- **Python** 3.11+ (imagen base `python:alpine3.23`)
- **pip** para gestión de dependencias
- Acceso a un clúster de **Kubernetes** con permisos para:
  - Listar/leer pods en el namespace de Vault.
  - Ejecutar comandos (`exec`) dentro de los contenedores de Vault (`kubectl exec` / API `exec`).
- **Docker** (opcional, para construir y ejecutar la imagen del contenedor)
- Variables de entorno configuradas (ver sección [Variables de Entorno](#variables-de-entorno--configuración))

## Instalación / Configuración

### Contenedor Docker

```bash
# Construir la imagen
docker build -t vault-unseal-manager:latest .

# Ejecutar el contenedor
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY="<clave-secreta-jwt>" \
  -e ADMIN_PASSWORD="<contraseña-admin>" \
  -e VAULT_UNSEAL_PASSWORD="<contraseña-worker>" \
  --name vault-unseal-manager \
  vault-unseal-manager:latest
```

> En Kubernetes, la configuración se inyecta mediante **ConfigMap** (parámetros no sensibles) y **Secret** (credenciales y llaves), siguiendo el estándar de gestión de secretos del equipo de Gobierno de Infraestructura y Nube.

## Uso / Ejecución

### Endpoints principales de la API

| Método | Endpoint | Descripción | Autenticación |
|---|---|---|---|
| `POST` | `/api/auth/login` | Autentica al usuario admin y retorna un JWT | No |
| `POST` | `/api/auth/verify` | Verifica la validez del token JWT | Sí |
| `POST` | `/api/auth/update-password` | Actualiza la contraseña del administrador | Sí |
| `GET` | `/api/keys` | Obtiene metadata o llaves descifradas de unseal | Sí |
| `POST` | `/api/keys` | Añade una nueva llave de unseal | Sí |
| `DELETE` | `/api/keys/{key_index}` | Elimina una llave por índice | Sí |
| `GET` | `/api/settings` | Obtiene la configuración actual (threshold, namespace, etc.) | Sí |
| `PUT` | `/api/settings` | Actualiza la configuración | Sí |
| `POST` | `/api/monitor/restart` | Reinicia el worker de monitoreo | Sí |
| `POST` | `/api/monitor/set-password` | Configura la contraseña usada por el worker | Sí |
| `GET` | `/api/health` | Health check general (incluye estado del worker) | No |
| `GET` | `/api/health/live` | Liveness probe (Kubernetes) | No |
| `GET` | `/api/health/ready` | Readiness probe (Kubernetes) | No |

La documentación interactiva (Swagger/OpenAPI) queda disponible automáticamente en `/docs` una vez el servicio está en ejecución.

## Estructura del Repositorio

```
backend/
├── api/                    # Routers de FastAPI
│   ├── __init__.py
│   ├── auth.py             # Login, verificación y actualización de contraseña (JWT)
│   ├── keys.py             # CRUD de llaves de unseal
│   ├── monitor.py          # Control del worker de monitoreo y trigger manual de unseal
│   └── settings.py         # Configuración del sistema (threshold, namespace, intervalo)
├── bin/
│   └── entrypoint.sh       # Script de arranque del contenedor
├── core/
│   ├── __init__.py
│   ├── crypto.py           # Cifrado AES-256-GCM y almacén seguro (SecureKeyStore)
│   ├── database.py         # Configuración de SQLAlchemy async y modelos ORM
│   └── security.py         # Servicio de seguridad, JWT, rate limiting, auditoría
├── models/                 # Modelos Pydantic (request/response)
│   ├── __init__.py
│   ├── key_models.py
│   └── settings_models.py
├── services/                # Lógica de negocio
│   ├── __init__.py
│   ├── k8s_service.py      # Interacción con la API de Kubernetes
│   ├── key_service.py      # Gestión de llaves de unseal
│   └── unseal_service.py   # Orquestación del proceso de unseal
├── worker/
│   ├── __init__.py
│   └── monitor_worker.py   # Tarea asíncrona de monitoreo periódico
├── dockerfile               # Imagen del backend (python:alpine)
├── main.py                  # Punto de entrada de la aplicación FastAPI
└── requirements.txt          # Dependencias del proyecto
```

## Variables de Entorno / Configuración

Todas las variables se inyectan desde **ConfigMap** (no sensibles) y **Secret** (sensibles) de Kubernetes.

| Variable | Obligatoria | Valor por defecto | Descripción |
|---|---|---|---|
| `SECRET_KEY` | ⭐ Sí | — | Clave secreta usada para firmar los tokens JWT |
| `ADMIN_USERNAME` | No | `admin` | Usuario administrador |
| `ADMIN_PASSWORD` | ⭐ Sí | — | Contraseña del usuario administrador (se hashea al iniciar) |
| `ALGORITHM` | No | `HS256` | Algoritmo de firma JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `480` | Minutos de validez del token de acceso |
| `TOKEN_EXPIRE_MINUTES` | No | `480` | Usada por `core/security.py` (alterna a `ACCESS_TOKEN_EXPIRE_MINUTES`) |
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./keys.db` | Cadena de conexión de la base de datos |
| `VAULT_UNSEAL_PASSWORD` | ⭐ Sí (para el worker) | — | Contraseña usada por el worker para descifrar las llaves de unseal almacenadas |

> ⚠️ **Nota de seguridad:** `SECRET_KEY` y `ADMIN_PASSWORD` son obligatorias; si no están definidas, la aplicación no arrancará. `VAULT_UNSEAL_PASSWORD` es necesaria para que el worker de monitoreo pueda operar automáticamente; si no se define, el unseal automático quedará deshabilitado hasta que se configure manualmente vía `/api/monitor/set-password`.


## Despliegue

El backend está diseñado para ejecutarse como contenedor dentro de Kubernetes:

- **Imagen base:** `python:alpine3.23`
- **Puerto expuesto:** `8000`
- **Probes recomendados:**
  - Liveness: `GET /api/health/live`
  - Readiness: `GET /api/health/ready`
- **Persistencia:** requiere un volumen persistente para la base de datos SQLite (`/opt/unseal-app/data`), a fin de conservar las llaves cifradas entre reinicios del pod.
- **Configuración:** inyectada vía ConfigMap (parámetros generales) y Secret (`SECRET_KEY`, `ADMIN_PASSWORD`, `VAULT_UNSEAL_PASSWORD`).
- **Permisos RBAC:** el ServiceAccount del pod debe contar con permisos para listar pods y ejecutar comandos (`exec`) sobre los pods de Vault en su namespace.
