#!/bin/bash
# Este script se ejecuta UNA SOLA VEZ durante la inicialización de Vault 
# Script de Almacenamiento en AWS Secrets Manager de las claves de unseal y el root token de Vault

REGION="us-east-1"
KMS_KEY_ID="alias/vault-unseal-key"

# 1. Guardar Root Token
aws secretsmanager create-secret \
  --name vault-root-token \
  --secret-string "hvs.xyz123abc..." \
  --kms-key-id $KMS_KEY_ID \
  --region $REGION \
  --tags Key=Application,Value=Vault Key=Environment,Value=Production

# 2. Guardar las 3 Unseal Keys
aws secretsmanager create-secret \
  --name vault-unseal-key-0 \
  --secret-string "f9k3j8d2h..." \
  --kms-key-id $KMS_KEY_ID \
  --region $REGION

aws secretsmanager create-secret \
  --name vault-unseal-key-1 \
  --secret-string "g7h4k9j3d..." \
  --kms-key-id $KMS_KEY_ID \
  --region $REGION

aws secretsmanager create-secret \
  --name vault-unseal-key-2 \
  --secret-string "l2m5n8p1q..." \
  --kms-key-id $KMS_KEY_ID \
  --region $REGION

echo "✅ Todas las claves han sido almacenadas en AWS Secrets Manager"