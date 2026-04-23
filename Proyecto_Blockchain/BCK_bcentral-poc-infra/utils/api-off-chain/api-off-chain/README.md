# API Off-Chain

Este proyecto contiene la implementación de una API off-chain definida en OpenAPI, diseñada para exponer datos complementarios de la blockchain a sistemas internos y externos de forma estandarizada y fácilmente integrable.

## Estructura del Proyecto

El proyecto está organizado de la siguiente manera:

- **specs/offchain-api.yaml**: Define la especificación OpenAPI para la API off-chain, incluyendo las rutas y esquemas necesarios.
- **clients/typescript/**: Contiene el cliente stub generado en TypeScript para interactuar con la API.
- **clients/go/**: Contiene el cliente stub generado en Go para interactuar con la API.
- **examples/**: Incluye ejemplos de peticiones y respuestas para facilitar la comprensión de la API.
- **scripts/**: Contiene scripts útiles para validar la especificación y generar los clientes.
- **package.json**: Configuración principal del proyecto, incluyendo dependencias y scripts.
- **README.md**: Documentación de este proyecto.

## Instalación

Para instalar las dependencias del proyecto, navega al directorio `api-offchain` y ejecuta:

```bash
npm install
```

## Validación de la Especificación

Para validar la especificación OpenAPI, puedes utilizar el siguiente script:

```bash
bash scripts/validate.sh
```

Asegúrate de que no haya errores en la validación.

## Generación de Clientes

Para generar los clientes stubs en TypeScript y Go, utiliza el siguiente script:

```bash
bash scripts/generate-clients.sh
```

Esto generará el código necesario en los directorios correspondientes.

## Ejemplos de Uso

Los ejemplos de peticiones y respuestas se encuentran en el directorio `examples`. 
Puedes revisar los archivos `sample-requests.json` y `sample-responses.json` para ver cómo estructurar tus solicitudes y qué respuestas esperar.