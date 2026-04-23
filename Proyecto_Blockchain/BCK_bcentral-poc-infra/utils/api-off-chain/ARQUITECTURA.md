# Documento de Arquitectura - Sistema de Escucha y Persistencia de Eventos Blockchain (SEPEB)



## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Propósito del Desarrollo](#2-propósito-del-desarrollo)
3. [Componentes del Sistema](#3-componentes-del-sistema)
4. [Arquitectura del Sistema](#4-arquitectura-del-sistema)
5. [Interacciones Entre Componentes](#5-interacciones-entre-componentes)
6. [Flujos de Información](#6-flujos-de-información)
7. [Tecnologías Utilizadas](#7-tecnologías-utilizadas)
8. [Casos de Uso para Instituciones Bancarias](#8-casos-de-uso-para-instituciones-bancarias)
9. [Consideraciones de Seguridad](#9-consideraciones-de-seguridad)
10. [Escalabilidad y Resiliencia](#10-escalabilidad-y-resiliencia)

---

## 1. Resumen Ejecutivo

El proyecto SEPEB implementa un sistema integral para la captura, procesamiento y persistencia de eventos generados en una blockchain empresarial. El sistema consta de tres componentes principales que trabajan en conjunto para garantizar la trazabilidad completa de las operaciones blockchain en una base de datos off-chain.

**Objetivo Principal:** Proporcionar al Banco Central una solución robusta que permita mantener un registro auditable y consultable de todas las transacciones y eventos blockchain, complementando la inmutabilidad de la cadena con capacidades de consulta SQL avanzadas y análisis de datos.

---

## 2. Propósito del Desarrollo

### 2.1 Contexto Institucional

Las instituciones financieras que adoptan tecnología blockchain enfrentan el desafío de integrar sistemas descentralizados con infraestructura tradicional. Si bien la blockchain ofrece inmutabilidad y descentralización, presenta limitaciones en:

- **Consultas complejas**: Las consultas en blockchain son costosas y lentas
- **Análisis histórico**: El acceso a datos históricos requiere recorrer toda la cadena
- **Integración con sistemas legacy**: Los sistemas tradicionales no pueden consultar directamente la blockchain
- **Reportería regulatoria**: Los reguladores requieren reportes en formatos tradicionales (SQL, CSV, Excel)
- **Auditoría**: Los auditores necesitan acceso rápido a información histórica consolidada

### 2.2 Solución Propuesta

El sistema SEPEB resuelve estos desafíos mediante:

1. **Escucha en tiempo real** de eventos blockchain
2. **Persistencia automática** en base de datos relacional
3. **API REST** para consultas y análisis
4. **Trazabilidad completa** de cada transacción
5. **Resiliencia** mediante reintentos automáticos

---

## 3. Componentes del Sistema

### 3.1 Smart Contract (ERC20Mock)

**Descripción:**  
Implementa un contrato inteligente estándar ERC-20 que representa un token digital. Este contrato genera eventos que son capturados por el sistema.

**Responsabilidades:**

- Gestión de tokens (transferencias, aprobaciones)
- Emisión de eventos blockchain (Transfer, Approval)
- Aplicación de reglas de negocio on-chain

**Eventos Emitidos:**

- `Transfer(address indexed from, address indexed to, uint256 value)`: Emitido en cada transferencia de tokens
- `Approval(address indexed owner, address indexed spender, uint256 value)`: Emitido cuando se otorga permiso de gasto

**Características Técnicas:**

- Lenguaje: Solidity
- Estándar: ERC-20
- Desplegable en: Hyperledger Besu, Ethereum, redes privadas

---

### 3.2 Event Listener Service

**Ubicación:** `eventListener/`

**Descripción:**  
Servicio Node.js que establece conexiones WebSocket con la blockchain para escuchar eventos en tiempo real y reenviarlos al API off-chain.

#### 3.2.1 Submódulos Principales

##### EventListener (`eventListener/src/services/eventListener.ts`)

**Responsabilidades:**

- Establecer conexión WebSocket con el nodo blockchain
- Suscribirse a eventos específicos de contratos
- Capturar eventos en tiempo real
- Transformar datos blockchain a formato JSON serializable
- Invocar el ApiClient para persistir eventos

**Funcionalidades clave:**

- Conversión de BigInt a String (para serialización JSON)
- Manejo de múltiples contratos y eventos simultáneos
- Procesamiento asíncrono de eventos

##### ApiClient (`eventListener/src/services/apiClient.ts`)

**Responsabilidades:**

- Gestionar comunicación HTTP con el API off-chain
- Enviar eventos capturados mediante POST
- Medir tiempos de respuesta
- Propagar errores para manejo de reintentos

**Características:**

- Cliente HTTP basado en Axios
- Timeout configurable (5 segundos)
- Logging de métricas de rendimiento

##### RetryService (`eventListener/src/services/retryService.ts`)

**Responsabilidades:**

- Implementar lógica de reintentos con backoff exponencial
- Manejar fallos temporales de red o API
- Registrar intentos fallidos

**Estrategia de reintentos:**

- Reintentos: Hasta 3 intentos (configurable)
- Backoff: Exponencial con base 2 (2^intento segundos)
- Condiciones de reintento: Errores 5xx, timeouts, errores de red

##### Logger (`eventListener/src/utils/logger.ts`)

**Responsabilidades:**

- Generar logs estructurados en formato JSON
- Registrar eventos exitosos y fallidos
- Facilitar auditoría y troubleshooting

**Información registrada:**

- Status (sent, error, initialized)
- EventId, transactionHash
- ResponseTimeMs
- Mensajes de error detallados

##### HealthController (`eventListener/src/controllers/healthController.ts`)

**Responsabilidades:**

- Exponer endpoint `/health` para monitoreo
- Validar conectividad con blockchain y API
- Proveer métricas de disponibilidad

---

### 3.3 Off-Chain API

**Ubicación:** `api-off-chain/`

**Descripción:**  
API REST en Node.js/TypeScript que recibe eventos del Event Listener y los persiste en una base de datos relacional, proporcionando endpoints para consultas avanzadas.

#### 3.3.1 Submódulos Principales

##### EventController (`api-off-chain/src/controllers/eventController.ts`)

**Responsabilidades:**

- Recibir peticiones HTTP POST con eventos
- Validar payload de entrada
- Invocar servicios de negocio
- Retornar respuestas HTTP apropiadas

**Endpoints principales:**

- `POST /api/events`: Crear nuevo evento
- `GET /api/events/:id`: Obtener evento por ID
- `PUT /api/events/:id`: Actualizar evento
- `DELETE /api/events/:id`: Eliminar evento
- `GET /api/events`: Listar eventos con filtros

##### EventService (`api-off-chain/src/services/eventService.ts`)

**Responsabilidades:**

- Implementar lógica de negocio
- Orquestar operaciones entre múltiples repositorios
- Validar reglas de negocio
- Enriquecer datos de eventos

**Operaciones:**

- Validación de datos de entrada
- Normalización de addresses
- Cálculo de métricas derivadas
- Coordinación de transacciones

##### EventRepository (`api-off-chain/src/repositories/eventRepository.ts`)

**Responsabilidades:**

- Abstracción de acceso a datos
- Ejecutar operaciones CRUD en base de datos
- Mapear objetos de dominio a entidades de BD

##### ContractMetadataRepository (`api-off-chain/src/repositories/contractMetadataRepository.ts`)

**Responsabilidades:**

- Gestionar metadata de contratos
- Almacenar ABIs y configuraciones
- Proveer información contextual de contratos

##### TransactionRepository (`api-off-chain/src/repositories/transactionRepository.ts`)

**Responsabilidades:**

- Gestionar información de transacciones
- Almacenar hashes, blocks, timestamps
- Facilitar auditoría de transacciones

##### PriceReferenceRepository (`api-off-chain/src/repositories/priceReferenceRepository.ts`)

**Responsabilidades:**

- Gestionar precios de referencia (caso bancario: tasas de cambio)
- Permitir valoración de transacciones
- Mantener histórico de precios

##### Database (`api-off-chain/src/database/database.ts`)

**Responsabilidades:**

- Gestionar pool de conexiones
- Implementar patrón Singleton
- Proveer transacciones ACID

##### ErrorHandler Middleware (`api-off-chain/src/middleware/errorHandler.ts`)

**Responsabilidades:**

- Capturar errores globales
- Formatear respuestas de error consistentes
- Registrar errores para análisis

##### Validation Middleware (`api-off-chain/src/middleware/validation.ts`)

**Responsabilidades:**

- Validar schemas de entrada
- Sanitizar datos
- Prevenir inyecciones

---

## 4. Arquitectura del Sistema

### 4.1 Diagrama de Arquitectura

```
┌────────────────────────────────────────────────────────────────────────┐
│                         BLOCKCHAIN LAYER                               │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    Hyperledger Besu Node                          │ │
│  │  ┌────────────────────┐  ┌────────────────────┐                   │ │
│  │  │  Smart Contract 1  │  │  Smart Contract 2  │  ...              │ │
│  │  │   (ERC20Mock)      │  │   (ERC20Mock)      │                   │ │
│  │  └────────────────────┘  └────────────────────┘                   │ │
│  │           │ Events              │ Events                          │ │
│  └───────────┼─────────────────────┼─────────────────────────────────┘ │
└──────────────┼─────────────────────┼───────────────────────────────────┘
               │                     │
               │  WebSocket/RPC      │
               ▼                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    EVENT LISTENER SERVICE LAYER                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     Event Listener Service                       │  │
│  │  ┌────────────────┐  ┌──────────────┐  ┌───────────────────┐     │  │
│  │  │ EventListener  │→→│ RetryService │→→│   ApiClient       │     │  │
│  │  │   (Web3.js)    │  │ (Backoff)    │  │   (Axios)         │     │  │
│  │  └────────────────┘  └──────────────┘  └───────────────────┘     │  │
│  │          │                                      │                │  │
│  │          ▼                                      │                │  │
│  │  ┌────────────────┐                             │                │  │
│  │  │     Logger     │                             │                │  │
│  │  └────────────────┘                             │                │  │
│  │                                                 │                │  │
│  │  ┌──────────────────────────────────────────────┘                │  │
│  │  │ Health Check Endpoint: GET /health           │                │  │
│  │  └──────────────────────────────────────────────┘                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │
                               │  HTTP POST
                               │  /api/events
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        OFF-CHAIN API LAYER                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      Off-Chain API Service                        │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │                    API Routes                               │  │  │
│  │  │  POST /api/events  │  GET /api/events/:id  │  GET /health   │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                    │  │
│  │                              ▼                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │              Middleware Layer                               │  │  │
│  │  │  ┌────────────┐  ┌────────────┐  ┌──────────────────┐       │  │  │
│  │  │  │ Validation │  │   Logger   │  │  Error Handler   │       │  │  │
│  │  │  └────────────┘  └────────────┘  └──────────────────┘       │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                    │  │
│  │                              ▼                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │                    Controllers                              │  │  │
│  │  │               EventController                               │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                    │  │
│  │                              ▼                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │                    Services                                 │  │  │
│  │  │               EventService                                  │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                    │  │
│  │                              ▼                                    │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │                  Repositories                               │  │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────────┐  │  │  │
│  │  │  │  Event   │ │ Contract │ │Transaction│ │PriceReference │  │  │  │
│  │  │  │Repository│ │Repository│ │Repository │ │  Repository   │  │  │  │
│  │  │  └──────────┘ └──────────┘ └───────────┘ └───────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               │  SQL Queries
                               ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA PERSISTENCE LAYER                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                  Relational Database (SQLite/PostgreSQL)         │  │
│  │  ┌──────────────┐  ┌───────────────┐  ┌────────────────────┐     │  │
│  │  │   events     │  │contract_meta  │  │  transactions      │     │  │
│  │  │  (Table)     │  │   (Table)     │  │     (Table)        │     │  │
│  │  └──────────────┘  └───────────────┘  └────────────────────┘     │  │
│  │  ┌──────────────┐                                                │  │
│  │  │price_refs    │                                                │  │
│  │  │  (Table)     │                                                │  │
│  │  └──────────────┘                                                │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
                               ▲
                               │
                               │  SQL Queries
                               │
┌────────────────────────────────────────────────────────────────────────┐
│                      REPORTING & ANALYTICS LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │  BI Tools    │  │  Dashboards  │  │ Audit Tools  │                  │
│  │ (Tableau,    │  │  (Grafana,   │  │              │                  │
│  │  PowerBI)    │  │  Custom)     │  │              │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Arquitectura de Capas

El sistema sigue una arquitectura de capas bien definida:

1. **Blockchain Layer**: Capa de contratos inteligentes y blockchain
2. **Event Listener Service Layer**: Capa de captura de eventos en tiempo real
3. **Off-Chain API Layer**: Capa de servicios REST y lógica de negocio
4. **Data Persistence Layer**: Capa de almacenamiento persistente
5. **Reporting & Analytics Layer**: Capa de análisis y reportería

---

## 5. Interacciones Entre Componentes

### 5.1 Flujo Principal: Captura de Evento

```
┌─────────────────┐
│ Smart Contract  │
│   (ERC20Mock)   │
└────────┬────────┘
         │
         │ 1. Emite evento Transfer/Approval
         ▼
┌─────────────────┐
│  Blockchain     │
│    (Besu)       │
└────────┬────────┘
         │
         │ 2. Propaga evento via WebSocket
         ▼
┌─────────────────┐
│ EventListener   │
│  startListening │
└────────┬────────┘
         │
         │ 3. Captura evento y lo procesa
         ▼
┌─────────────────┐
│ EventListener   │
│  handleEvent    │
└────────┬────────┘
         │
         │ 4. Serializa BigInt a String
         ▼
┌─────────────────┐
│ RetryService    │
│executeWithRetry │
└────────┬────────┘
         │
         │ 5. Intenta enviar con lógica de reintentos
         ▼
┌─────────────────┐
│   ApiClient     │
│   postEvent     │
└────────┬────────┘
         │
         │ 6. HTTP POST /api/events
         ▼
┌─────────────────┐
│ Off-Chain API   │
│  Middleware     │
└────────┬────────┘
         │
         │ 7. Valida y registra petición
         ▼
┌─────────────────┐
│EventController  │
│  createEvent    │
└────────┬────────┘
         │
         │ 8. Delega a servicio de negocio
         ▼
┌─────────────────┐
│ EventService    │
│  createEvent    │
└────────┬────────┘
         │
         │ 9. Valida y enriquece datos
         ▼
┌─────────────────┐
│EventRepository  │
│     save        │
└────────┬────────┘
         │
         │ 10. Persiste en BD
         ▼
┌─────────────────┐
│    Database     │
│  (events table) │
└─────────────────┘
```

### 5.2 Interacción con Múltiples Repositorios

El EventService coordina operaciones con múltiples repositorios:

```
EventService
    │
    ├─→ EventRepository (almacena evento principal)
    │
    ├─→ ContractMetadataRepository (obtiene metadata del contrato)
    │
    ├─→ TransactionRepository (registra transacción asociada)
    │
    └─→ PriceReferenceRepository (obtiene precio de referencia si aplica)
```

### 5.3 Flujo de Reintentos

```
ApiClient.postEvent()
    │
    │ (intento 1) → Fallo 503
    ▼
RetryService
    │
    │ Espera 2^1 = 2 segundos
    │ (intento 2) → Fallo timeout
    ▼
RetryService
    │
    │ Espera 2^2 = 4 segundos
    │ (intento 3) → Éxito 201
    ▼
Logger.log({ status: 'sent' })
```

### 5.4 Patrón de Comunicación

El sistema implementa varios patrones:

1. **Event-Driven**: Blockchain → Event Listener (basado en eventos)
2. **Request-Response**: Event Listener → Off-Chain API (HTTP REST)
3. **Repository Pattern**: Off-Chain API → Database (abstracción de datos)
4. **Retry Pattern**: RetryService (resiliencia)
5. **Singleton Pattern**: Database Connection Pool

---

## 6. Flujos de Información

### 6.1 Formato de Evento Capturado

```typescript
// Evento emitido por Smart Contract
Transfer Event {
  event: "Transfer",
  address: "0x37cDc84e510a0221f01e12E76Ae7902eBe61f627",
  blockNumber: 1234567,
  transactionHash: "0xabc123...",
  returnValues: {
    from: "0x123...",
    to: "0x456...",
    value: "1000000000000000000" // 1 ETH en Wei
  }
}
```

### 6.2 Formato de Payload HTTP

```json
// Enviado por Event Listener a Off-Chain API
POST /api/events
{
  "eventId": "Transfer",
  "blockNumber": "1234567",
  "transactionHash": "0xabc123...",
  "address": "0x37cDc84e510a0221f01e12E76Ae7902eBe61f627",
  "returnValues": {
    "from": "0x123...",
    "to": "0x456...",
    "value": "1000000000000000000"
  }
}
```

### 6.3 Estructura de Datos Persistida

```sql
-- Tabla events
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id VARCHAR(255),
    block_number BIGINT,
    transaction_hash VARCHAR(66),
    contract_address VARCHAR(42),
    from_address VARCHAR(42),
    to_address VARCHAR(42),
    value VARCHAR(255),
    timestamp BIGINT,
    raw_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla contract_metadata
CREATE TABLE contract_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_address VARCHAR(42) UNIQUE,
    contract_name VARCHAR(255),
    abi TEXT,
    deployment_block BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla transactions
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_hash VARCHAR(66) UNIQUE,
    block_number BIGINT,
    from_address VARCHAR(42),
    to_address VARCHAR(42),
    gas_used BIGINT,
    gas_price BIGINT,
    timestamp BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla price_references
CREATE TABLE price_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_code VARCHAR(10),
    price_usd DECIMAL(18, 8),
    effective_date DATE,
    source VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. Tecnologías Utilizadas

### 7.1 Stack Tecnológico

| Capa | Tecnología | Versión | Propósito |
|------|------------|---------|-----------|
| **Blockchain** | Hyperledger Besu | Latest | Blockchain empresarial |
| | Solidity | 0.8.x | Desarrollo de Smart Contracts |
| **Event Listener** | Node.js | 18+ | Runtime JavaScript |
| | TypeScript | 5.x | Tipado estático |
| | Web3.js | 4.x | Interacción con blockchain |
| | Axios | 1.x | Cliente HTTP |
| | Express | 4.x | Servidor HTTP |
| **Off-Chain API** | Node.js | 18+ | Runtime JavaScript |
| | TypeScript | 5.x | Tipado estático |
| | Express | 4.x | Framework web |
| | SQLite/PostgreSQL | Latest | Base de datos relacional |
| **Testing** | Jest | 29.x | Framework de testing |
| | Supertest | 6.x | Testing de APIs |
| **DevOps** | Docker | Latest | Containerización |
| | Docker Compose | Latest | Orquestación local |

### 7.2 Librerías Clave

**Event Listener Service:**

- `web3`: Conexión y escucha de eventos blockchain
- `axios`: Cliente HTTP para comunicación con API
- `express`: Servidor para health checks
- `winston`: Logging estructurado
- `dotenv`: Gestión de configuración

**Off-Chain API:**

- `express`: Framework web REST
- `sqlite3/pg`: Driver de base de datos
- `joi`: Validación de schemas
- `helmet`: Seguridad HTTP
- `cors`: Control de acceso CORS
- `morgan`: Logging de peticiones HTTP

---

## 8. Casos de Uso para Instituciones Bancarias

### 8.1 Caso de Uso 1: Sistema de Pagos Interbancarios

**Contexto:**  
Un banco central implementa un sistema de pagos en tiempo real entre bancos comerciales usando blockchain.

**Aplicación del Sistema:**

1. **Smart Contract**: Implementa un token digital que representa dinero del banco central (CBDC - Central Bank Digital Currency)

2. **Eventos Capturados**:
   - `Transfer`: Cada vez que un banco transfiere fondos a otro banco
   - `Approval`: Cuando un banco autoriza a otro para realizar operaciones en su nombre

3. **Persistencia Off-Chain**:
   - Registro de todas las transacciones para cumplimiento regulatorio
   - Base de datos permite queries complejas: "¿Cuánto transfirió el Banco A al Banco B en el último trimestre?"
   - Generación de reportes diarios de liquidación

4. **Beneficios**:
   - **Trazabilidad**: Auditoría completa de movimientos
   - **Reportería**: Generación automática de reportes para reguladores
   - **Conciliación**: Identificación rápida de discrepancias
   - **Analytics**: Análisis de patrones de flujo de dinero

**Ejemplo de Transacción:**

```
Evento Blockchain:
Transfer(
  from: 0xBancoA...,
  to: 0xBancoB...,
  value: 10000000 // $10M en representación digital
)

Registro Off-Chain:
- ID: TXN-2025-12-26-001
- Banco Origen: Banco Comercial A
- Banco Destino: Banco Comercial B
- Monto: $10,000,000 USD
- Timestamp: 2025-12-26 14:35:22
- Block: 1234567
- TxHash: 0xabc123...
- Estado: Confirmado
```

### 8.2 Caso de Uso 2: Registro de Garantías (Collateral Management)

**Contexto:**  
Un sistema de registro de garantías mobiliarias sobre blockchain para préstamos comerciales.

**Aplicación del Sistema:**

1. **Smart Contract**: Representa certificados de depósito, bonos, o acciones usadas como garantía

2. **Eventos Capturados**:
   - `CollateralPledged`: Cuando se registra una garantía
   - `CollateralReleased`: Cuando se libera una garantía
   - `CollateralValuationUpdate`: Actualización de valor de garantía

3. **Persistencia Off-Chain**:
   - Histórico completo de garantías por cliente
   - Valoración histórica de garantías
   - Alertas cuando el valor de garantía cae bajo umbral

4. **Integración con PriceReferenceRepository**:
   - Almacena precios históricos de activos
   - Permite valoración automática de garantías
   - Genera alertas de márgenes insuficientes

**Ejemplo de Flujo:**

```
1. Empresa XYZ constituye garantía por $5M en bonos
   → Evento: CollateralPledged
   → Off-Chain DB: Registra garantía con valoración inicial

2. Sistema diario revalúa garantía usando precios de mercado
   → PriceReferenceRepository consulta precio actual bonos
   → Valoración cae a $4.5M
   → Sistema genera alerta: Margin Call requerido

3. Empresa aporta garantía adicional
   → Evento: CollateralPledged (adicional)
   → Off-Chain DB: Actualiza posición total

4. Préstamo liquidado, garantía liberada
   → Evento: CollateralReleased
   → Off-Chain DB: Cierra registro de garantía
```

### 8.3 Caso de Uso 3: Know Your Transaction (KYT) - Monitoreo Anti-Lavado

**Contexto:**  
Cumplimiento normativo AML/CFT (Anti-Money Laundering / Combating the Financing of Terrorism).

**Aplicación del Sistema:**

1. **Smart Contract**: Tokens que representan activos financieros

2. **Eventos Capturados**:
   - Todos los `Transfer` events son capturados

3. **Persistencia Off-Chain**:
   - Base de datos permite análisis de patrones
   - Identificación de transacciones sospechosas
   - Generación de reportes SAR (Suspicious Activity Reports)

4. **Análisis Implementables**:

   ```sql
   -- Detectar Smurfing (múltiples transacciones pequeñas)
   SELECT from_address, COUNT(*) as tx_count, SUM(CAST(value AS DECIMAL)) as total
   FROM events
   WHERE event_id = 'Transfer'
     AND timestamp > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
   GROUP BY from_address
   HAVING COUNT(*) > 10 AND SUM(CAST(value AS DECIMAL)) > 50000;

   -- Detectar Round-tripping (fondos que vuelven al origen)
   SELECT e1.from_address, e2.to_address, e1.value
   FROM events e1
   JOIN events e2 ON e1.from_address = e2.to_address 
                  AND e1.to_address = e2.from_address
   WHERE e2.timestamp > e1.timestamp 
     AND e2.timestamp < (e1.timestamp + INTERVAL '1 hour')
     AND ABS(CAST(e1.value AS DECIMAL) - CAST(e2.value AS DECIMAL)) < 100;
   ```

5. **Beneficios**:
   - **Compliance**: Cumplimiento automático de regulaciones
   - **Trazabilidad**: Reconstrucción de flujos de fondos
   - **Alertas Tempranas**: Detección proactiva de patrones sospechosos
   - **Auditoría**: Evidencia para reguladores

### 8.4 Caso de Uso 4: Liquidación de Valores (Securities Settlement)

**Contexto:**  
Cámara de compensación para valores digitalizados (bonos, acciones).

**Aplicación del Sistema:**

1. **Smart Contracts**: Representan bonos del tesoro o acciones tokenizadas

2. **Eventos Capturados**:
   - `TradeExecuted`: Cuando se ejecuta una operación
   - `SettlementInitiated`: Inicio del proceso de liquidación
   - `SettlementCompleted`: Liquidación completada (DVP - Delivery vs Payment)

3. **Persistencia Off-Chain**:
   - Registro de todas las operaciones para clearing
   - Cálculo de posiciones netas
   - Reportes T+0, T+1, T+2

4. **Flujo Operativo**:

```
   Day 1 (Trade Date):
   → Multiple Trades: TradeExecuted events
   → Off-Chain: Agregación de operaciones

   Day 1 EOD:
   → Netting Calculation (query off-chain DB)
   → Generate Settlement Instructions

   Day 2 (Settlement Date):
   → Blockchain: Execute settlements
   → Events: SettlementCompleted
   → Off-Chain: Update positions, generate confirmations
```

1. **Queries Críticos**:

   ```sql
   -- Posición neta por participante
   SELECT 
       participant_id,
       security_code,
       SUM(CASE WHEN side='BUY' THEN quantity ELSE -quantity END) as net_position,
       SUM(CASE WHEN side='BUY' THEN amount ELSE -amount END) as net_amount
   FROM events
   WHERE event_id = 'TradeExecuted'
     AND trade_date = '2025-12-26'
   GROUP BY participant_id, security_code;
   ```

### 8.5 Caso de Uso 5: Sistema de Trazabilidad de Remesas

**Contexto:**  
Red de transferencias internacionales entre corresponsales bancarios.

**Aplicación del Sistema:**

1. **Smart Contract**: Token stablecoin para transferencias internacionales

2. **Eventos Capturados**:
   - `RemittanceInitiated`: Inicio de remesa
   - `IntermediaryProcessed`: Procesado por banco intermediario
   - `RemittanceCompleted`: Entrega al beneficiario final

3. **Persistencia Off-Chain**:
   - Tracking end-to-end de remesas
   - Tiempos de procesamiento por cada hop
   - Comisiones cobradas en cada etapa

4. **Dashboard de Monitoreo**:
   - Estado en tiempo real de cada remesa
   - SLA tracking (¿se completó en <2 horas?)
   - Identificación de cuellos de botella

5. **Beneficios para Cliente Final**:

```
   Cliente consulta: "¿Dónde está mi remesa?"
   
   Sistema responde (query off-chain):
   Remesa ID: REM-2025-123456
   ├─ [✓] Enviada por Banco A (2025-12-26 10:00)
   ├─ [✓] Procesada por Banco Intermediario B (2025-12-26 10:15)
   ├─ [⏳] En proceso en Banco C (desde 10:45)
   └─ [ ] Pendiente entrega a beneficiario
   
   Tiempo estimado de entrega: 30 minutos
   ```

---

## 9. Consideraciones de Seguridad

### 9.1 Seguridad en Event Listener

**Autenticación y Autorización:**

- Validación de certificados SSL/TLS para conexiones WebSocket
- API keys para comunicación con Off-Chain API
- Tokens JWT para autenticación de servicios

**Protección de Datos Sensibles:**

- Variables de entorno para credenciales (nunca hardcoded)
- Encriptación de logs que contengan información sensible
- Rotación periódica de API keys

**Validación de Eventos:**

```typescript
// Validar que el evento proviene del contrato esperado
if (event.address.toLowerCase() !== expectedContract.toLowerCase()) {
    Logger.error({ status: 'security_violation', reason: 'unexpected_contract' });
    return;
}

// Validar estructura del evento
if (!event.transactionHash || !event.blockNumber) {
    Logger.error({ status: 'invalid_event', event });
    return;
}
```

### 9.2 Seguridad en Off-Chain API

**Middleware de Seguridad:**

```typescript
// helmet: Protección de headers HTTP
app.use(helmet());

// CORS: Control de orígenes permitidos
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS.split(','),
    methods: ['GET', 'POST'],
    credentials: true
}));

// Rate limiting: Prevenir abuso
app.use(rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutos
    max: 100 // límite de requests
}));
```

**Validación de Input:**

```typescript
// Sanitización de addresses
function sanitizeAddress(address: string): string {
    return address.toLowerCase().trim();
}

// Validación de transaction hash
function isValidTxHash(hash: string): boolean {
    return /^0x[a-fA-F0-9]{64}$/.test(hash);
}
```

**SQL Injection Prevention:**

- Uso de prepared statements
- ORM/Query builders
- Validación estricta de inputs

### 9.3 Seguridad de Base de Datos

**Cifrado:**

- Cifrado at-rest de base de datos (TDE - Transparent Data Encryption)
- Cifrado in-transit (SSL/TLS para conexiones)

**Backup y Recuperación:**

- Backups automáticos cada 6 horas
- Backup completo diario
- Retention de 30 días
- Testing periódico de restauración

**Acceso:**

- Principio de mínimo privilegio
- Auditoría de accesos a datos sensibles
- Segregación de ambientes (dev, staging, prod)

---

## 10. Escalabilidad y Resiliencia

### 10.1 Escalabilidad Horizontal

**Event Listener Service:**

- Múltiples instancias escuchando diferentes contratos
- Particionamiento por tipo de evento
- Load balancing para health checks

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Listener 1    │     │ Listener 2    │     │ Listener 3    │
│ Contracts A-C │     │ Contracts D-F │     │ Contracts G-I │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  Off-Chain API  │
                    │  (Load Balanced)│
                    └─────────────────┘
```

**Off-Chain API:**

- Múltiples instancias detrás de load balancer
- Stateless design (session en cache distribuido)
- Auto-scaling basado en CPU/memoria

### 10.2 Resiliencia

**Circuit Breaker Pattern:**

```typescript
class CircuitBreaker {
    private failureCount = 0;
    private readonly threshold = 5;
    private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
    
    async execute(fn: Function) {
        if (this.state === 'OPEN') {
            throw new Error('Circuit breaker is OPEN');
        }
        
        try {
            const result = await fn();
            this.onSuccess();
            return result;
        } catch (error) {
            this.onFailure();
            throw error;
        }
    }
    
    private onSuccess() {
        this.failureCount = 0;
        this.state = 'CLOSED';
    }
    
    private onFailure() {
        this.failureCount++;
        if (this.failureCount >= this.threshold) {
            this.state = 'OPEN';
            setTimeout(() => this.state = 'HALF_OPEN', 60000); // 1 min
        }
    }
}
```

**Message Queue (Opcional):**
Para mayor resiliencia, se puede interponer una cola de mensajes:

```
Event Listener → RabbitMQ/Kafka → Off-Chain API Workers
```

Beneficios:

- Desacoplamiento completo
- Buffer para picos de tráfico
- Garantía de entrega (at-least-once)
- Reintento automático

### 10.3 Monitoreo y Observabilidad

**Métricas Clave:**

```
Event Listener:
- events_captured_total (counter)
- events_processed_success (counter)
- events_processed_failed (counter)
- api_call_duration_seconds (histogram)
- retry_attempts_total (counter)

Off-Chain API:
- http_requests_total (counter)
- http_request_duration_seconds (histogram)
- database_query_duration_seconds (histogram)
- database_connections_active (gauge)
```

**Health Checks:**

```typescript
// Comprehensive health check
GET /health
Response:
{
    "status": "healthy",
    "timestamp": "2025-12-26T14:35:22Z",
    "checks": {
        "blockchain": {
            "status": "up",
            "latency_ms": 45
        },
        "database": {
            "status": "up",
            "latency_ms": 12,
            "connections": 5
        },
        "api_downstream": {
            "status": "up",
            "latency_ms": 120
        }
    },
    "version": "1.0.0"
}
```

**Alerting:**

- Prometheus + Grafana para métricas
- AlertManager para notificaciones
- PagerDuty para on-call

**Logging Centralizado:**

- ELK Stack (Elasticsearch, Logstash, Kibana)
- Structured logging (JSON)
- Correlation IDs para trazabilidad de requests

### 10.4 Disaster Recovery

**RTO/RPO:**

- RTO (Recovery Time Objective): < 1 hora
- RPO (Recovery Point Objective): < 5 minutos

**Estrategia:**

1. Base de datos con replicación asíncrona
2. Snapshots automáticos cada hora
3. Backups en región geográfica diferente
4. Playbooks de recuperación documentados y testeados

**Procedimiento de Failover:**

```
1. Detectar fallo (monitoring alerts)
2. Promover réplica de BD a primary
3. Actualizar DNS/Load Balancer
4. Reiniciar servicios en región secundaria
5. Validar integridad de datos
6. Notificar stakeholders
```

---

## Conclusión

El sistema SEPEB proporciona una solución integral y robusta para la captura, procesamiento y persistencia de eventos blockchain en instituciones financieras. La arquitectura de tres capas (Blockchain, Event Listener, Off-Chain API) permite:

1. **Trazabilidad completa** de todas las operaciones blockchain
2. **Consultas avanzadas** mediante SQL sobre datos blockchain
3. **Integración con sistemas legacy** a través de API REST
4. **Resiliencia operacional** mediante reintentos y circuit breakers
5. **Escalabilidad horizontal** para crecimiento futuro
6. **Cumplimiento regulatorio** con reportería automatizada

El sistema está diseñado para soportar casos de uso críticos en banca central y comercial, incluyendo sistemas de pagos, registro de garantías, monitoreo anti-lavado, liquidación de valores y trazabilidad de remesas.
