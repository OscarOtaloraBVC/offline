# Implementación de Velero con S3 (AWS)

Guía paso a paso para implementar **Velero** utilizando un bucket de **Amazon S3** como backend de almacenamiento para backups de Kubernetes.

---

## Índice

1. [Prerrequisitos](#1-prerrequisitos)
2. [Instalación del CLI de Velero](#2-instalación-del-cli-de-velero)
3. [Autenticación en AWS](#3-autenticación-en-aws)
4. [Creación del bucket S3](#4-creación-del-bucket-s3)
5. [Creación de usuario IAM y política de permisos](#5-creación-de-usuario-iam-y-política-de-permisos)
6. [Generación de Access Keys](#6-generación-de-access-keys)
7. [Verificación de la configuración](#7-verificación-de-la-configuración)
8. [Ejecución de backups manuales](#8-ejecución-de-backups-manuales)
9. [Monitoreo y consulta de backups](#9-monitoreo-y-consulta-de-backups)

---

## 1. Prerrequisitos

- Acceso a un clúster de Kubernetes con permisos de administrador.
- AWS CLI configurado con perfiles SSO (`aws configure sso`).
- Permisos para crear buckets S3, usuarios y políticas IAM en la cuenta AWS destino.
- `kubectl` configurado apuntando al clúster objetivo.

---

Arquitectura

```bash
┌────────────────────────────────────────────────────────────────┐
│                        CLUSTER KUBERNETES                      │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    NAMESPACE: VELERO                    │   │
│  │                                                         │   │
│  │  ┌───────────────┐  ┌───────────────────────────────┐   │   │
│  │  │   Velero      │  │      Velero Node Agent        │   │   │
│  │  │   Controller  │  │      (Restic/Kopia)           │   │   │
│  │  │   Manager     │  │                               │   │   │
│  │  └──────┬────────┘  └──────────────┬────────────────┘   │   │
│  │         │                          │                    │   │
│  │         └──────────┬───────────────┘                    │   │
│  │                    │                                    │   │
│  │          ┌─────────▼─────────┐                          │   │
│  │          │   Schedules       │                          │   │
│  │          │   - Diario        │                          │   │
│  │          │   - Semanal       │                          │   │
│  │          └───────────────────┘                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                 │
└──────────────────────────────┼─────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   S3 Storage (AWS)   │
                    │   Bucket: velero-    │
                    │   backups            │
                    └──────────────────────┘
```


## 2. Instalación del CLI de Velero en la consola de adminitración

> En la cosnola (en este caso WSL / Linux)

```bash
# Descargar el binario de Velero (ajustar versión según necesidad)
curl -L https://github.com/vmware-tanzu/velero/releases/download/v1.15.0/velero-v1.15.0-linux-amd64.tar.gz -o /tmp/velero.tar.gz

# Extraer el archivo
tar -xzvf /tmp/velero.tar.gz -C /tmp

# Mover el binario a un directorio del PATH
sudo mv /tmp/velero-v1.15.0-linux-amd64/velero /usr/local/bin/

# Validar instalación
velero version
```

> Plugin de AWS:** Velero requiere el plugin oficial [`velero-plugin-for-aws`](https://github.com/velero-io/velero-plugin-for-aws#create-s3-bucket) para integrarse con S3.

---

## 3. Autenticación en AWS

Autenticarse contra la cuenta AWS mediante SSO utilizando el perfil correspondiente al ambiente:

> En la cosnola (en este caso WSL / Linux)

Previo a la ejecución de estos comandos se debe tener configurado un perfil [`aws configure sso`](https://docs.aws.amazon.com/cli/latest/reference/configure/sso.html) para la conexión al ambiente AWS.

```bash
aws sso login --profile PERFIL-AWS-SSO

# Alternativa con código de dispositivo (útil en entornos sin navegador local)
aws sso login --profile PERFIL-AWS-SSO --use-device-code
```

> Consola AWS: `https://us-east-1.console.aws.amazon.com/console/home?region=us-east-1`

> La region de la consola en este caso es `us-east-1` pero en todos los comandos se debe ajustaracorde a la region 
---

## 4. Creación del bucket S3

> En la cosnola (en este caso WSL / Linux)

### 4.1 Crear el bucket

```bash
aws s3api create-bucket \
    --bucket velero-backups-NOMBRE-BUCKET \
    --region us-east-1 \
    --profile PERFIL-AWS-SSO
```

**Resultado esperado:**

```json
{
    "Location": "/velero-backups-NOMBRE-BUCKET",
    "BucketArn": "arn:aws:s3:::velero-backups-NOMBRE-BUCKET"
}
```

### 4.2 Habilitar versionado

Habilita el versionado del bucket para proteger los backups frente a eliminaciones accidentales:

```bash
aws s3api put-bucket-versioning \
    --bucket velero-backups-NOMBRE-BUCKET \
    --versioning-configuration Status=Enabled \
    --profile PERFIL-AWS-SSO
```

---

## 5. Creación de usuario IAM y política de permisos

> En la cosnola (en este caso WSL / Linux)

### 5.1 Crear el usuario IAM

```bash
aws iam create-user \
    --user-name velero-s3-user \
    --profile PERFIL-AWS-SSO
```

**Resultado esperado:**

```json
{
    "User": {
        "Path": "/",
        "UserName": "velero-s3-user",
        "UserId": "AIDAQ2Z3INJ2A********",
        "Arn": "arn:aws:iam::05756****092:user/velero-s3-user",
        "CreateDate": "2026-08-13T20:12:13+00:00"
    }
}
```

### 5.2 Crear la política de permisos

```bash
cat > velero-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeVolumes",
                "ec2:DescribeSnapshots",
                "ec2:CreateTags",
                "ec2:CreateVolume",
                "ec2:CreateSnapshot",
                "ec2:DeleteSnapshot"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:PutObject",
                "s3:AbortMultipartUpload",
                "s3:ListMultipartUploadParts",
                "s3:ListBucketMultipartUploads"
            ],
            "Resource": [
                "arn:aws:s3:::velero-backups-NOMBRE-BUCKET",
                "arn:aws:s3:::velero-backups-NOMBRE-BUCKET/*"
            ]
        }
    ]
}
EOF
```

Los permisos EC2 son necesarios para backups de volúmenes (snapshots), mientras que los permisos S3 permiten a Velero leer, escribir y gestionar objetos en el bucket de backups.

### 5.3 Asignar la política al usuario

```bash
aws iam put-user-policy \
    --user-name velero-s3-user \
    --policy-name velero-s3-policy \
    --policy-document file://velero-policy.json \
    --profile PERFIL-AWS-SSO
```

---

## 6. Generación de Access Keys

```bash
aws iam create-access-key \
    --user-name velero-s3-user \
    --profile PERFIL-AWS-SSO
```

> ⚠️ **Seguridad:** El `SecretAccessKey` solo se muestra una vez al momento de la creación. Debe almacenarse de forma segura (por ejemplo, en un Secret de Kubernetes o en un gestor de secretos como Vault) y **nunca** debe versionarse en repositorios de código ni documentación en texto plano.

Credenciales generadas para Velero (usar el archivo `credentials-velero` al configurar el plugin):

```ini
[default]
aws_access_key_id=<ACCESS_KEY_ID>
aws_secret_access_key=<SECRET_ACCESS_KEY>
```

---

## 7. Verificación de la configuración

> En la cosnola (en este caso WSL / Linux)

### 7.1 Verificar el usuario y la política

```bash
# Ver todos los usuarios
aws iam list-users --profile PERFIL-AWS-SSO

# Buscar específicamente al usuario
aws iam get-user --user-name velero-s3-user --profile PERFIL-AWS-SSO

# Listar todas las políticas asociadas al usuario
aws iam list-user-policies --user-name velero-s3-user --profile PERFIL-AWS-SSO

# Ver el contenido de la política específica
aws iam get-user-policy \
    --user-name velero-s3-user \
    --policy-name velero-s3-policy \
    --profile PERFIL-AWS-SSO
```

### 7.2 Validar acceso y permisos sobre el bucket

```bash
# Listar contenido del bucket
aws s3 ls s3://velero-backups-NOMBRE-BUCKET \
    --profile PERFIL-AWS-SSO

# Crear un archivo de prueba
echo "test" > test-file.txt

# Subirlo al bucket (debe listarse desde la consola)
aws s3 cp test-file.txt \
    s3://velero-backups-NOMBRE-BUCKET/test-file.txt \
    --profile PERFIL-AWS-SSO

# Verificar que existe
aws s3 ls s3://velero-backups-NOMBRE-BUCKET/ \
    --profile PERFIL-AWS-SSO

# Eliminar el archivo de prueba
aws s3 rm s3://velero-backups-NOMBRE-BUCKET/test-file.txt \
    --profile PERFIL-AWS-SSO
```

### 7.3 Verificar las Access Keys del usuario

```bash
aws iam list-access-keys --user-name velero-s3-user --profile PERFIL-AWS-SSO
```

---

## 8. Ejecución de backups manuales

### Backup de un solo namespace

```bash
velero backup create manual-test \
  --include-namespaces vault \
  --ttl 2h
```

### Backup de múltiples namespaces

```bash
velero backup create multiples-namespaces \
  --include-namespaces vault,keycloak \
  --ttl 2h
```

---

## 9. Monitoreo y consulta de backups

```bash
# Ver el estado del backup
velero backup describe manual-test

# Ver lista de todos los backups
velero backup get

# Ver los logs del backup
velero backup logs manual-test

# Ver detalles en formato YAML
kubectl get backup manual-test -n velero -o yaml

# Ver el progreso del backup (si se usó --wait, esto no será necesario)
velero backup describe multiples-namespaces | grep -A 10 "Status:"
```

---

## Recursos relacionados

- [Documentación oficial de Velero](https://velero.io/docs/)
- [Plugin de AWS para Velero](https://github.com/velero-io/velero-plugin-for-aws)
- [Backups con Velero](https://nuamexchange.atlassian.net/wiki/x/CwAyIg)
- [Automatización de Backups con Velero](https://nuamexchange.atlassian.net/wiki/x/FoBYIg)

## Notas de seguridad

- Las credenciales IAM (`AccessKeyId` / `SecretAccessKey`) mostradas en este proceso deben tratarse como información sensible: no deben quedar registradas en documentos, tickets o repositorios sin cifrar.
- Se recomienda rotar periódicamente las Access Keys del usuario `velero-s3-user` y, de ser posible, evaluar el uso de **IRSA (IAM Roles for Service Accounts)** en lugar de Access Keys estáticas para entornos EKS.
- El versionado del bucket S3 ayuda a mitigar pérdidas de datos por eliminación accidental, pero no reemplaza una política de retención y ciclo de vida (lifecycle policy) adecuada.
