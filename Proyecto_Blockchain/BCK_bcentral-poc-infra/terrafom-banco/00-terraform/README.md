# ☁️ Terraform Infrastructure

Contiene la definición **IaC (Infraestructura como Código)** para aprovisionar los recursos de Azure requeridos por el entorno BCC.

## Componentes Principales
- **main.tf** → Despliegue principal.
- **modules/** → Módulos reutilizables (ej. AKS).
- **providers.tf** y **backend.tf** → Configuración de proveedores y backend remoto (Azure Storage).
- **azure-pipelines.yml** → Pipeline de ejecución automatizada en Azure DevOps.


## Despliegue en Azure

- Install azure cli:  https://learn.microsoft.com/en-us/cli/azure/install-azure-cli

- Login to azure
```
az login --use-device-code
```

- Deploy with terraform
```
cd tools/terraform

terraform init
terraform plan
terraform apply
```

- Checking cluster

```
az account set --subscription <id_of_subscription>
az aks get-credentials --resource-group BCC-Blockchain-group --name <name_of_aks> --overwrite-existing
kubectl get nodes
```
