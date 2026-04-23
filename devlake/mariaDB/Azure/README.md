DevLake Deployment

Este Proyecto contiene los manifiestos de Kubernetes para el despliegue de Apache DevLake (v1.0.2) utilizando MariaDB (MariaDB 10.6.25) como motor de base de datos persistente. El despliegue está diseñado para entornos en clusters Azure.

🏗️ Arquitectura del Sistema

El despliegue se organiza en el namespace devlake-mariadb y se compone de tres capas principales:

Capa de Datos: MariaDB 10.6 desplegado como StatefulSet con almacenamiento persistente local.

Capa de Aplicación: Apache DevLake gestionado mediante un HelmRelease de Flux.

Capa de Ingress: Exposición del servicio a través de devlake.nuam.com.

🛠️ Componentes Técnicos

1. Base de Datos (MariaDB)

Tipo: StatefulSet para garantizar la identidad de red y estabilidad del almacenamiento.
Configuración: Optimizada mediante un ConfigMap (custom.cnf) que ajusta el innodb_buffer_pool_size a 1G y el max_connections a 500 para cargas analíticas.
Persistencia: Utiliza un PersistentVolume de tipo hostPath (/data/mariadb) con capacidad de 10Gi.
Recursos: Reservas de 1 CPU y 6Gi de RAM, con límites de hasta 10Gi de RAM para prevenir OOM (Out of Memory).

1. Aplicación (Apache DevLake)

Gestión: Desplegado vía Flux CD utilizando HelmRepository y HelmRelease.
Sincronización: El HelmRelease incluye un postRenderer con parches de Kustomize para:
Inyectar un initContainer que espera a que MariaDB esté disponible en el puerto 3306.
Forzar el despliegue en el nodo k3d-devlake-server-0.
Secretos: Gestión de credenciales mediante objetos Secret codificados en Base64 y una clave de encriptación dedicada para los plugins de DevLake.

1. Flujo de Despliegue (Kustomization)

El archivo kustomization.yaml orquestra el orden de aplicación:
Namespace y Secretos.
Infraestructura de DB (ConfigMap, Service, StatefulSet).
Definiciones de Helm (Repo y Release).
Configuración de alertas.

🔐 Configuración de Secretos

El proyecto utiliza cuatro secretos principales:
devlake-mysql-auth: Credenciales de acceso para MariaDB.
mariadb-secret: Variables de entorno para la inicialización del contenedor.
devlake-encryption-secret: Clave ENCRYPTION_SECRET necesaria para que DevLake cifre tokens de acceso.
devlake-db-url: Cadena de conexión JDBC formateada para los componentes de la aplicación.

🚀 Instalación

Para desplegar este stack utilizando Kustomize:

Bash
kubectl apply -k .
