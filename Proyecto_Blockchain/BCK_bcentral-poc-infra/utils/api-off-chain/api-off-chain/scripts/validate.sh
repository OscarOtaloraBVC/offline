#!/bin/bash

# Script para validar la especificación OpenAPI utilizando @redocly/cli

# Verificar si @redocly/cli está instalado
if ! command -v redocly &> /dev/null
then
    echo "@redocly/cli no está instalado. Por favor, instálalo usando npm install -g @redocly/cli o usa npx."
    exit 1
fi

# Ruta al archivo de especificación OpenAPI
SPEC_FILE="./specs/offchain-api.yaml"

# Validar la especificación
npx @redocly/cli lint $SPEC_FILE

# Verificar el resultado de la validación
if [ $? -eq 0 ]; then
    echo "La especificación OpenAPI es válida."
else
    echo "La especificación OpenAPI contiene errores."
    exit 1
fi