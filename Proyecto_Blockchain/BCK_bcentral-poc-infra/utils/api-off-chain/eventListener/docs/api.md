# Documentación del API Off-Chain

## Introducción

Este documento describe el API off-chain que se utiliza para almacenar eventos generados por la blockchain. 
El API permite la persistencia de datos y la trazabilidad de eventos importantes como Transferencias y Aprobaciones.

## Endpoints

### 1. POST /offchain/events

Este endpoint se utiliza para recibir eventos desde el servicio de event listeners.

#### Request

- **Headers**:
  - Content-Type: application/json

- **Body**:
```json
{
  "eventName": "string",
  "contractAddress": "string",
  "transactionHash": "string",
  "timestamp": "string",
  "payload": "object"
}
```

#### Ejemplo de Request

```json
{
  "eventName": "Transfer",
  "contractAddress": "0x1234567890abcdef1234567890abcdef12345678",
  "transactionHash": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef",
  "timestamp": "2023-10-01T12:00:00Z",
  "payload": {
    "from": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef",
    "to": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcdef",
    "value": "100"
  }
}
```

#### Response

- **Código de éxito**: 200 OK
- **Body**:
```json
{
  "status": "success",
  "message": "Evento almacenado correctamente"
}
```

- **Código de error**: 500 Internal Server Error
- **Body**:
```json
{
  "status": "error",
  "message": "Error al almacenar el evento"
}
```

## Manejo de Errores

El API implementa un manejo de errores robusto. En caso de errores 5xx, el servicio de event listeners intentará reintentar la solicitud hasta 3 veces con un back-off exponencial.

## Logs

Cada solicitud exitosa y fallida se registra en formato JSON, permitiendo un seguimiento detallado de las interacciones con el API.

## Conclusión

Este API es fundamental para la integración de datos entre la blockchain y sistemas externos, asegurando que la información crítica se almacene de manera confiable y esté disponible para su consulta.