# 1. Crear el contenedor del Secreto
resource "aws_secretsmanager_secret" "vault_keys" {
  name        = "vault-unseal-keys"
  description = "Vault unseal keys stored in AWS"
  
  # Usa la clave KMS creada anteriormente para encriptar este secreto si lo deseas:
  # kms_key_id = aws_kms_key.vault_unseal.arn
}

# 2. Agregar el valor del Secreto
resource "aws_secretsmanager_secret_version" "vault_keys_value" {
  secret_id     = aws_secretsmanager_secret.vault_keys.id
  secret_string = jsonencode({
    "unseal-key-1" = "ZitUR21abm0wVU9mNm1RbWJnNXpHbCtmZUpmZE5uZm83cGhac0ZCUXgzVWU="
    "unseal-key-2" = "RWtJZDRhWkFyQVZxLzY1NjVxRlFVT3IzcjFDMXhaaVVQb0czcDhRdzI5N2Y="
  })
}