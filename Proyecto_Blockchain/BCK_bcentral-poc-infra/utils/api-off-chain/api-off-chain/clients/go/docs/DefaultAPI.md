# \DefaultAPI

All URIs are relative to *https://api.bancocentral.gov.cl/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**GetAssetPrice**](DefaultAPI.md#GetAssetPrice) | **Get** /offchain/prices/{asset} | Obtener precio de un activo
[**GetContractMetadata**](DefaultAPI.md#GetContractMetadata) | **Get** /offchain/contracts/{contractId}/metadata | Obtener metadata de un contrato inteligente
[**GetTransactionDetails**](DefaultAPI.md#GetTransactionDetails) | **Get** /offchain/transactions/{txHash}/details | Obtener detalles de una transacción



## GetAssetPrice

> PriceReference GetAssetPrice(ctx, asset).FromDate(fromDate).ToDate(toDate).Execute()

Obtener precio de un activo

### Example

```go
package main

import (
	"context"
	"fmt"
	"os"
    "time"
	openapiclient "github.com/GIT_USER_ID/GIT_REPO_ID"
)

func main() {
	asset := "asset_example" // string | Nombre del activo
	fromDate := time.Now() // string | Fecha de inicio para filtrar resultados (optional)
	toDate := time.Now() // string | Fecha de fin para filtrar resultados (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DefaultAPI.GetAssetPrice(context.Background(), asset).FromDate(fromDate).ToDate(toDate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DefaultAPI.GetAssetPrice``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetAssetPrice`: PriceReference
	fmt.Fprintf(os.Stdout, "Response from `DefaultAPI.GetAssetPrice`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**asset** | **string** | Nombre del activo | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetAssetPriceRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **fromDate** | **string** | Fecha de inicio para filtrar resultados | 
 **toDate** | **string** | Fecha de fin para filtrar resultados | 

### Return type

[**PriceReference**](PriceReference.md)

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetContractMetadata

> ContractMetadata GetContractMetadata(ctx, contractId).FromDate(fromDate).ToDate(toDate).Execute()

Obtener metadata de un contrato inteligente

### Example

```go
package main

import (
	"context"
	"fmt"
	"os"
    "time"
	openapiclient "github.com/GIT_USER_ID/GIT_REPO_ID"
)

func main() {
	contractId := "contractId_example" // string | ID del contrato inteligente
	fromDate := time.Now() // string | Fecha de inicio para filtrar resultados (optional)
	toDate := time.Now() // string | Fecha de fin para filtrar resultados (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DefaultAPI.GetContractMetadata(context.Background(), contractId).FromDate(fromDate).ToDate(toDate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DefaultAPI.GetContractMetadata``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetContractMetadata`: ContractMetadata
	fmt.Fprintf(os.Stdout, "Response from `DefaultAPI.GetContractMetadata`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**contractId** | **string** | ID del contrato inteligente | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetContractMetadataRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **fromDate** | **string** | Fecha de inicio para filtrar resultados | 
 **toDate** | **string** | Fecha de fin para filtrar resultados | 

### Return type

[**ContractMetadata**](ContractMetadata.md)

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)


## GetTransactionDetails

> TransactionDetails GetTransactionDetails(ctx, txHash).FromDate(fromDate).ToDate(toDate).Execute()

Obtener detalles de una transacción

### Example

```go
package main

import (
	"context"
	"fmt"
	"os"
    "time"
	openapiclient "github.com/GIT_USER_ID/GIT_REPO_ID"
)

func main() {
	txHash := "txHash_example" // string | Hash de la transacción
	fromDate := time.Now() // string | Fecha de inicio para filtrar resultados (optional)
	toDate := time.Now() // string | Fecha de fin para filtrar resultados (optional)

	configuration := openapiclient.NewConfiguration()
	apiClient := openapiclient.NewAPIClient(configuration)
	resp, r, err := apiClient.DefaultAPI.GetTransactionDetails(context.Background(), txHash).FromDate(fromDate).ToDate(toDate).Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error when calling `DefaultAPI.GetTransactionDetails``: %v\n", err)
		fmt.Fprintf(os.Stderr, "Full HTTP response: %v\n", r)
	}
	// response from `GetTransactionDetails`: TransactionDetails
	fmt.Fprintf(os.Stdout, "Response from `DefaultAPI.GetTransactionDetails`: %v\n", resp)
}
```

### Path Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
**ctx** | **context.Context** | context for authentication, logging, cancellation, deadlines, tracing, etc.
**txHash** | **string** | Hash de la transacción | 

### Other Parameters

Other parameters are passed through a pointer to a apiGetTransactionDetailsRequest struct via the builder pattern


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------

 **fromDate** | **string** | Fecha de inicio para filtrar resultados | 
 **toDate** | **string** | Fecha de fin para filtrar resultados | 

### Return type

[**TransactionDetails**](TransactionDetails.md)

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to Model list]](../README.md#documentation-for-models)
[[Back to README]](../README.md)

