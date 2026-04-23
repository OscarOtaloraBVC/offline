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
  name     = "BCC-primary-Blockchain-group"
  location = "eastus"
  tags = {
    app = "BCC-Blockchain"
  }
}

module "aks_primary" {
  source              = "./modules/aks"
  aks_cluster_name    = "aks-cluster"
  location            = "eastus"
  dns_prefix          = "bcc-primary"
  vm_size             = "Standard_B2ms"
  min_count           = 1
  max_count           = 3
  node_count_init     = 1
  resource_group_name = azurerm_resource_group.rg.name
  kubernetes_version  = "1.31.1"
  tag_app             = "BCC-Blockchain"
  
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