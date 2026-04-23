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
    repository: ghcr.io/blockscout/blockscout
    tag: "latest"
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
    repository: ghcr.io/blockscout/frontend
    tag: "latest"
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

# Create Ingress
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: blockscout-ingress
  namespace: $NAMESPACE
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - ${HOST}
    secretName: blockscout-tls
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
echo "Nota: Asegúrate de que el DNS apunte al Load Balancer del Ingress Controller"
