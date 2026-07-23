#!/bin/bash
# entrypoint.sh

set -e

# Cambiar al directorio del backend
cd /opt/unseal-app/backend

# Configurar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/opt/unseal-app/backend"

# Crear directorio de datos si no existe
mkdir -p /data

# Ejecutar la aplicación
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000