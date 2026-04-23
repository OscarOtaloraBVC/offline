# Pipelines de Automatización de despliegues en Azure DevOps

## Visión General

Esta suite de pipelines Azure DevOps representa un sistema de automatización para el despliegue de una plataforma blockchain completa en Azure Kubernetes Service (AKS). Diseñado bajo principios Infrastructure as Code (IaC) y GitOps, el conjunto permite gestionar desde la infraestructura cloud hasta aplicaciones blockchain con consistencia, repetibilidad y seguridad.

## 🎯 Propósito Principal

Automatizar el ciclo completo de vida de la plataforma blockchain en Azure:

1. Infraestructura Cloud → Creación y gestión de recursos Azure

2. Red Blockchain → Despliegue de nodos Hyperledger Besu

3. Explorador → Instalación de Blockscout para monitoreo

4. Conectividad → Configuración de red y seguridad

## 🔄 Flujo de Automatización

```
  ┌──────────────────────────┐
  | Infraestructura Terraform|
  └──────────────────────────┘
               |
               v
  ┌──────────────────────────┐
  |   Cluster AKS + Redes    |
  └──────────────────────────┘
        /              \
       /                \
      v                  v
┌────────────┐    ┌──────────────┐
|    Red     |    |  Explorador  |
| Blockchain |===>|  Blockscout  |
|   Besu     |    |              |
└────────────┘    └──────────────┘
                         |
                         v
                  ┌──────────────┐
                  |  Plataforma  |
                  |  Operativa   |
                  |     POC      |                  
                  └──────────────┘
```

Pipeline 1: Infraestructura Base (azure-pipelines-DeployCluster.yml.yml)

"El Cimiento" - Automatiza la creación de la base tecnológica:

✅ Cluster AKS con configuración optimizada

✅ Redes VNet, Storage, Identidad

✅ Integración GitOps con Flux CD

✅ Estado remoto para colaboración equipo

Pipeline 2: Red Blockchain (azure-pipeline-Deploy_Hype_Besu.yml)

"El Core" - Instala la red Hyperledger Besu enterprise:

✅ Arquitectura multi-nodo (4 validadores + 3 peers)

✅ Genesis automático - configuración inicial automatizada

✅ API Gateway con Ambassador Edge Stack

✅ Monitoreo integrado con ServiceMonitors

✅ Storage persistente configurado

Pipeline 3: Explorador/UI (azure-pipeline-Deploy_Blockscout.yml)
"La Interfaz" - Despliega el dashboard de monitoreo blockchain:

✅ Stack completo backend (Elixir/Phoenix) + frontend (Next.js)

✅ Certificados TLS automáticos

✅ Routing inteligente (/api vs / frontend)

✅ Variables sensibles gestionadas centralmente

✅ Health checks y rollback automático

## ⚡ Beneficios de Automatización

### 🕒 Velocidad y Eficiencia

✅De minutos a segundos en despliegues repetitivos

✅Elimina errores humanos en configuraciones complejas

✅Consistencia garantizada entre entornos (dev, staging, prod)

### 🔒 Seguridad y Compliance

✅Secrets management centralizado en Azure Key Vault

✅Certificados TLS gestionados automáticamente

✅Auditoría completa de todos los despliegues

✅Políticas de red aplicadas consistentemente

### 🔄 DevOps y CI/CD

✅Git como fuente de verdad

✅Pipeline como código - versionado y revisable

✅Approval gates integrables para producción

✅Rollback automático en fallos

### 📊 Observabilidad

✅Logs centralizados en cada paso

✅Estado visible de todos los componentes

✅Métricas de despliegue automáticas

### 🔄 Actualizaciones

✅Parches seguridad: Solo re-ejecutar pipeline afectado

✅Escalado: Modificar variables → Re-desplegar

✅Recuperación desastres: Pipelines idempotentes para restore

### 🔧 Mantenimiento

✅Rotación certificados: Automático vía pipeline

✅Actualización versión: Cambiar tag imagen → Re-desplegar

✅Backup/restore: Integrable en pipelines existentes