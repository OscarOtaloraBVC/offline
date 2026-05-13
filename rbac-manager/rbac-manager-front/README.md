# RBAC Manager Frontend

Frontend de la aplicación **RBAC Manager**, diseñado para la gestión de usuarios, perfiles y permisos en entornos Kubernetes mediante una interfaz web intuitiva.

---

## Descripción

Este proyecto es una aplicación desarrollada en **React** que permite:

- Gestión de usuarios
- Administración de perfiles (roles)
- Asignación de permisos
- Integración con servicios backend para RBAC
- Operaciones relacionadas con Kubernetes (ej. kubeconfig)

---

## Estructura del Proyecto

```text
rbac-manager-frontend/
├── 📁 .github
│   └── 📁 workflows
│       └── ⚙️ continuos_integration.yml   			    # Pipeline de CI
├── 📁 public							                # Archivos estáticos			
│   ├── 📄 favicon.ico
│   ├── 🖼️ favicon.svg
│   ├── 🌐 index.html
│   ├── 🖼️ logo.png
│   ├── 🖼️ logo192.png
│   ├── 🖼️ logo512.png
│   ├── ⚙️ manifest.json
│   └── 📄 robots.txt
├── 📁 src							                    # Recursos (imágenes, etc.)
│   ├── 📁 assets
│   │   └── 🖼️ logo.png
│   ├── 📁 components						            # Componentes reutilizables
│   │   ├── 📁 forms						            # Formularios
│   │   │   ├── 📄 ProfileForm.js
│   │   │   └── 📄 UserForm.js
│   │   ├── 📁 modals						            # Modales
│   │   │   ├── 📄 ManageGetKubeconfigModal.js
│   │   │   ├── 📄 ManageProfilePermissionsModal.js
│   │   │   └── 📄 ManageUserAssignmentsModal.js
│   │   ├── 📄 Autocomplete.js
│   │   ├── 📄 Layout.js
│   │   └── 📄 TopMenu.js
│   ├── 📁 pages						                # Vistas principales
│   │   ├── 📁 profiles
│   │   │   ├── 📄 ProfileDetailPage.js
│   │   │   ├── 📄 ProfileEditPage.js
│   │   │   ├── 📄 ProfileListPage.js
│   │   │   └── 📄 ProfileNewPage.js
│   │   ├── 📁 users
│   │   │   ├── 📄 UserDetailPage.js
│   │   │   ├── 📄 UserEditPage.js
│   │   │   ├── 📄 UserListPage.js
│   │   │   └── 📄 UserNewPage.js
│   │   └── 📄 HomePage.js
│   ├── 📁 services						                # Lógica de conexión a APIs
│   │   ├── 📄 api.js
│   │   ├── 📄 api.js.dev
│   │   ├── 📄 api.js.prod
│   │   ├── 📄 k8sService.js
│   │   ├── 📄 profileService.js
│   │   └── 📄 userService.js
│   ├── 🎨 App.css
│   ├── 📄 App.js						                # Componente principal
│   ├── 📄 App.test.js
│   ├── 🎨 index.css
│   ├── 📄 index.js						                # Punto de entrada
│   ├── 🖼️ logo.svg
│   ├── 📄 reportWebVitals.js
│   └── 📄 setupTests.js
├── ⚙️ .gitignore
├── 🐳 Dockerfile
├── 📝 README.md
├── ⚙️ nginx.conf						                # Construcción de imagen
├── ⚙️ package-lock.json
└── ⚙️ package.json						                # Dependencias y scripts
└── 📄 run.sh
```

---

## 🚀 Tecnologías utilizadas

- React
- Axios
- Nginx (para despliegue)
- Docker
- Kubernetes (entorno objetivo)

---

## ⚙️ Configuración

### Variables de entorno

El frontend se conecta al backend mediante la URL definida en:

- src/services/api.js

- Ejemplo:

```js
baseURL: 'http://localhost:8000/api/v1'
```

---

## Cambios en esta version

- Se adicionan elementos para la identificacion de certificados proximos a expirar y Alertamiento de certificados.

```text

└── src
    ├── components
    │   └── CertificateSummary.js
    ├── pages
    │   └── alerts
    │       └── CertificateAlertsPage.js
    └── services
        ├── alertService.js
        └── certificateService.js
```

- Se incluyen vistas en

```text
└── src
    ├── App.js
    └── components
        └── TopMenu.js
```