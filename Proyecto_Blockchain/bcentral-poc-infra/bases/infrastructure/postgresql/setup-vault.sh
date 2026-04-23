#!/bin/bash

# Script para configurar HashiCorp Vault con los secretos necesarios para la base de datos PostgreSQL.

# Variables
export VAULT_ADDR="http://localhost:8200"          # Dirección de Vault
#export VAULT_ADDR="http://vault.vault:8200"
#export VAULT_ADDR="http://172.193.32.109:8200"
export VAULT_TOKEN="hvs.<tokenroot>"    # Token de acceso a Vault
DB_SECRET_PATH="secretsv2/postgresql"                # Ruta donde se almacenarán los secretos de la base de datos
DB_USER="admin"                                    # Nombre de usuario de la base de datos
DB_PASSWORD="admin_password"                       # Contraseña de la base de datos
DB_HOST="postgresql-service"                       # Nombre del servicio de PostgreSQL en Kubernetes
DB_PORT="5432"                                     # Puerto de conexión a PostgreSQL

# Iniciar sesión en Vault
echo "Iniciando sesión en HashiCorp Vault..."
vault login token=$VAULT_TOKEN

# Crear la ruta de secretos si no existe
echo "Creando la ruta de secretos en Vault..."
vault kv put $DB_SECRET_PATH \
    username=$DB_USER \
    password=$DB_PASSWORD \
    host=$DB_HOST \
    port=$DB_PORT

echo "Secretos de la base de datos configurados en Vault."

# Fin del script
echo "Configuración de Vault completada."
