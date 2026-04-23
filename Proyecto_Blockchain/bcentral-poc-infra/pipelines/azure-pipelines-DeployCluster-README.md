# Azure Pipelines / Despliegue Cluster

Pipeline de infraestructura como código que despliega recursos Azure usando Terraform.

## Documentación Técnica

### Funcionalidad

- Gestión de infraestructura Azure via Terraform
- Pipeline de dos etapas: Plan + Apply
- Autenticación segura via OIDC (sin secrets en variables)
- Estado remoto en Azure Storage
- Integración con Flux CD para GitOps

### Ubicacion

en el repositorio bcentral-poc-infra crear un directorio **pipelines**

En Repositorio:
*bcentral-poc-infra\pipelines*

### Tecnologías

- IaC: Terraform 1.6.6
- Cloud: Azure (azurerm provider)
- Autenticación: OIDC con Azure Federated Token
- Estado: Azure Blob Storage
- GitOps: Flux CD

### Configuración Clave

- Variables en grupo: Deploy_Cluster
- Backend remoto: Azure Storage Account
- Autenticación: Service Principal via OIDC
- Token Git para Flux: $(FLUX_GIT_TOKEN)

## Grupo de Variables

Crear un Grupo de variables en Azure pipeline con

- Variable group name: **Deploy_Cluster**

- Variables:

|Nombre|valor|🔒|
|--|--|--|
|FLUX_GIT_TOKEN |Token de autenticaion en repositorio para flux|🔒 Variable Secreta (candado cerrado)|

### Procedimiento

1- Navegar a la Biblioteca: En el de Azure DevOps, seleccionar Pipelines > Library (Biblioteca) en el menú de la izquierda.

2- Crear un nuevo grupo: Hacer clic en + Variable group (+ Grupo de variables).

3- Configura las propiedades:

    - Ingresar un Nombre para el grupo (nombre: **Deploy_Cluster**).
    - Añadir una Descripción (opcional).
    - Añadir variables:
        - En la sección Variables, hacer clic en + Add (+ Agregar).
        - Introducir el Nombre y el Valor de la variable.
        - Para un secreto (como contraseñas), hacer clic en el ícono de candado al final de la fila para cifrarlo.
4- Guarda el grupo: Al terminar, hacer clic en Save (Guardar)

## Flujo

**Stage 1 - Terraform Plan:**

1- Checkout código y instala Terraform

2- Configura autenticación OIDC

3- Inicializa backend remoto

4- Valida y genera plan

5- Publica artefacto del plan

**Stage 2 - Terraform Apply:**

1- Descarga artefacto del plan

2- Vuelve a inicializar backend

3- Aplica cambios del plan

4- Despliega infraestructura

## Importacion en Azure PipeLines

Para importar el pipeline en Azure DevOps, se puede usar la opción "Importar PipeLine" desde el menú de Pipelines estado el arvhico .YML ubicado en el repositorio **bcentral-poc-infra\pipelines**, antes de su ejecucion se debe tener creado el grupo de variables y seguridad según sea necesario.

### Procedimiento

1- Navegar a Pipelines: En el proyecto de Azure DevOps, ir a la sección Pipelines.

2- Seleccionar "Nuevo PipeLine": Hacer clic en Nuevo PipeLine.

3- Eligir la ubicación del código fuente: Selecciona dónde está el archivo .yml (**Azure Repos Git**).

4- Seleccionar el Repositorio: **bcentral-poc-infra**.

5- En "Configurar su PipeLine": Selecionar **Archivo Azure PipeLine YAML Existente**.  

6- En **Seleecionar Archivo YAML Existente**

    - Elegir la rama / Branch : main. 
    - Elegir la ruta / Path: /pipelines/azure-pipelines-DeployCluster.yml

7- En Previsualizar: Se mostrara el contenideo del archivo.yml y en esta ventana se peude crear las variables.

8- En el icono de **Ejecutar / Run**: Se puede seleccionar Salvar o Ejecutar. importante Salvar.

## Seguridad

- No almacena credenciales en variables de pipeline
- Usa OIDC con tokens federados
- Estado en storage seguro
- Token Flux protegido como variable secreta

## Enlaces de Interes

- OIDC: <https://learn.microsoft.com/en-us/samples/azure-samples/azure-devops-terraform-oidc-ci-cd/azure-devops-terraform-oidc-ci-cd/>
- Grupo de Variables: <https://learn.microsoft.com/es-es/cli/azure/pipelines/variable-group?view=azure-cli-latest>
