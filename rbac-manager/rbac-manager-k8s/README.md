# RBAC Manager - Kubernetes Deployment

Este repositorio contiene los manifiestos de **Kubernetes** necesarios para desplegar la aplicación **RBAC Manager**, incluyendo frontend, backend, configuración, almacenamiento y control de accesos (RBAC).

---

## Descripción

Este proyecto define la infraestructura Kubernetes para:

- Despliegue del backend (API RBAC)
- Despliegue del frontend (UI React)
- Configuración mediante ConfigMap
- Control de acceso mediante RBAC
- Persistencia de datos

---

## Estructura del Proyecto

```text
rbac-manager-k8s/
├── cluster-role-binding.yaml           # Vinculación de roles a cuentas de servicio
├── cluster-role.yaml                   # Definición de permisos RBAC
├── deployment-backend.yaml             # Deployment del backend
├── deployment-frontend.yaml            # Deployment del frontend
├── env-configmap.yaml                  # Variables de entorno
├── kustomization.yaml                  # Configuración Kustomize
├── namespace.yaml                      # Namespace del proyecto
├── pvc.yaml                            # Volumen persistente
├── service-account.yaml                # Cuenta de servicio
├── service-backend.yaml                # Servicio backend
└── service-frontend.yaml               # Servicio frontend
```

---

## 🚀 Componentes desplegados

### Backend

- API RBAC
- Conectividad con Kubernetes
- Gestión de usuarios, perfiles y permisos

### Frontend

- Interfaz web para administración RBAC

### RBAC (Kubernetes)

- `ClusterRole`
- `ClusterRoleBinding`
- `ServiceAccount`

### Red

- Services (ClusterIP)

### Almacenamiento

- PersistentVolumeClaim para base de datos SQLite

la base de datos se almacena en `/opt/rbac-manager/data/rbac-sqlite3.db.` en el pod rbac-manager-backend

---

## Configuración (ConfigMap)

En el archivo `deployment-backend.yaml` se define la imagen utilizada para el despliegue.

```yaml
image: registry.nuamexchange.com/transversal-nuam/rbac-manager-backend:0.0.1-alpha.1
```

En el archivo `deployment-frontend.yaml` se define la imagen utilizada para el despliegue.

```yaml
image: registry.nuamexchange.com/transversal-nuam/rbac-manager-frontend:0.0.1-alpha.1 
```

El archivo `env-configmap.yaml` define las variables de entorno utilizadas por el backend.

### Definición

```yaml
data:
  RBAC_DB_SQLITE3_PATH: /opt/rbac-manager/data/rbac-sqlite3.db # - - - No Modificar
  RBAC_STATIC_FRONTEND_DIR: ""                                 # - - - No Modificar
  RBAC_CLUSTER_NAME: rbac-cluster                              # - - - Ejemplo
  RBAC_CLUSTER_URL: https://0.0.0.0:45711                      # - - - Ejemplo
  RBAC_CLUSTER_CA_CRT_PATH: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt  # Path generado por ServiceAccount No modificar
  RBAC_ADDITIONAL_RESOURCES: '[{"namespaced": true, "resource": "pods/exec", "apiversion": "v1"}, {"namespaced": true, "resource": "pods/portforward", "apiversion": "v1"}, {"namespaced": true, "resource": "pods/log", "apiversion": "v1"}, {"namespaced": true, "resource": "pods/proxy", "apiversion": "v1"}]' # Recursos en RBAC / No Modificar
```

| Variable                    | Descripción                                                       |
| --------------------------- | ----------------------------------------------------------------- |
| `RBAC_DB_SQLITE3_PATH`      | Ruta del archivo de base de datos SQLite utilizado por el backend |
| `RBAC_STATIC_FRONTEND_DIR`  | Ruta para servir archivos estáticos del frontend (opcional)       |
| `RBAC_CLUSTER_NAME`         | Nombre del clúster Kubernetes                                     |
| `RBAC_CLUSTER_URL`          | URL del API Server del clúster                                    |
| `RBAC_CLUSTER_CA_CRT_PATH`  | Ruta al certificado CA del clúster                                |
| `RBAC_ADDITIONAL_RESOURCES` | Recursos adicionales permitidos en RBAC                           |

## Requisitos

- Kubernetes (k3d, k8s, EKS, AKS, etc.)
- kubectl
- Soporte para Persistent Volumes

## Acceso  

Para acceder a los servicios se debe ejecutar en terminal por separado.

```bash
kubectl port-forward svc/rbac-manager-frontend 8080:8080 -n rbac-manager

kubectl port-forward svc/rbac-manager-backend 8000:8000 -n rbac-manager

http://localhost:8080/ui/
