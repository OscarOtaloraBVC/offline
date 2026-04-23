#!/bin/bash
# Script para generar clientes stubs en TypeScript y Go a partir de la especificación OpenAPI

# Variables
SPEC_FILE="./specs/offchain-api.yaml"
OUTPUT_DIR_TS="./clients/typescript"
OUTPUT_DIR_GO="./clients/go"

# Generar cliente TypeScript
echo "Generando cliente TypeScript..."
npx @openapitools/openapi-generator-cli generate -i $SPEC_FILE -g typescript-axios -o $OUTPUT_DIR_TS

# Generar cliente Go
echo "Generando cliente Go..."
npx @openapitools/openapi-generator-cli generate -i $SPEC_FILE -g go -o $OUTPUT_DIR_GO

echo "Clientes generados exitosamente."