# RBAC Manager Backend

Backend de la aplicación **RBAC Manager**, encargado de la gestión de usuarios, perfiles, permisos y la integración con Kubernetes para la administración de accesos (RBAC).

---

## Descripción

Este proyecto implementa una API backend desarrollada en **Python** que permite:

- Gestión de usuarios
- Administración de perfiles (roles)
- Asignación de permisos
- Generación de configuraciones RBAC para Kubernetes
- Emisión de certificados y kubeconfig para acceso a clústeres

---

## Estructura del Proyecto

```text
rbac-manager-backend/
├── 📁 .github
│   └── 📁 workflows
│       └── ⚙️ continuos_integration.yml	                  			# Pipeline de CI
├── 📁 api
│   ├── 🐍 __init__.py
│   ├── 🐍 k8s_api.py
│   ├── 🐍 profiles_api.py
│   └── 🐍 users_api.py
├── 📁 database							                                      # Configuración de base de datos
│   ├── 🐍 __init__.py
│   └── 🐍 db.py
├── 📁 models								                                      # Modelos de datos
│   ├── 🐍 __init__.py
│   ├── 🐍 permission_model.py
│   ├── 🐍 profile_model.py
│   ├── 🐍 user_certs_model.py
│   ├── 🐍 user_model.py
│   └── 🐍 user_profile_namespace_association_model.py
├── 📁 services							                                      # Lógica de negocio
│   ├── 📁 rbac							                                      # Gestión RBAC para Kubernetes
│   │   ├── 📁 templates						                              # Plantillas YAML
│   │   │   ├── ⚙️ clusterRoleCustom.yaml
│   │   │   ├── ⚙️ clusterRoleListNs.yaml
│   │   │   ├── ⚙️ clusterRoleReadAll.yaml
│   │   │   ├── ⚙️ clusterRoleSuperUser.yaml
│   │   │   ├── ⚙️ csrTemplate.yaml
│   │   │   ├── ⚙️ roleTemplate.yaml
│   │   │   └── ⚙️ roleTemplateAllNs.yaml
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 rbac_core.py
│   │   └── 🐍 rbac_service.py
│   ├── 🐍 __init__.py
│   ├── 🐍 k8s_service.py
│   ├── 🐍 profile_service.py
│   └── 🐍 user_service.py
├── 📁 tests
│   ├── 📁 api
│   │   ├── 🐍 test_profiles_api.py
│   │   └── 🐍 test_users_api.py
│   ├── 📁 services
│   │   └── 🐍 test_rbac_service.py
│   ├── 🐍 conftest.py
│   └── 🐍 test_dummy.py
├── 🐳 Dockerfile							                                  # Construcción de imagen.
├── 📄 Dockerfile_Funcional
├── 📄 Dockerfile_Oringinal.dockerfile
├── 📝 README.md
├── 🐍 main.py								                                  # Punto de entrada de la aplicación
└── 📄 requirements.txt						                              # Bibliotecas, paquetes y sus versiones del proyetco.
```

---

## Tecnologías utilizadas

- Python
- Framework API (Flask / FastAPI según implementación)
- Kubernetes API
- YAML (plantillas RBAC)
- Docker

---

## Funcionalidades principales

### Gestión de usuarios

- Creación, edición y eliminación de usuarios
- Asociación con perfiles y namespaces
- Generación de certificados

### Gestión de perfiles

- Creación de roles personalizados
- Asignación de permisos
- Asociación con usuarios

### Integración con Kubernetes

- Creación de:
  - Roles
  - ClusterRoles
  - RoleBindings
- Generación de archivos kubeconfig
- Uso de plantillas YAML para automatización

---

## Plantillas RBAC

Ubicadas en:
python/services/rbac/templates/

Incluyen:

- `clusterRoleCustom.yaml`
- `clusterRoleReadAll.yaml`
- `clusterRoleSuperUser.yaml`
- `roleTemplate.yaml`
- `csrTemplate.yaml`

Estas plantillas son utilizadas para generar dinámicamente configuraciones RBAC en Kubernetes.

---

## Cambios en esta version

- Se adicionan elementos para la identificacion de certificados proximos a expirar.

```text
├── .env
├── Dockerfile
├── api
│   ├── alerts_api.py
│   └── certificates_api.py
├── models
│   └── alert_model.py
└── services
    ├── alert_service.py
    └── email_service.py
```

- Se modifica la creacion de la base de datos y main.

```text
├── bin
│   └── install-create-db-sqlite3.sh
└── main.py
```