# 📈 Prometheus Stack (Base)

Este módulo define la configuración base del stack de observabilidad, incluyendo:

- **Prometheus** → Métricas y monitoreo.
- **Loki** → Centralización de logs.
- **Fluentd** → Agente de recolección de logs.
- **Dashboards** → Configuración de paneles en Grafana.

Los manifiestos están organizados en subcarpetas (`dashboards`, `fluentd-loki`, `loki`) y se ensamblan mediante `kustomization.yaml`.

> 💡 Puede ser extendido desde `overlays/dev/infrastructure/prometheus` o entornos superiores.

Para Obtener la contraseña de acceso en la interfaz de grafana utilizar:

Usuario: admin

Contraseña:

Obtenerla desde cli o terminal segun el cliente.

Linux: kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode; echo
Windows: kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }