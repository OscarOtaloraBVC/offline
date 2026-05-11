#!/bin/bash

PATHPROJECT=/opt/rbac-manager
#APP_DIRECTORY="$PATHPROJECT/backend/python" # Directory containing main.py
APP_DIRECTORY="$PATHPROJECT/backend"
## Important set var in SO
###export RBAC_DB_SQLITE3_PATH="/opt/rbac-manager/.data/rbac-sqlite3.db"

/opt/rbac-manager/backend/bin/install-create-db-sqlite3.sh

# Navigate to the directory containing main.py
cd "$APP_DIRECTORY"

echo "Ensuring dependencies are installed..."
pip install fastapi "uvicorn[standard]" pydantic # Make sure your Python env is active

echo "Current working directory: $(pwd)" # For debugging, will show .../backend/python
echo "Starting Uvicorn server..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000