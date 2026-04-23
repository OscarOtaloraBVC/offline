# 🧩 Overlay: Dev

Contiene la configuración y personalización del entorno **de desarrollo**.

## Subdirectorios
- **apps/** → Despliegues de aplicaciones de desarrollo.
- **infrastructure/** → Servicios base (Prometheus, Reposources, etc.).
- **kustoms/** → Definiciones de Kustomize para componer la infraestructura.

> 🔄 Este overlay se sincroniza con el clúster mediante FluxCD (ver `env/dev/flux-system`).
