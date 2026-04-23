# ⚙️ Bases / Infrastructure

Agrupa la infraestructura común desplegada en todos los entornos (monitoring, logging, repositorios Helm, etc.).

## Subdirectorios
- **prometheus/** → Stack de observabilidad (Prometheus, Loki, Fluentd, dashboards).
- **reposources/** → Definiciones de fuentes de HelmRepositories para FluxCD.

Estas definiciones se combinan mediante Kustomize en los overlays de cada entorno.
