#!/bin/bash

NAMESPACE="blockscout"
RELEASE_NAME="explorer"
HOST="etablockscoutbc.labbcch.local"

SECRET_KEY=$(openssl rand -base64 64 | tr -d '\n')

kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

PG_USER="admin"
PG_PASSWORD="admin_password"
PG_HOST="postgresql-service.postgresql.svc.cluster.local"
PG_PORT="5432"
PG_DBNAME="blockscout"

# Crear Secret con los certificados personalizados ANTES del Ingress
echo "Creando Secret con certificados personalizados..."
CERT_FILE="etablockscoutbc.labbcch.local.cer"
KEY_FILE="etablockscoutbc.labbcch.local-orig.key"

if [[ -f "$CERT_FILE" && -f "$KEY_FILE" ]]; then
    # Codificar certificados a base64
    TLS_CRT=$(cat "$CERT_FILE" | base64 | tr -d '\n')
    TLS_KEY=$(cat "$KEY_FILE" | base64 | tr -d '\n')
    
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: blockscout-custom-tls
  namespace: $NAMESPACE
type: kubernetes.io/tls
data:
  tls.crt: $TLS_CRT
  tls.key: $TLS_KEY
EOF
    echo "✅ Secret 'blockscout-custom-tls' creado con certificados personalizados"
else
    echo "⚠️  Advertencia: No se encontraron los archivos de certificado"
    echo "   Asegúrate de que existan: $CERT_FILE y $KEY_FILE"
    echo "   Se continuará sin certificados personalizados"
fi

cat > values-temp.yaml <<EOF
config:
  network:
    id: "1337"
    name: "B-Central Testnet"
    currency:
      name: "B-Central"
      symbol: "BCEN"
      decimals: "18"
  prometheus:
    enabled: false
  testnet: true
  account:
    enabled: false
  nameService:
    enabled: false
  redirect:
    enabled: false

blockscout:
  enabled: true
  replicaCount: 1
  image:
    repository: labbcch.azurecr.io/dlt/blockscout  # ← Imagen desde el ACR 
    tag: "9.3.2"
    pullPolicy: Always
  env:
    DATABASE_URL: "postgresql://${PG_USER}:${PG_PASSWORD}@${PG_HOST}:${PG_PORT}/${PG_DBNAME}"
    POOL_SIZE: "10"
    ETHEREUM_JSONRPC_VARIANT: "besu"
    ETHEREUM_JSONRPC_HTTP_URL: "http://besu-node-validator-1.bcentral-testnet.svc.cluster.local:8545"
    ETHEREUM_JSONRPC_WS_URL: "ws://besu-node-validator-1.bcentral-testnet.svc.cluster.local:8546"
    ECTO_USE_SSL: "false"
    SECRET_KEY_BASE: "${SECRET_KEY}"
    MIX_ENV: "prod"
    DISABLE_EXCHANGE_RATES: "true"
    INDEXER_DISABLE_PENDING_TRANSACTIONS_FETCHER: "true"
  resources:
    limits:
      cpu: 2
      memory: 4Gi
    requests:
      cpu: 500m
      memory: 1Gi

frontend:
  enabled: true
  replicaCount: 1
  image:
    repository: labbcch.azurecr.io/dlt/blockscout-frontend  # ← Imagen desde el ACR
    tag: "2.5.3"
    pullPolicy: Always
  env:
    NEXT_PUBLIC_API_WEBSOCKET_PROTOCOL: "wss"
    NEXT_PUBLIC_APP_HOST: "${HOST}"
    NEXT_PUBLIC_APP_PROTOCOL: "https"
    NEXT_PUBLIC_API_HOST: "${HOST}"
    NEXT_PUBLIC_API_PROTOCOL: "https"
  resources:
    limits:
      cpu: 500m
      memory: 1Gi
    requests:
      cpu: 250m
      memory: 256Mi

stats:
  enabled: false

userOpsIndexer:
  enabled: false
EOF

helm upgrade --install $RELEASE_NAME blockscout/blockscout-stack \
  --namespace $NAMESPACE \
  --values values-temp.yaml \
  --wait --timeout 10m

# Create Ingress con certificados personalizados
echo "Creando Ingress con certificados personalizados..."
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: blockscout-ingress
  namespace: $NAMESPACE
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    # Se ha eliminado cert-manager para usar certificados personalizados
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - ${HOST}
    secretName: blockscout-custom-tls  # ← Usa el Secret personalizado
  rules:
  - host: ${HOST}
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: explorer-blockscout-stack-blockscout-svc
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: explorer-blockscout-stack-frontend-svc
            port:
              number: 80
EOF

rm values-temp.yaml

echo ""
echo "✅ Instalación completada"
echo ""
echo "Blockscout estará disponible en: https://${HOST}"
echo ""
echo "📋 Resumen de certificados aplicados:"
echo "   - Se está usando el Secret: blockscout-custom-tls"
echo "   - Certificado: etablockscoutbc.labbcch.local.cer"
echo "   - Llave privada: etablockscoutbc.labbcch.local.key"
echo ""
echo "📝 Para verificar el certificado:"
echo "   kubectl describe secret blockscout-custom-tls -n $NAMESPACE"
echo ""
echo "⚠️  Nota: Asegúrate de:"
echo "   1. El DNS apunte al Load Balancer del Ingress Controller"
echo "   2. El certificado sea válido para el dominio: ${HOST}"
echo "   3. Los archivos de certificado estén en el directorio actual"