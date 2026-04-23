# Creating cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = var.aks_cluster_name
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = var.dns_prefix
  kubernetes_version  = var.kubernetes_version

  tags = {
    app         = var.tag_app
    environment = "dev"
  }
  
  # Private access
  private_cluster_enabled = true

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
    vnet_subnet_id         = var.vnet_subnet_id
    
    tags = {
      app         = var.tag_app
      environment = "dev"
      pool        = "bcc-primary"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  linux_profile {
    admin_username = "azureuser"
 
    ssh_key {
      key_data = file("/mnt/e/WSL/bcentral-poc-infra/utils/00-terraform/id_key.pub")
    }
  } 

  network_profile {
    network_plugin = "kubenet"
    network_policy = "calico"
    dns_service_ip = "10.2.0.10"
    service_cidr   = "10.2.0.0/16"
    outbound_type  = "userAssignedNATGateway"
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

# --- 1. Obtener IDs de Recursos Conocidos ---

# A. Cluster AKS
data "azurerm_kubernetes_cluster" "aks" {
  name                = azurerm_kubernetes_cluster.aks.name    # ⬅️ Reemplazar
  resource_group_name = var.resource_group_name     # ⬅️ Reemplazar
}

data "azurerm_virtual_network" "existing_vnet" {
  name                = "VNET-ZDP-PAAS01"
  resource_group_name = "RG-Net-ZDP"
}


# --- 2. Obtener la Referencia a la Tabla de Rutas ---

# C. Subnet de AKS (contiene la referencia a la tabla de rutas)
data "azurerm_subnet" "existing_subnet" {
  depends_on = [azurerm_kubernetes_cluster.aks]
  name = "Subnet-AKS-PG-ZDP"
  virtual_network_name = data.azurerm_virtual_network.existing_vnet.name
  resource_group_name  = data.azurerm_virtual_network.existing_vnet.resource_group_name
}

# D. Extracción Dinámica del Nombre de la Route Table
locals {
  # Formato del ID: /subscriptions/.../resourceGroups/RG_NAME/providers/Microsoft.Network/routeTables/RT_NAME
  # Usamos split("/", ID) y element() para obtener los valores en las posiciones 4 (RG) y 8 (Nombre)
  route_table_id      = data.azurerm_subnet.existing_subnet.route_table_id
  route_table_rg_name = element(split("/", local.route_table_id), 4)
  route_table_name    = element(split("/", local.route_table_id), 8)
}
## A. Asignación de Permiso Network Contributor

resource "azurerm_role_assignment" "aks_network_contributor" {
  # ... otras configuraciones

  # CRUCiAL: Genera un UUID V5 determinístico y único para este recurso.
  # Usamos el principal_id y el scope.id como entrada para garantizar la unicidad.
  name                 = uuidv5("2088b9be-912f-502a-9f5e-1c62f0260799", 
                            "${data.azurerm_kubernetes_cluster.aks.id}/${data.azurerm_virtual_network.existing_vnet.id}/NetworkContributor")
  
  principal_id         = data.azurerm_kubernetes_cluster.aks.identity[0].principal_id
  scope                = data.azurerm_virtual_network.existing_vnet.id
  role_definition_name = "Network Contributor" 
}

## B. Agregar una Ruta a la Tabla de Rutas Dinámica

resource "azurerm_route" "nueva_ruta_servicio" {
  # Referencia dinámica a la Route Table
  route_table_name       = local.route_table_name
  resource_group_name    = local.route_table_rg_name
  
  # Definición de la Ruta
  name                   = "ruta-a-onprem-service" 
  address_prefix         = "10.55.0.48/32"               # ⬅️ Red de destino (Reemplazar)
  next_hop_type          = "VirtualAppliance" 
  next_hop_in_ip_address = "10.190.1.132"              # ⬅️ IP del Next Hop (Reemplazar)
  
  # Opcional: Asegura la dependencia si es necesario.
  depends_on = [
    azurerm_role_assignment.aks_network_contributor 
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
#resource "null_resource" "install_flux_cli" {
#  depends_on = [null_resource.aks_kubeconfig]

#  provisioner "local-exec" {
#    command = <<EOF
#      # Verificar si Flux CLI ya está instalado
#      if ! command -v flux &> /dev/null; then
#        echo "Instalando Flux CLI..."
#        curl -s https://fluxcd.io/install.sh | sudo bash
#      else
#        echo "Flux CLI ya está instalado"
#      fi
      
#     # Verificar versión instalada
#      flux --version
#    EOF
#  }
#}

#Modificar Archivo host para acceso al cluster
resource "null_resource" "modificar_hosts" {
  depends_on = [null_resource.aks_kubeconfig]
  provisioner "local-exec" {
  command = "API_IP=\"10.198.32.132\"; API_FQDN_RAW=\"${azurerm_kubernetes_cluster.aks.kube_config[0].host}\"; API_FQDN=$(echo $API_FQDN_RAW | sed -e 's|^https://||' -e 's|:443$||'); if [ -n \"$API_IP\" ]; then echo \"Agregando entrada del servidor API privado al archivo /etc/hosts...\"; sudo sh -c \"echo \\\"$API_IP $API_FQDN\\\" >> /etc/hosts\";fi"
}
}

# Instalar FluxCD en el cluster (DESPUÉS de tener el CLI)
resource "null_resource" "install_flux" {
#  depends_on = [null_resource.install_flux_cli]
   depends_on = [null_resource.modificar_hosts]
  provisioner "local-exec" {
    command = "if ! kubectl get ns flux-system &> /dev/null; then echo \"Instalando FluxCD en el cluster...\"; flux install --components=source-controller,kustomize-controller,helm-controller,notification-controller; else echo \"FluxCD ya está instalado en el cluster\"; fi"
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
    command = "if [ -n \"${var.git_token}\" ]; then echo \"Ejecutando bootstrap de Flux...\"; flux bootstrap git --url=${var.flux_repo_url} --branch=${var.flux_branch} --path=${var.flux_path} --token-auth --username=git --password=\"${var.git_token}\"; else echo \"Token no proporcionado, omitiendo bootstrap\"; fi"
  }
}

# Define la cantidad de claves de desbloqueo (Total Shares) y el umbral requerido (Threshold).
locals {
  vault_shares    = 5
  vault_threshold = 3
  root_token_filepath = "/mnt/e/WSL/bcentral-poc-infra/utils/00-terraform/root_token_extracted.txt"
  aks_endpoint = azurerm_kubernetes_cluster.aks.kube_config[0].host
  script_install_dir = "/mnt/e/WSL/bcentral-poc-infra/utils/bcentral-testnet/hyperledger-besu/charts/"
}

resource "time_sleep" "wait_project_identities" {
  depends_on = [
    data.azurerm_kubernetes_cluster.aks
  ]
  create_duration = "300s"
}
resource "null_resource" "vault_initialization" {
  # Asegura la dependencia del clúster AKS
  depends_on = [
    data.azurerm_kubernetes_cluster.aks, time_sleep.wait_project_identities
    # Puedes añadir un recurso para esperar a que el Pod 'vault-0' esté listo aquí
  ]

  # --- 1. Inicializar Vault (Crea el archivo vault-keys.txt) ---
  # El comando de inicialización y la redirección de la salida deben estar en una sola línea.
  provisioner "local-exec" {
    command = "kubectl exec -n vault vault-0 -- vault operator init -key-shares=${local.vault_shares} -key-threshold=${local.vault_threshold} > vault-keys.txt"
    
    # Esta operación se realiza solo una vez.
    when    = create 
  }
  
  # --- 2. Desbloquear Vault (Unseal) ---
  # La lógica de bucle se sustituye por la ejecución secuencial de las claves necesarias
  # (asumiendo 3 como umbral, que es el valor de 'vault_threshold').
  # Usamos 'grep' y 'sed' para extraer cada una de las 3 primeras claves del archivo.
  provisioner "local-exec" {
    # Comando condensado a una sola línea:
    command = "KEY1=$(grep 'Unseal Key 1:' vault-keys.txt | awk '{print $NF}'); KEY2=$(grep 'Unseal Key 2:' vault-keys.txt | awk '{print $NF}'); KEY3=$(grep 'Unseal Key 3:' vault-keys.txt | awk '{print $NF}'); if [ -f vault-keys.txt ] && [ -s vault-keys.txt ]; then kubectl exec -n vault vault-0 -- vault operator unseal $KEY1; sleep 5; kubectl exec -n vault vault-0 -- vault operator unseal $KEY2; sleep 5; kubectl exec -n vault vault-0 -- vault operator unseal $KEY3; echo 'Vault unsealing sequence completed.'; else echo 'Vault keys file not found or is empty. Cannot unseal.'; exit 1; fi"

    # Esta operación también se realiza solo una vez.
    when    = create
  }
  
  provisioner "local-exec" {
  # Corregido: Agregado el espacio y usando la ruta absoluta para el archivo de salida
  command = "grep 'Root Token: ' vault-keys.txt | awk '{print $NF}' > ${local.root_token_filepath}"
  when    = create
  }
}
data "local_file" "vault_root_token_reader" {
  # Utiliza la ruta absoluta al archivo generado por el provisioner de Vault
  filename = local.root_token_filepath 
  
  # CRÍTICO: Fuerza la dependencia para que el archivo sea creado antes de intentar leerlo.
  depends_on = [null_resource.vault_initialization]
}

resource "null_resource" "execute_besu_installation" {
  # Los triggers aseguran que se ejecute si el script cambia
  triggers = {
    script_content = filemd5("${local.script_install_dir}/install.sh")
    aks_endpoint_val = local.aks_endpoint
  }

  depends_on = [
    # Dependencia de la lectura del token (el archivo debe existir y ser leído)
    data.local_file.vault_root_token_reader, 
    # Dependencia del recurso que obtiene las credenciales (para kubectl)
    null_resource.aks_kubeconfig, 
    # Dependencia del recurso que modifica el hosts file
    null_resource.modificar_hosts, 
  ]

  provisioner "local-exec" {    
    # CRÍTICO: Establece el Directorio de Trabajo al directorio donde está install.sh
    working_dir = local.script_install_dir
    
    # Ejecuta el script (usando "./" ya que estamos en el working_dir correcto)
    command = "./install.sh ${trimspace(data.local_file.vault_root_token_reader.content)} ${azurerm_kubernetes_cluster.aks.kube_config[0].host}"
    when    = create 
  }
}
