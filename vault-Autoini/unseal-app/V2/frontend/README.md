# Vault Unseal Manager - Frontend

## Descripción

**Vault Unseal Manager Frontend** es una aplicación web desarrollada en **React** que actúa como panel de administración (SPA) para el sistema de auto-unseal de HashiCorp Vault. Permite a los administradores autenticarse, monitorear en tiempo real el estado de sellado (*sealed/unsealed*) de los pods de Vault desplegados en Kubernetes, gestionar las llaves (*unseal keys*) utilizadas para el proceso de desbloqueo, disparar manualmente el proceso de unseal y configurar los parámetros operativos del monitor (threshold, namespace, contenedor, intervalo de monitoreo).

La aplicación está construida con **Create React App** (`react-scripts`), utiliza **Material UI (MUI)** como sistema de componentes visuales, **React Router** para el enrutamiento, **Axios** para el consumo de la API REST del backend y **React Query** junto con **React Hot Toast** para el manejo de datos remotos y notificaciones. Para producción, la aplicación se empaqueta en una imagen Docker basada en **Nginx**, la cual sirve los assets estáticos y actúa como *reverse proxy* hacia el backend.

## Arquitectura / Diagrama

La aplicación sigue una arquitectura de SPA cliente-servidor, desplegada como contenedor independiente dentro del clúster de Kubernetes, junto al backend de Vault Unseal Manager:

```

┌─────────────────────┐        HTTPS         ┌────────────────────────────────┐
│  Usuario / Admin    │ ───────────────────▶ │   Nginx (Contenedor Frontend) │
└─────────────────────┘                      │  - Sirve build estático React │
                                             │  - Proxy /api → BACKEND_URL   │
                                             └──────────────────┬────────────┘
                                                                │
                                                        Sirve SPA (React)
                                                                │
                                                                ▼
                                               ┌────────────────────────┐
                                               │   React SPA (cliente)  │
                                               │  Axios + Bearer Token  │
                                               └───────────────┬────────┘
                                                               │ /api (proxy_pass)
                                                               ▼
                                               ┌───────────────────────────────┐
                                               │  Backend Vault Unseal Manager  │
                                               └───────┬───────────────┬───────┘
                                                       │               │
                                                       ▼               ▼
                                          ┌────────────────────┐  ┌──────────────────┐
                                          │  HashiCorp Vault    │  │  API Kubernetes   │
                                          └────────────────────┘  └──────────────────┘
```

**Flujo general:**
1. El usuario accede a la SPA servida por Nginx.
2. El componente `AuthContext` gestiona el login contra el backend (`/auth/login`) y almacena el token JWT en `localStorage`.
3. Los componentes (`MonitorDashboard`, `KeyManager`, `SettingsPanel`) consumen la API REST del backend a través del cliente `axios` centralizado en `services/api.js`, el cual inyecta automáticamente el token Bearer en cada solicitud.
4. En tiempo de despliegue, Nginx sustituye la variable `BACKEND_URL` en la plantilla `nginx/default.conf.template` para enrutar las peticiones `/api` hacia el backend correspondiente dentro del clúster.

## Prerrequisitos

Para trabajar con este proyecto en entorno local se requiere:

- **Node.js** 20.x (misma versión utilizada en el `Dockerfile`)
- **npm** (incluido con Node.js)
- Acceso al backend de **Vault Unseal Manager** (local o remoto) para consumo de la API
- **Docker** (opcional, para construir y ejecutar la imagen de producción)
- Acceso al clúster de **Kubernetes** donde se despliega el servicio (para pruebas de integración end-to-end)

## Instalación / Configuración

### Configuración de variables de entorno

Crear un archivo `.env` en la raíz del proyecto (no versionado) con la variable necesaria para apuntar al backend en desarrollo:

```bash
REACT_APP_API_URL=http://localhost:8000/api
```

> Si la variable `REACT_APP_API_URL` no se define, el cliente Axios utiliza por defecto la ruta relativa `/api`, asumiendo que el backend está expuesto detrás del mismo dominio (caso de producción vía Nginx).

## Uso / Ejecución

### Ejecución vía Docker

```bash
# Construir la imagen
docker build -t vault-unseal-frontend .

# Ejecutar el contenedor
docker run -p 80:80 \
  -e BACKEND_URL=http://vault-unseal-backend.vault.svc.cluster.local:8000 \
  vault-unseal-frontend
```

## Estructura del Repositorio

```
frontend/
├── nginx/
│   └── default.conf.template     # Plantilla de configuración de Nginx (proxy hacia el backend)
├── public/
│   └── index.html                # HTML base de la SPA
├── src/
│   ├── components/
│   │   ├── Dashboard.js          # Layout principal: AppBar, Drawer de navegación y Outlet
│   │   ├── KeyManager.js         # Gestión de llaves de unseal (alta, baja, visualización)
│   │   ├── Login.js              # Formulario de autenticación
│   │   ├── MonitorDashboard.js   # Monitoreo en tiempo real del estado de los pods de Vault
│   │   └── SettingsPanel.js      # Configuración de threshold, namespace, intervalo y contraseña
│   ├── contexts/
│   │   └── AuthContext.js        # Contexto de autenticación (login, logout, token, verificación)
│   ├── services/
│   │   └── api.js                # Cliente Axios centralizado con interceptores de auth
│   ├── App.js                    # Definición de rutas y providers globales
│   ├── index.css                 # Estilos globales y animaciones
│   └── index.js                  # Punto de entrada de la aplicación React
├── Dockerfile                    # Build multi-stage (Node + Nginx) para producción
└── package.json                  # Dependencias y scripts del proyecto
```

## Variables de Entorno / Configuración

| Variable | Contexto | Descripción | Valor por defecto |
|---|---|---|---|
| `REACT_APP_API_URL` | Build / desarrollo (React) | URL base de la API consumida por el cliente Axios. Debe iniciar con `REACT_APP_` para ser embebida en el build de Create React App. | `/api` |
| `BACKEND_URL` | Runtime del contenedor (Nginx) | URL del backend hacia la cual Nginx enruta las peticiones `/api` mediante `envsubst` sobre `default.conf.template`. | `http://vault-unseal-backend.vault.svc.cluster.local:8000` |

Adicionalmente, la aplicación persiste en el navegador (`localStorage`) los siguientes valores de sesión, gestionados por `AuthContext`:

- `auth_token`: token JWT de la sesión activa.
- `auth_user`: datos básicos del usuario autenticado.