terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "BCC-priACR-Blockchain-group"
  location = "eastus"
  tags = {
    app = "BCC-Blockchain-ACR"
  }
}

# Crear Azure Container Registry (ACR)
resource "azurerm_container_registry" "acr" {
  name                = "bccblockchainacr"  # Nombre debe ser único globalmente
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Standard"
  admin_enabled       = true  # Habilitar credenciales de administrador
  
  tags = {
    app = "BCC-Blockchain-ACR"
  }
}

# Asignar permiso al cluster AKS para acceder al ACR
resource "azurerm_role_assignment" "aks_acr" {
  principal_id                     = module.aks_primary.aks_principal_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.acr.id
  skip_service_principal_aad_check = true
}

module "aks_primary" {
  source              = "./modules/aks"
  aks_cluster_name    = "aks-cluster"
  location            = "eastus"
  dns_prefix          = "bcc-priACR"
  vm_size             = "Standard_B2ms"
  min_count           = 1
  max_count           = 3
  node_count_init     = 1
  resource_group_name = azurerm_resource_group.rg.name
  kubernetes_version  = "1.31.1"
  tag_app             = "BCC-Blockchain-ACR"
  
  # Configuración de Flux 
   enable_flux_bootstrap = true
   git_token            = var.flux_git_token
   flux_repo_url        = "https://dev.azure.com/Nuam-BancoCentral/Blockchain/_git/bcentral-poc-infra"
   flux_branch          = "main"
   flux_path            = "./env/dev"
}

variable "flux_git_token" {
  type        = string
  description = "Token para Flux Bootstrap"
  sensitive   = true
}