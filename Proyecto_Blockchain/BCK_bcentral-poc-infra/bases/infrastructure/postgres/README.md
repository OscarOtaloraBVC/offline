CloudNative-PG Operator Deployment

Este proyecto despliega un operador de PostgreSQL nativo en la nube (CloudNative-PG) utilizando FluxCD para la gestión de GitOps.

🏗️ Arquitectura del Proyecto

Componentes Principales

1-CloudNative-PG Operator
    Operador de Kubernetes para gestionar clusters PostgreSQL
    Versión: 0.23.1
    Desplegado en el namespace cnpg-system
2-Cluster PostgreSQL
    Instancia única de PostgreSQL 15
    Desplegado en el namespace postgres
3-Secret Management
    Almacenadas como Secret de Kubernetes

📁 Estructura de Archivos
    ├── cloudnative-pg-operator.yaml  # HelmRelease para el operador
    ├── kustomization.yaml           # Configuración de Kustomize
    ├── namespace.yaml               # Namespaces del sistema
    └── postgres-cluster.yaml        # Configuración del cluster PostgreSQL
    

🔧 Funcionalidades

1. Operador CloudNative-PG
    Gestión Automatizada: Despliegue y gestión automática de clusters PostgreSQL
    High Availability: Soporte para configuración de alta disponibilidad
    Backup y Recovery: Funcionalidades integradas de backup y recuperación
    Monitoring: Integración con Prometheus mediante PodMonitor

2. Cluster PostgreSQL
    Versión: PostgreSQL 15
    Almacenamiento: 10Gi
    Conexiones máximas: 100


🚀 Despliegue

Namespaces Creados
    cnpg-system: Para el operador CloudNative-PG
    postgres: Para el cluster de base de datos

📊 Monitoreo
El cluster PostgreSQL incluye monitoreo habilitado:
    monitoring:
        enablePodMonitor: true