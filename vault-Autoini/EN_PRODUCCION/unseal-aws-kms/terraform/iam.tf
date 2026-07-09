# 1. Rol de IAM con la política de confianza (Trust Policy) para el Service Account
resource "aws_iam_role" "vault_unseal_role" {
  name        = "vault-unseal-role"
  description = "Role for Vault unseal service account"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/311f3d50-401f-47dc-87a7-fbfd1d7f245a"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "oidc.eks.us-east-1.amazonaws.com/id/311f3d50-401f-47dc-87a7-fbfd1d7f245a:aud" = "sts.amazonaws.com"
            "oidc.eks.us-east-1.amazonaws.com/id/311f3d50-401f-47dc-87a7-fbfd1d7f245a:sub" = "system:serviceaccount:vault:vault-unseal-sa"
          }
        }
      }
    ]
  })
}

# 2. Política de permisos inline adjuntada al rol
resource "aws_iam_role_policy" "vault_unseal_policy" {
  name = "vault-unseal-policy"
  role = aws_iam_role.vault_unseal_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = [
          aws_kms_key.vault_unseal.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "${aws_secretsmanager_secret.vault_keys.arn}*"
        ]
      }
    ]
  })
}