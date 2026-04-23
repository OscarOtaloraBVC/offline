# DefaultApi

All URIs are relative to *https://api.bancocentral.gov.cl/v1*

|Method | HTTP request | Description|
|------------- | ------------- | -------------|
|[**getAssetPrice**](#getassetprice) | **GET** /offchain/prices/{asset} | Obtener precio de un activo|
|[**getContractMetadata**](#getcontractmetadata) | **GET** /offchain/contracts/{contractId}/metadata | Obtener metadata de un contrato inteligente|
|[**getTransactionDetails**](#gettransactiondetails) | **GET** /offchain/transactions/{txHash}/details | Obtener detalles de una transacción|

# **getAssetPrice**
> PriceReference getAssetPrice()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

let asset: string; //Nombre del activo (default to undefined)
let fromDate: string; //Fecha de inicio para filtrar resultados (optional) (default to undefined)
let toDate: string; //Fecha de fin para filtrar resultados (optional) (default to undefined)

const { status, data } = await apiInstance.getAssetPrice(
    asset,
    fromDate,
    toDate
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **asset** | [**string**] | Nombre del activo | defaults to undefined|
| **fromDate** | [**string**] | Fecha de inicio para filtrar resultados | (optional) defaults to undefined|
| **toDate** | [**string**] | Fecha de fin para filtrar resultados | (optional) defaults to undefined|


### Return type

**PriceReference**

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Precio del activo |  -  |
|**404** | Activo no encontrado |  -  |
|**500** | Error interno del servidor |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getContractMetadata**
> ContractMetadata getContractMetadata()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

let contractId: string; //ID del contrato inteligente (default to undefined)
let fromDate: string; //Fecha de inicio para filtrar resultados (optional) (default to undefined)
let toDate: string; //Fecha de fin para filtrar resultados (optional) (default to undefined)

const { status, data } = await apiInstance.getContractMetadata(
    contractId,
    fromDate,
    toDate
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **contractId** | [**string**] | ID del contrato inteligente | defaults to undefined|
| **fromDate** | [**string**] | Fecha de inicio para filtrar resultados | (optional) defaults to undefined|
| **toDate** | [**string**] | Fecha de fin para filtrar resultados | (optional) defaults to undefined|


### Return type

**ContractMetadata**

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Metadata del contrato inteligente |  -  |
|**404** | Contrato no encontrado |  -  |
|**500** | Error interno del servidor |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getTransactionDetails**
> TransactionDetails getTransactionDetails()


### Example

```typescript
import {
    DefaultApi,
    Configuration
} from './api';

const configuration = new Configuration();
const apiInstance = new DefaultApi(configuration);

let txHash: string; //Hash de la transacción (default to undefined)
let fromDate: string; //Fecha de inicio para filtrar resultados (optional) (default to undefined)
let toDate: string; //Fecha de fin para filtrar resultados (optional) (default to undefined)

const { status, data } = await apiInstance.getTransactionDetails(
    txHash,
    fromDate,
    toDate
);
```

### Parameters

|Name | Type | Description  | Notes|
|------------- | ------------- | ------------- | -------------|
| **txHash** | [**string**] | Hash de la transacción | defaults to undefined|
| **fromDate** | [**string**] | Fecha de inicio para filtrar resultados | (optional) defaults to undefined|
| **toDate** | [**string**] | Fecha de fin para filtrar resultados | (optional) defaults to undefined|


### Return type

**TransactionDetails**

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
|**200** | Detalles de la transacción |  -  |
|**404** | Transacción no encontrada |  -  |
|**500** | Error interno del servidor |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

