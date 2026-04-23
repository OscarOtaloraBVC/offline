variable "resource_group_name" {
  type        = string
  description = "Nombre del Resource Group"
}

variable "location" {
  type        = string
  description = "Ubicación del Resource Group y el Cluster"
}

variable "aks_cluster_name" {
  type        = string
  description = "Nombre del Cluster AKS"
}

variable "dns_prefix" {
  type        = string
  description = "Prefijo DNS para el cluster AKS"
}

variable "min_count" {
  type        = number
  description = "Número mínimo de nodos para autoscale"
}

variable "max_count" {
  type        = number
  description = "Número máximo de nodos para autoscale"
}

variable "vm_size" {
  type        = string
  description = "Tamaño de la VM para los nodos"
}

variable "kubernetes_version" {
  type        = string
  description = "Versión de Kubernetes"
}

variable "tag_app" {
  type        = string
  description = "Tag para identificar la aplicación"
}

variable "node_count_init" {
  type        = number
  description = "Número inicial de nodos"
}

# Nuevas variables para Flux
variable "git_token" {
  type        = string
  description = "Token de acceso para Azure DevOps (Git)"
  default     = ""
  sensitive   = true
}

variable "enable_flux_bootstrap" {
  type        = bool
  description = "Habilitar bootstrap automático de Flux"
  default     = false
}

variable "flux_repo_url" {
  type        = string
  description = "URL del repositorio Git para Flux"
  default     = "https://dev.azure.com/Nuam-BancoCentral/Blockchain/_git/bcentral-poc-infra"
}

variable "flux_branch" {
  type        = string
  description = "Rama del repositorio para Flux"
  default     = "main"
}

variable "flux_path" {
  type        = string
  description = "Ruta dentro del repositorio para Flux"
  default     = "./env/dev"
}