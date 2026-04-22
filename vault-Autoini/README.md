## No utilizado - Validar funcionalidad de Job de Inicialización
Vault con CloudNativePG en Kubernetes
Este proyecto implementa una solución completa de HashiCorp Vault utilizando CloudNative PostgreSQL como backend de almacenamiento, desplegada en Kubernetes mediante FluxCD.

🚀 Funcionalidades Principales
    Vault con Alta Disponibilidad: Configuración de Vault con múltiples réplicas
    Almacenamiento en PostgreSQL: Utiliza CloudNativePG como backend de base de datos
    Auto-inicialización: Scripts automáticos para inicializar y desbloquear Vault
    Gestión de Secretos: Almacenamiento seguro de claves de Vault en Secrets de Kubernetes
    Interfaz Web: UI de Vault habilitada y accesible mediante LoadBalancer
    Operador PostgreSQL: Gestión automatizada de clusters PostgreSQL con CloudNativePG

🏗️ Arquitectura del Proyecto
Componentes Principales
1.CloudNativePG Operator
    Operador para gestión de clusters PostgreSQL en Kubernetes
    Namespace: cnpg-system
2.Cluster PostgreSQL
    Base de datos para almacenamiento de Vault
    Namespace: vault
    Instancia única con 10Gi de almacenamiento
3.HashiCorp Vault
    Servidor Vault con configuración HA
    2 réplicas para alta disponibilidad
    UI habilitada en puerto 8200
4.Sistema de Inicialización
    Job de inicialización automática de Vault
    Gestión de claves de desbloqueo
    RBAC para permisos de Kubernetes

📁 Estructura de Archivos
    ├── cloudnative-pg-operator.yaml    # HelmRelease del operador PostgreSQL
├── helmrelease-vault.yaml          # HelmRelease de Vault
├── kustomization.yaml              # Configuración de Kustomize
├── namespace.yaml                  # Namespace para Vault
├── override-values.yaml            # Valores de configuración de Vault
├── postgres-cluster.yaml           # Cluster PostgreSQL para Vault
├── vault-db-secret.yaml            # Secret con credenciales de BD
├── vault-override-values-configmap.yaml # ConfigMap para valores de Vault
└── vault-init/
    ├── vault-init-script-configmap.yaml  # Script de inicialización
    ├── vault-init-rbac.yaml              # Permisos RBAC
    └── vault-init-job-improved.yaml      # Job de inicialización

🔧 Configuración
PostgreSQL (CloudNativePG)
    Imagen: ghcr.io/cloudnative-pg/postgresql:15
    Almacenamiento: 10Gi
    Base de datos: vault
    Usuario: vault (credenciales en secret)

Vault
    Réplicas: 2
    UI: Habilitada en puerto 8200
    Almacenamiento: 10Gi
    Tipo de servicio: LoadBalancer

Configuración de Vault

storage "postgresql" {
  connection_url = "postgresql://vault:vaultpassword123@vault-postgres-rw.vault.svc.cluster.local:5432/vault?sslmode=disable"
}

listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = 1
}

🛠️ Despliegue

El proyecto utiliza FluxCD para la gestión de despliegues GitOps:
Operador CloudNativePG: Se despliega primero para gestionar PostgreSQL
Cluster PostgreSQL: Proporciona el backend de almacenamiento
Vault: Se despliega con configuración de alta disponibilidad
Job de Inicialización: Configura y desbloquea Vault automáticamente