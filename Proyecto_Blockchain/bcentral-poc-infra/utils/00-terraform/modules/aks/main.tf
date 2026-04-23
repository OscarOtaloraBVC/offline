# Creating cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "BCC-primary-${var.aks_cluster_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = var.dns_prefix
  kubernetes_version  = var.kubernetes_version

  tags = {
    app         = var.tag_app
    environment = "dev"
  }

  sku_tier = "Standard"

  role_based_access_control_enabled = true
  local_account_disabled            = false
  automatic_channel_upgrade         = "patch"

  default_node_pool {
    name                   = "bccprimary"
    vm_size                = var.vm_size
    enable_node_public_ip  = false
    node_count             = var.node_count_init
    enable_auto_scaling    = true
    min_count              = var.min_count
    max_count              = var.max_count
    
    tags = {
      app         = var.tag_app
      environment = "dev"
      pool        = "bcc-primary"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "kubenet"
    network_policy = "calico"
    dns_service_ip = "10.2.0.10"
    service_cidr   = "10.2.0.0/16"
  }
}

# Get credentials to access the cluster
data "azurerm_kubernetes_cluster" "aks_get" {
  name                = azurerm_kubernetes_cluster.aks.name
  resource_group_name = var.resource_group_name
  depends_on = [
    azurerm_kubernetes_cluster.aks,
  ]
}

# Obtener credenciales del cluster AKS
resource "null_resource" "aks_kubeconfig" {
  depends_on = [azurerm_kubernetes_cluster.aks]

  provisioner "local-exec" {
    command = "az aks get-credentials --resource-group ${azurerm_kubernetes_cluster.aks.resource_group_name} --name ${azurerm_kubernetes_cluster.aks.name} --overwrite-existing"
  }
}

# Instalación de Flux CLI (PRIMERO esto)
resource "null_resource" "install_flux_cli" {
  depends_on = [null_resource.aks_kubeconfig]

  provisioner "local-exec" {
    command = <<EOF
      # Verificar si Flux CLI ya está instalado
      if ! command -v flux &> /dev/null; then
        echo "Instalando Flux CLI..."
        curl -s https://fluxcd.io/install.sh | sudo bash
      else
        echo "Flux CLI ya está instalado"
      fi
      
      # Verificar versión instalada
      flux --version
    EOF
  }
}

# Instalar FluxCD en el cluster (DESPUÉS de tener el CLI)
resource "null_resource" "install_flux" {
  depends_on = [null_resource.install_flux_cli]

  provisioner "local-exec" {
    command = <<EOF
      # Verificar si Flux ya está instalado en el cluster
      if ! kubectl get ns flux-system 2>/dev/null; then
        echo "Instalando FluxCD en el cluster..."
        flux install \
          --components=source-controller,kustomize-controller,helm-controller,notification-controller
      else
        echo "FluxCD ya está instalado en el cluster"
      fi
    EOF
  }
}

# Bootstrap conexion a repositorio Git (OPCIONAL - solo si se provee token)
resource "null_resource" "flux_bootstrap" {
  count = var.enable_flux_bootstrap ? 1 : 0

  depends_on = [null_resource.install_flux]

  triggers = {
    repo_url    = var.flux_repo_url
    branch      = var.flux_branch
    path        = var.flux_path
    always_run  = timestamp()
  }

  provisioner "local-exec" {
    command = <<EOF
      if [ -n "${var.git_token}" ]; then
        echo "Ejecutando bootstrap de Flux..."
        flux bootstrap git \
          --url=${var.flux_repo_url} \
          --branch=${var.flux_branch} \
          --path=${var.flux_path} \
          --token-auth \
          --username=git \
          --password="${var.git_token}"
      else
        echo "Token no proporcionado, omitiendo bootstrap"
      fi
    EOF
  }
}