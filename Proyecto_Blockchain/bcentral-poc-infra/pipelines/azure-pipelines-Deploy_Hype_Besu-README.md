# Azure Pipelines / Despliegue Hyperledger Besu

Pipeline de Azure DevOps para el despliegue automatizado de una red blockchain Hyperledger Besu en un clúster de Azure Kubernetes Service (AKS). El pipeline implementa una arquitectura completa que incluye nodos validadores, nodos transaccionales y componentes auxiliares necesarios para el funcionamiento de la red..

## Documentación Técnica

### Funcionalidad

- Despliega red blockchain Besu con arquitectura multi-nodo
- Configura nodos validadores (4) y peers (3)
- Instala Ambassador Edge Stack para API gateway
- Gestiona secrets y storage classes
- Configura monitoreo con ServiceMonitors

### Ubicacion

en el repositorio bcentral-poc-infra crear un directorio **pipelines**

En Repositorio:
*bcentral-poc-infra\pipelines*

### Tecnologías

- Blockchain: Hyperledger Besu
- Orquestación: Kubernetes (AKS)
- Herramientas: Helm 3.14.0, kubectl, Azure CLI
- API Gateway: Ambassador Edge Stack (Emissary)
- Monitoreo: Prometheus ServiceMonitors
- Storage: Kubernetes StorageClasses

### Configuración Clave

- Variables en grupo: Besu-Deploy-Vars, FRONTEND-GROUP
- Namespace fijo: bcentral-testnet
- Arquitectura: Genesis + 4 Validators + 3 Tx Nodes
- Configuración proxy-and-vault para seguridad

## Grupo de Variables

Crear un Grupo de variables en Azure pipeline con

- Variable group name: **Besu-Deploy-Vars**

- Variables:

|Nombre|valor|🔒|
|--|--|--|
|kubernetesServiceEndpoint|Nombre del cluster en aks| 🔓 Variable (Candado Abierto)|
|NAMESPACE|bcentral-testnet|🔓 Variable (Candado Abierto)|
|ROOT_TOKEN|Token de autenticaion root en VAULT|🔒 Variable Secreta (candado cerrado)|

### Procedimiento

1- Navegar a la Biblioteca: En el de Azure DevOps, seleccionar Pipelines > Library (Biblioteca) en el menú de la izquierda.

2- Crear un nuevo grupo: Hacer clic en + Variable group (+ Grupo de variables).

3- Configura las propiedades:

    - Ingresar un Nombre para el grupo (nombre: **Besu-Deploy-Vars**).
    - Añadir una Descripción (opcional).
    - Añadir variables:
        - En la sección Variables, hacer clic en + Add (+ Agregar).
        - Introducir el Nombre y el Valor de la variable.
        - Para un secreto (como contraseñas), hacer clic en el ícono de candado al final de la fila para cifrarlo.
4- Guarda el grupo: Al terminar, hacer clic en Save (Guardar)

## Flujo

1- Instala herramientas y autentica con AKS
2- Crea namespaces (bcentral-testnet, emissary-system)
3- Instala CRDs de Ambassador
4- Aplica manifiestos de acceso y storage
5- Crea secret roottoken
6- Despliega nodos en orden:

    - Genesis (nodo inicial)
    - Validadores 1-4
    - Peers 1-3
7- Configura ConfigMap de nodos en la red. 

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
    - Elegir la ruta / Path: /pipelines/azure-pipeline-Deploy_Hype_Besu.yml

7- En Previsualizar: Se mostrara el contenideo del archivo.yml y en esta ventana se peude crear las variables.

8- En el icono de **Ejecutar / Run**: Se puede seleccionar Salvar o Ejecutar. importante Salvar.

## Seguridad

- No almacena credenciales en variables de pipeline
- Usa OIDC con tokens federados
- Estado en storage seguro
- Token VAULT protegido como variable secreta

## Enlaces de Interes

- OIDC: <https://learn.microsoft.com/en-us/samples/azure-samples/azure-devops-terraform-oidc-ci-cd/azure-devops-terraform-oidc-ci-cd/>
- Grupo de Variables: <https://learn.microsoft.com/es-es/cli/azure/pipelines/variable-group?view=azure-cli-latest>
