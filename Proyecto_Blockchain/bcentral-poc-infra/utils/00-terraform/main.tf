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


#########  ------- Crfeacion resource group
#resource "azurerm_resource_group" "rg" {
#  name     = "BCC-primary-Blockchain-group"
#  location = "eastus"
#  tags = {
#    app = "BCC-Blockchain"
#  }
#}

# Referenciar un resource group existente usando data source
#resource "azurerm_resource_group" "rg" 

data "azurerm_resource_group" "existing_rg" {
  name     = "BCC-primary-Blockchain-group"
}


module "aks_primary" {
  source              = "./modules/aks"
  aks_cluster_name    = "aks-cluster"
  location            = "eastus"
  dns_prefix          = "bcc-primary"
  vm_size             = "Standard_B2ms"
  min_count           = 2
  max_count           = 4
  node_count_init     = 2
  resource_group_name = data.azurerm_resource_group.existing_rg.name
#  resource_group_name = azurerm_resource_group.rg.name
  kubernetes_version  = "1.33.5"
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