## Ejecución

Para ejecutar los manifiestos terraform previo crear el perfil Perfil --- SandboxMCD

### 1 Instalar y configurar AWS CLI

Perfil: SandboxMCD

Configurar Perfil

```bash
aws configure sso
```

SandboxMCD
```text
URL de inicio de SSO
<https://identitycenter.amazonaws.com/ssoins-7223e41207ba70dc>
Región de SSO
us-east-1
```
```bash
There are 5 AWS accounts available to you.
Using the account ID 722959781259
The only role available to you is: Power_Users_Iam
Using the role name "Power_Users_Iam"
Default client Region [None]: us-east-2
CLI default output format (json if not specified) [None]:
Profile name [Power_Users_Iam-722959781259]: SandboxMCD
To use this profile, specify the profile name using --profile, as shown:

# Asegurarce de la creacion del perfil 

aws sts get-caller-identity --profile SandboxMCD
```

Estar logueado en la CLI con 

```bash
aws sso login --profile SandboxMCD
```

### 2 Ejecutar los comandos de Terraform:

```bash
terraform init
terraform plan
terraform apply
```
