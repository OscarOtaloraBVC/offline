# TransactionDetails

## Properties

Name | Type | Description
------------ | ------------- | -------------
**TxHash** | Pointer to **string** | [optional]
**Details** | Pointer to [**TransactionDetailsDetails**](TransactionDetailsDetails.md) | [optional]

## Methods

### NewTransactionDetails

`func NewTransactionDetails() *TransactionDetails`

NewTransactionDetails instantiates a new TransactionDetails object
This constructor will assign default values to properties that have it defined,
and makes sure properties required by API are set, but the set of arguments
will change when the set of required properties is changed

### NewTransactionDetailsWithDefaults

`func NewTransactionDetailsWithDefaults() *TransactionDetails`

NewTransactionDetailsWithDefaults instantiates a new TransactionDetails object
This constructor will only assign default values to properties that have it defined,
but it doesn't guarantee that properties required by API are set

### GetTxHash

`func (o *TransactionDetails) GetTxHash() string`

GetTxHash returns the TxHash field if non-nil, zero value otherwise.

### GetTxHashOk

`func (o *TransactionDetails) GetTxHashOk() (*string, bool)`

GetTxHashOk returns a tuple with the TxHash field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetTxHash

`func (o *TransactionDetails) SetTxHash(v string)`

SetTxHash sets TxHash field to given value.

### HasTxHash

`func (o *TransactionDetails) HasTxHash() bool`

HasTxHash returns a boolean if a field has been set.

### GetDetails

`func (o *TransactionDetails) GetDetails() TransactionDetailsDetails`

GetDetails returns the Details field if non-nil, zero value otherwise.

### GetDetailsOk

`func (o *TransactionDetails) GetDetailsOk() (*TransactionDetailsDetails, bool)`

GetDetailsOk returns a tuple with the Details field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetDetails

`func (o *TransactionDetails) SetDetails(v TransactionDetailsDetails)`

SetDetails sets Details field to given value.

### HasDetails

`func (o *TransactionDetails) HasDetails() bool`

HasDetails returns a boolean if a field has been set.

[[Back to Model list]](../README.md#documentation-for-models)
[[Back to API list]](../README.md#documentation-for-api-endpoints)
[[Back to README]](../README.md)
