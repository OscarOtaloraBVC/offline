# 🧩 Overlays

Los *overlays* representan las personalizaciones específicas para cada entorno:
- `dev/`
- `staging/`
- `produccion/`

Cada overlay ajusta las configuraciones base (en `bases/`) mediante `kustomization.yaml`, permitiendo modificar namespaces, variables, versiones y dependencias según el entorno.
