# Documentación API Off-Chain

## Introducción

Esta documentación describe la API Off-Chain definida en el archivo `offchain-api.yaml`. 
La API permite acceder a información complementaria relacionada con la blockchain de manera estandarizada y fácilmente integrable.

## Endpoints

### 1. Obtener Metadata de Contratos

- **Ruta:** `GET /offchain/contracts/{contractId}/metadata`
- **Descripción:** Recupera la metadata asociada a un contrato inteligente específico.
- **Parámetros:**
  - `contractId` (path, obligatorio): ID del contrato inteligente.
  - Filtros opcionales pueden ser añadidos a través de parámetros de consulta.

- **Ejemplo de Petición:**
  ```
  GET /offchain/contracts/12345/metadata
  ```

- **Ejemplo de Respuesta:**
  ```json
  {
    "name": "Contrato Ejemplo",
    "version": "1.0",
    "parameters": {
      "param1": "valor1",
      "param2": "valor2"
    }
  }
  ```

### 2. Obtener Detalles de Transacciones

- **Ruta:** `GET /offchain/transactions/{txHash}/details`
- **Descripción:** Recupera detalles extendidos de una transacción específica.
- **Parámetros:**
  - `txHash` (path, obligatorio): Hash de la transacción.
  - Filtros opcionales pueden ser añadidos a través de parámetros de consulta.

- **Ejemplo de Petición:**
  ```
  GET /offchain/transactions/abc123/details
  ```

- **Ejemplo de Respuesta:**
  ```json
  {
    "transactionHash": "abc123",
    "businessData": {
      "field1": "value1",
      "field2": "value2"
    },
    "multiSignature": true
  }
  ```

### 3. Obtener Precios de Activos

- **Ruta:** `GET /offchain/prices/{asset}`
- **Descripción:** Recupera el precio o valor referencial de un activo específico.
- **Parámetros:**
  - `asset` (path, obligatorio): Nombre del activo.
  - Filtros opcionales pueden ser añadidos a través de parámetros de consulta.

- **Ejemplo de Petición:**
  ```
  GET /offchain/prices/bitcoin
  ```

- **Ejemplo de Respuesta:**
  ```json
  {
    "asset": "bitcoin",
    "price": 45000,
    "currency": "USD"
  }
  ```

## Validación

La especificación OpenAPI puede ser validada utilizando herramientas como Swagger Editor o `swagger-cli`. Asegúrese de que el archivo `offchain-api.yaml` no contenga errores antes de proceder con la implementación.

## Generación de Clientes

Se pueden generar clientes stubs en TypeScript y Go utilizando el script `generate-clients.sh`. Asegúrese de tener las dependencias necesarias instaladas y siga las instrucciones en el archivo `README.md` del directorio `api-offchain`.

## Conclusión

Esta API Off-Chain proporciona una forma estandarizada de acceder a información relevante de la blockchain, facilitando la integración con sistemas internos y externos. 
Para más detalles, consulte el archivo `offchain-api.yaml` y los ejemplos proporcionados en el directorio `examples`.