#!/bin/bash

PATHPROJECT=/opt/rbac-manager
APP_DIRECTORY="$PATHPROJECT/backend/python" # Directory containing main.py
## Important set var in SO
export RBAC_DB_SQLITE3_PATH="/opt/rbac-manager/data/rbac-sqlite3.db"
export RBAC_CLUSTER_NAME="nuam-poc1"
export RBAC_CLUSTER_URL="https://localhost:6443"
export RBAC_CLUSTER_CA_CRT_PATH="/opt/rbac-manager/data/ca.crt"
export RBAC_ADDITIONAL_RESOURCES='[{"namespaced": true, "resource": "pods/exec", "apiversion": "v1"}, {"namespaced": true, "resource": "pods/portforward", "apiversion": "v1"}, {"namespaced": true, "resource": "pods/log", "apiversion": "v1"},{"namespaced": true, "resource": "pods/proxy", "apiversion": "v1"}]'

## Check if file RBAC_DB_SQLITE3_PATH exist
if [ ! -f "$RBAC_DB_SQLITE3_PATH" ]; then
    echo "File $RBAC_DB_SQLITE3_PATH doesn't found"
    exit 0
fi

## Check if file RBAC_CLUSTER_CA_CRT_PATH exist
if [ ! -f "$RBAC_CLUSTER_CA_CRT_PATH" ]; then
    echo "File $RBAC_CLUSTER_CA_CRT_PATH doesn't found"
    exit 0
fi

VENV=$PATHPROJECT/backend/venv/bin/activate
if [ ! -f "$VENV" ]; then
    echo "File $VENV doesn't found"
fi

source $VENV

##export RBAC_STATIC_FRONTEND_DIR="/opt/rbac-manager/frontend/build"

# Navigate to the directory containing main.py
cd "$APP_DIRECTORY"

# It's generally better to install dependencies once, not every time the script runs.
# Consider if this pip install is truly needed here every time,
# or if it should be part of a setup process.
echo "Ensuring dependencies are installed..."
pip install fastapi "uvicorn[standard]" pydantic # Make sure your Python env is active

echo "Current working directory: $(pwd)" # For debugging, will show .../backend/python
echo "Starting Uvicorn server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000