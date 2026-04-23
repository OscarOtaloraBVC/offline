# README del Proyecto Blockscout en Kubernetes

Descripción
Este documento describe como desplegar Blockscout (backend + frontend) en el clúster de Kubernetes, utilizando por medio de una automatizacion en un scritp (install_ACR.sh o instal.sh), imágenes privadas almacenadas en Azure Container Registry (ACR) y exponiendo la aplicación mediante un Ingress con TLS.

El despliegue está orientado a una red Ethereum/Besu de tipo testnet y asume que la base de datos PostgreSQL ya existe y es accesible desde el clúster. 

Configura todos los componentes necesarios incluyendo el backend, frontend, base de datos y reglas de ingreso.

Características Principales

✅ Despliega Blockscout en un namespace específico de Kubernetes

✅ Configura conexión a base de datos PostgreSQL

✅ Establece conexión con un nodo Besu JSON-RPC

✅ Configura el frontend con variables de entorno apropiadas

✅ Crea reglas de Ingress para acceso HTTPS

✅ Genera automáticamente una clave secreta segura

⚙️ Requisitos previos

Cargar la imagenes en ACR 

- blockscout-frontend.tar
- blockscout.tar

Acceso a las imágenes en Azure Container Registry (ACR)

- blockscout-frontend:2.5.3
- blockscout:9.3.2 

Suposiciones (importantes)

Estos archivos existen en la máquina desde donde ejecutas el script:

- etablockscoutbc.labbcch.local.cer
- etablockscoutbc.labbcch.local-orig.key

El CN o SAN del certificado es:

-  etablockscoutbc.labbcch.local

Variables Configurables

| **Variable**              | **Descripción **              | **	Valor por Defecto**             |
|---------------------------|-------------------------------|-------------------------------------|
|NAMESPACE  | 	Namespace de Kubernetes  | blockscout
|RELEASE_NAME | Nombre del release de Helm | explorer
|HOST | Hostname para acceso público | etablockscoutbc.labbcch.local
|PG_HOST | Servicio PostgreSQL | postgresql-service.postgresql.svc.cluster.local
|PG_PORT | Puerto PostgreSQL | 5432
|PG_DBNAME | Nombre de la base de datos | blockscout
|PG_USER | Usuario de PostgreSQL | admin
|PG_PASSWORD | Contraseña de PostgreSQL | admin_password

Componentes Desplegados

1. Blockscout Backend
Imagen: labbcch.azurecr.io/dlt/blockscout:9.3.2
Conexión RPC: Besu en besu-node-validator-1.bcentral-testnet.svc.cluster.local
Recursos: 2 CPU / 4Gi RAM (límites), 500m CPU / 1Gi RAM (requests)

2. Frontend
Imagen: labbcch.azurecr.io/dlt/blockscout-frontend:2.5.3
Framework: Next.js
Recursos: 500m CPU / 1Gi RAM (límites), 250m CPU / 256Mi RAM (requests)

3. Configuración de Red
ID de Red: 1337
Nombre: "B-Central Testnet"

4. Ingress Configuration
TLS: Certificado Let's Encrypt automático

Paths:
/api → Servicio Blockscout backend
/ → Servicio Frontend

Funcionamiento del Script
Pasos de Ejecución

1. Generación de Clave Secreta
2. Crea una clave base64 de 64 bytes para SECRET_KEY_BASE
3. Creación de Namespace
4. Crea el namespace especificado si no existe
5. Generación de Values de Helm
6. Crea archivo temporal values-temp.yaml con toda la configuración
7. Elimina el archivo temporal de valores

Ejecución

bash
# Dar permisos de ejecución
chmod +x install_ACR.sh

# Ejecutar el script
./install_ACR.sh

## Notas Importantes
Seguridad

El script genera automáticamente una clave secreta segura
Las credenciales de PostgreSQL están hardcodeadas (considerar remover una ves ejecutado)

## Red

Asegurar que el DNS apunte al Load Balancer del Ingress Controller
Verificar conectividad con el nodo Besu
Confirmar acceso a la base de datos PostgreSQL

## Salida Esperada

Al finalizar exitosamente, el script mostrará:

text:

✅ Instalación completada
Blockscout estará disponible en: https://etablockscoutbc.labbcch.local
Nota: Asegúrate de que el DNS apunte al Load Balancer del Ingress Controller