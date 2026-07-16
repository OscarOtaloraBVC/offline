# 1. Crear la KMS Key
resource "aws_kms_key" "vault_unseal" {
  description             = "Clave para desbloquear Vault"
  key_usage               = "ENCRYPT_DECRYPT"
  customer_master_key_spec = "SYMMETRIC_DEFAULT"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Environment = "SandboxMCD"
    Project     = "Vault"
  }
}

# 2. Crear el Alias para la KMS Key
resource "aws_kms_alias" "vault_unseal_alias" {
  name          = "alias/vault-unseal-key"
  target_key_id = aws_kms_key.vault_unseal.key_id
}

# 3. Datos de la cuenta actual para la política
data "aws_caller_identity" "current" {}

# 4. Configurar política de la KMS Key
resource "aws_kms_key_policy" "vault_unseal_policy" {
  key_id = aws_kms_key.vault_unseal.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      }
    ]
  })
}