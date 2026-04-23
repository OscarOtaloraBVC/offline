# 🧱 Módulo Terraform: AKS

Define la creación y configuración de un clúster **Azure Kubernetes Service (AKS)**.

## Contenido
- **main.tf** → Recursos principales del clúster.
- **variables.tf** → Parámetros personalizables.
- **outputs.tf** → Valores de salida (nombres, credenciales, endpoints).

> 🚀 Este módulo es utilizado por `main.tf` para crear el clúster BCC-Primary-AKS y asociar los recursos necesarios (RG, red, identidad, etc.).
