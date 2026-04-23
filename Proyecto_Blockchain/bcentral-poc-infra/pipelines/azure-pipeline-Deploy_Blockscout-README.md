# Azure Pipelines / Despliegue Blockscout

Pipeline para desplegar Blockscout (explorador de bloques) en el cluster de AKS, configuración completa del stack con backend de base de datos, frontend y certificados TLS.

## Documentación Técnica

### Funcionalidad

- Despliega el stack de Blockscout (backend + frontend) en AKS
- Configura certificados TLS personalizados
- Crea Ingress para routing HTTP/HTTPS
- Gestiona secrets y variables de entorno sensibles

### Ubicacion

en el repositorio bcentral-poc-infra crear un directorio **pipelines**

En Repositorio:
*bcentral-poc-infra\pipelines*

### Tecnologías

- Orquestación: Kubernetes (AKS)
- Herramientas: Helm 3.14.0, kubectl
- Contenedores:
    - Blockscout 9.3.2 (backend)
    - Blockscout Frontend 2.5.3 (frontend)
- Base de datos: PostgreSQL (externo)
- Networking: NGINX Ingress Controller
- Blockchain: Hyperledger Besu (JSON-RPC)

### Configuración Clave

- Variables en grupo: blockscout-deploy-vars, FRONTEND-GROUP
- Conexión a Besu via service DNS interno
- Certificados TLS desde archivos locales

## Grupo de Variables

Crear un Grupo de variables en Azure pipeline con

- Variable group name: **blockscout-deploy-vars**

- Variables:

|Nombre|valor|🔒|
|--|--|--|
|AKS_NAMESPACE|AKS_NAMESPACE| 🔓 Variable (Candado Abierto)|
|BLOCKSCOUT_HOST|etablockscoutbc.labbcch.local|🔓 Variable (Candado Abierto)|
|PG_DBNAME|blockscout|🔓 Variable (Candado Abierto)|
|PG_PASSWORD|admin_password|🔒 Variable Secreta (candado cerrado)|
|PG_PORT|5432|🔓 Variable (Candado Abierto)|
|PG_USER|admin|🔓 Variable (Candado Abierto)|
|RELEASE_NAME|explorer|🔓 Variable (Candado Abierto)|

### Procedimiento

1- Navegar a la Biblioteca: En el de Azure DevOps, seleccionar Pipelines > Library (Biblioteca) en el menú de la izquierda.

2- Crear un nuevo grupo: Hacer clic en + Variable group (+ Grupo de variables).

3- Configura las propiedades:

    - Ingresar un Nombre para el grupo (nombre: **blockscout-deploy-vars**).
    - Añadir una Descripción (opcional).
    - Añadir variables:
        - En la sección Variables, hacer clic en + Add (+ Agregar).
        - Introducir el Nombre y el Valor de la variable.
        - Para un secreto (como contraseñas), hacer clic en el ícono de candado al final de la fila para cifrarlo.
4- Guarda el grupo: Al terminar, hacer clic en Save (Guardar)

## Flujo

1- Instala herramientas (Helm, kubectl)
2- Autentica con AKS
3- Crea namespace y secrets TLS
4- Genera values.yaml dinámico
5- Despliega chart Helm de Blockscout
6- Configura Ingress con routing específico (/api, /)

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
    - Elegir la ruta / Path: /pipelines/azure-pipeline-Deploy_Blockscout.yml

7- En Previsualizar: Se mostrara el contenideo del archivo.yml y en esta ventana se peude crear las variables.

8- En el icono de **Ejecutar / Run**: Se puede seleccionar Salvar o Ejecutar. importante Salvar.

## Seguridad

- No almacena credenciales en variables de pipeline
- Usa OIDC con tokens federados
- Estado en storage seguro

## Enlaces de Interes

- OIDC: <https://learn.microsoft.com/en-us/samples/azure-samples/azure-devops-terraform-oidc-ci-cd/azure-devops-terraform-oidc-ci-cd/>
- Grupo de Variables: <https://learn.microsoft.com/es-es/cli/azure/pipelines/variable-group?view=azure-cli-latest>
