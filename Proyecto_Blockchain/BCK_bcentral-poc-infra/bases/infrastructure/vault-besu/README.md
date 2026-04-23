Despliegue de Vault con Flux CD

Este proyecto despliega HashiCorp Vault en Kubernetes utilizando Flux CD para la gestión GitOps, con ajustes para la implememntacion de hyperledger-besu.


🚀 Funcionalidades

Despliegue Automatizado: Instalación y actualización automática de Vault mediante Flux CD
Gestión GitOps: Configuración declarativa versionada en Git
Interfaz Web: UI de Vault habilitada y accesible mediante LoadBalancer
Namespaces Aislados: Despliegue en namespace dedicado "vault"
Control de Versiones: Versión específica de Helm Chart (0.25.0) para hyperledger-besu 
Configuración Personalizable: Valores override mediante HelmRelease

🏗️ Componentes
Core Components

Vault Server: Servidor principal de HashiCorp Vault
Vault UI: Interfaz gráfica web (habilitada)
LoadBalancer Service: Servicio para acceso externo a la UI
Kubernetes Namespace: Namespace aislado "vault"

Flux CD Components

HelmRelease: Recurso personalizado de Flux para gestionar releases de Helm
HelmRepository: Repositorio de charts de HashiCorp
Kustomization: Recurso para orquestación de manifiestos

📁 Estructura de Carpetas
    vault/
    ├── kustomization.yaml      # Configuración Kustomize para Vault
    ├── namespace.yaml          # Definición del namespace vault
    ├── prom-rbac.yaml          # Permite monitorear pods Vault.
    └── helm-release.yaml       # HelmRelease para Vault con valores custom.


⚙️ Configuración

Helm Chart Configuration
    Chart: vault
    Versión: 0.25.0
    Repositorio: https://helm.releases.hashicorp.com
    Namespace: vault

Network Configuration
    Puerto UI: 8200 (externo via LoadBalancer)
    Protocolo: HTTP/HTTPS (dependiendo de la configuración de Vault)
    Acceso: Externo mediante LoadBalancer de Kubernetes