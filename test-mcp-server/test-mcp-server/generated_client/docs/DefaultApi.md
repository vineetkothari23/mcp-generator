# generated_client.DefaultApi

All URIs are relative to *https://api.simple.example.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_items**](DefaultApi.md#get_items) | **GET** /items | Get all items


# **get_items**
> List[Item] get_items()

Get all items

### Example


```python
import generated_client
from generated_client.models.item import Item
from generated_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to https://api.simple.example.com
# See configuration.py for a list of all supported configuration parameters.
configuration = generated_client.Configuration(
    host = "https://api.simple.example.com"
)


# Enter a context with an instance of the API client
with generated_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = generated_client.DefaultApi(api_client)

    try:
        # Get all items
        api_response = api_instance.get_items()
        print("The response of DefaultApi->get_items:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling DefaultApi->get_items: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[Item]**](Item.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | List of items |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

