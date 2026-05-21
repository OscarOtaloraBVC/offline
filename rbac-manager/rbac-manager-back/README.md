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
│   ├── 🐍 alerts_api.py
│   ├── 🐍 certificates_api.py
│   ├── 🐍 k8s_api.py
│   ├── 🐍 profiles_api.py
│   └── 🐍 users_api.py
├── 📁 database							                                      # Configuración de base de datos
│   ├── 🐍 __init__.py
│   └── 🐍 db.py
├── 📁 models								                                      # Modelos de datos
│   ├── 🐍 __init__.py
│   ├── 🐍 alert_model.py
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
│   ├── 🐍 __init__.py
│   ├── 🐍 alert_service.py                                    # Identificacion de certificados proximos a expirar
│   ├── 🐍 email_service.py                                    # Envio de correo 
│   ├── 🐍 k8s_service.py
│   ├── 🐍 profile_service.py
│   └── 🐍 user_service.py
├── 📁 tests
│   └── 🐍 test_dummy.py
├── 🐳 Dockerfile							                                  # Construcción de imagen.
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

## Cambios en esta versión

- Se adicionan elementos para la identificación de certificados próximos a expirar y envio de correo.

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

- Se modifica la creación de la base de datos y main.

```text
├── bin
│   └── install-create-db-sqlite3.sh
└── main.py
```

- En base de datos se crean las tablas.

  - users_certs: Almacena el contenido del archivo kubeconfig generado para el usuario y la fecha de creación.

  - certificate_alerts: Controla las alertas para avisar antes de que venza un certificado (por ejemplo, enviar un correo si faltan 5 días).

- En  `main.py` se incluye la función  `alerts_api` para la configuración de las alertas de vencimiento de certificados.

- En `services/alert_service.py` la función `def check_and_send_alerts() -> dict:` se configura el `Cooldown` de 24 horas para el envio de un único mensaje diario.
