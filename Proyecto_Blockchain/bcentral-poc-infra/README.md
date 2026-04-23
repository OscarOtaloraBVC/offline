# 📦 Repositorio: bcentral-poc-infra

## 🧭 Descripción General

Este repositorio contiene la infraestructura declarativa y la configuración de despliegues automatizados gestionados mediante **FluxCD** y **Terraform** para el entorno **BCC Primary**.  
Su propósito es centralizar la definición de infraestructura, aplicaciones y entornos (dev, staging, producción), facilitando la observabilidad, trazabilidad y versionamiento completo del estado del clúster Kubernetes.

Acorde a lo visto en [GitOps-Despliegue de AKS](https://dev.azure.com/Bcentral-Arquitectura/ETAD/_wiki/wikis/ETAD.wiki/34/GitOps-Despliegue-de-AKS)
---

## 🧩 Estructura del Repositorio

bcentral-poc-infra/
│
├── bases/ # Definiciones base de infraestructura y aplicaciones
│ ├── apps/ # Bases genéricas para aplicaciones
│ └── infrastructure/ # Recursos base de infraestructura común
│ ├── prometheus/ # Monitoreo (Prometheus, Loki, Fluentd)
│ └── reposources/ # Fuentes de HelmRepositories (Appscode, Jetstack, etc.)
│
├── overlays/ # Overlays por entorno (dev, staging, producción)
│ ├── dev/ # Personalización para entorno de desarrollo
│ │ ├── apps/
│ │ ├── infrastructure/
│ │ └── kustoms/
│ ├── staging/
│ └── produccion/
│
├── env/ # Definición de entornos gestionados por FluxCD
│ ├── dev/
│ │ └── flux-system/ # Componentes de sincronización FluxCD (gotk)
│ ├── staging/
│ └── produccion/
│
├── utils/ # Utilitarios de automatización e infraestructura
│ └── 00-terraform/ # Infraestructura IaC en Terraform
│ ├── modules/ # Módulos reutilizables (ej. AKS)
│ └── main.tf # Definición principal del despliegue
│
├── ejemplo-azure-pipelines.yml # Ejemplo de pipeline CI/CD en Azure DevOps
└── README.md # Este archivo

---

## ⚙️ Componentes Principales

### 🧱 Bases (`bases/`)
Contiene las definiciones genéricas reutilizables que sirven como plantillas para los overlays.  
Incluye:
- **`apps/`** → Definiciones base de aplicaciones comunes.
- **`infrastructure/`** → Servicios compartidos como Prometheus, Loki, Fluentd, Repositorios Helm, etc.

### 🧩 Overlays (`overlays/`)
Personalizaciones específicas por entorno (dev, staging, producción).  
Cada overlay aplica configuraciones sobre las bases para ajustar parámetros según el entorno, como recursos, namespaces, y valores de despliegue.

### 🌍 Env (`env/`)
Define la configuración específica que **FluxCD** utiliza para sincronizar los manifests con el clúster.  
Cada entorno contiene un subdirectorio `flux-system` con los manifiestos `gotk-components.yaml`, `gotk-sync.yaml`, y el `kustomization.yaml`.

### 🛠️ Utils (`utils/`)
Incluye herramientas auxiliares:
- **`00-terraform/`** → Estructura IaC para la provisión automática de infraestructura en Azure (AKS, networking, backend de estado, etc.).
  - Contiene módulos reutilizables (`modules/aks`) y definiciones principales (`main.tf`, `variables.tf`, `outputs.tf`).

---

## 🚀 Flujo de Trabajo (GitOps + Terraform)

1. **Terraform** (ubicado en `utils/00-terraform/`) crea y configura los recursos de infraestructura base en Azure, incluyendo el clúster AKS y el almacenamiento del estado remoto.
2. **FluxCD** sincroniza automáticamente los manifests del repositorio con el clúster, aplicando las configuraciones definidas en `env/` y `overlays/`.
3. Las actualizaciones se gestionan mediante **Pull Requests** para mantener control y trazabilidad sobre los cambios en la infraestructura o aplicaciones.

---

## 🔐 Autenticación y Seguridad

- El acceso a los repositorios y despliegues está gestionado mediante tokens personales (PAT) de Azure DevOps.
- Las credenciales y secretos sensibles deben manejarse mediante **External Secrets** o **Vault**, nunca en texto plano.

---

## 📈 Monitoreo y Observabilidad

El módulo `bases/infrastructure/prometheus` implementa un stack de monitoreo que incluye:
- **Prometheus** para métricas.
- **Loki + Fluentd** para logs centralizados.
- **Grafana** (opcional, si se incluye en reposources) para visualización.

---

## 🧾 Referencias

- [GitOps-Despliegue de AKS](https://dev.azure.com/Bcentral-Arquitectura/ETAD/_wiki/wikis/ETAD.wiki/34/GitOps-Despliegue-de-AKS)
- [FluxCD Documentation](https://fluxcd.io/docs/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Kustomize](https://kubectl.docs.kubernetes.io/references/kustomize/)
- [Azure DevOps Pipelines](https://learn.microsoft.com/en-us/azure/devops/pipelines/)

---

> ⚠️ **Nota:** Toda modificación en `bases/` o `overlays/` debe ser probada en `dev` antes de su promoción a `staging` o `producción`.

