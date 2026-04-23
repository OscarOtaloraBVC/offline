# Salida para mostrar cómo acceder al cluster
output "kube_config" {
  value = data.azurerm_kubernetes_cluster.aks_get.kube_config_raw
  sensitive = true # No mostrar la configuración en la salida
}

output "client_certificate" {
  value     = data.azurerm_kubernetes_cluster.aks_get.kube_config.0.client_certificate
  sensitive = true
}

output "kube_config_raw" {
  value     = data.azurerm_kubernetes_cluster.aks_get.kube_config_raw
  sensitive = true
}