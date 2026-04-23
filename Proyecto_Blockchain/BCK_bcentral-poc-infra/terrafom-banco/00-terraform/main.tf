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

data "azurerm_resource_group" "rg" {
  name     = "RG-ACTDIG-ZDP"
}

data "azurerm_virtual_network" "existing_vnet" {
  name                = "VNET-ZDP-PAAS01"
  resource_group_name = "RG-Net-ZDP"
}

data "azurerm_subnet" "existing_subnet" {
  name                 = "Subnet-AKS-PG-ZDP"
  virtual_network_name = data.azurerm_virtual_network.existing_vnet.name
  resource_group_name  = data.azurerm_virtual_network.existing_vnet.resource_group_name
  
}
module "aks_primary" {
  source              = "./modules/aks"
  aks_cluster_name    = "aks-poc-dlt-zdp"
  location            = "eastus2"
  dns_prefix          = "aks-poc-dlt-zdp-dns"
  vm_size             = "Standard_D4s_v3"
  min_count           = 1
  max_count           = 3
  node_count_init     = 1
  resource_group_name = data.azurerm_resource_group.rg.name
  kubernetes_version  = "1.33.5"
  tag_app             = "BCC-Blockchain"
  vnet_subnet_id      = data.azurerm_subnet.existing_subnet.id

  # Configuración de Flux
  enable_flux_bootstrap = true
  git_token            = "4AKJOUSbJ0KaJGUMaK99bsLgTUHUnub44lyIApVIbQeVfewzip67JQQJ99BKACAAAAAi4tlgAAASAZDOcBec"
  flux_repo_url        = "https://Bcentral-Arquitectura@dev.azure.com/Bcentral-Arquitectura/ETAD/_git/bcentral-poc-infra"
  flux_branch          = "main"
  flux_path            = "./env/dev"
}

#variable "flux_git_token" {
#  type        = string
#  description = "Token para Flux Bootstrap"
#  sensitive   = true
#}