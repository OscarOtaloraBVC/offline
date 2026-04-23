# PriceReference

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**Asset** | Pointer to **string** |  | [optional] 
**Price** | Pointer to **float32** |  | [optional] 

## Methods

### NewPriceReference

`func NewPriceReference() *PriceReference`

NewPriceReference instantiates a new PriceReference object
This constructor will assign default values to properties that have it defined,
and makes sure properties required by API are set, but the set of arguments
will change when the set of required properties is changed

### NewPriceReferenceWithDefaults

`func NewPriceReferenceWithDefaults() *PriceReference`

NewPriceReferenceWithDefaults instantiates a new PriceReference object
This constructor will only assign default values to properties that have it defined,
but it doesn't guarantee that properties required by API are set

### GetAsset

`func (o *PriceReference) GetAsset() string`

GetAsset returns the Asset field if non-nil, zero value otherwise.

### GetAssetOk

`func (o *PriceReference) GetAssetOk() (*string, bool)`

GetAssetOk returns a tuple with the Asset field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetAsset

`func (o *PriceReference) SetAsset(v string)`

SetAsset sets Asset field to given value.

### HasAsset

`func (o *PriceReference) HasAsset() bool`

HasAsset returns a boolean if a field has been set.

### GetPrice

`func (o *PriceReference) GetPrice() float32`

GetPrice returns the Price field if non-nil, zero value otherwise.

### GetPriceOk

`func (o *PriceReference) GetPriceOk() (*float32, bool)`

GetPriceOk returns a tuple with the Price field if it's non-nil, zero value otherwise
and a boolean to check if the value has been set.

### SetPrice

`func (o *PriceReference) SetPrice(v float32)`

SetPrice sets Price field to given value.

### HasPrice

`func (o *PriceReference) HasPrice() bool`

HasPrice returns a boolean if a field has been set.


[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


