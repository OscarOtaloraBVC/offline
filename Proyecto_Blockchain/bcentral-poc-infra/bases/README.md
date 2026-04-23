# 📁 Bases

Este directorio contiene las **definiciones base** reutilizables de infraestructura y aplicaciones.  
Sirven como plantilla para los *overlays* específicos de cada entorno (dev, staging, producción).

## Estructura
- **apps/** → Bases genéricas para despliegues de aplicaciones.
- **infrastructure/** → Servicios compartidos (Prometheus, Loki, repositorios Helm, etc.).

Estas bases son combinadas mediante `kustomization.yaml` en los overlays correspondientes.
