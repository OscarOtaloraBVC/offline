output "kms_key_arn" {
  value       = aws_kms_key.vault_unseal.arn
  description = "ARN de la clave KMS creada"
}

output "secret_arn" {
  value       = aws_secretsmanager_secret.vault_keys.arn
  description = "ARN del Secreto en Secrets Manager"
}

output "iam_role_arn" {
  value       = aws_iam_role.vault_unseal_role.arn
  description = "ARN del rol de IAM para configurar en el Service Account de Kubernetes"
}