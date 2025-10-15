# Amazon SP-API: getInventorySummaries

## Overview

The `getInventorySummaries` operation returns a list of inventory summaries from Amazon's Selling Partner API (SP-API). The summaries returned depend on the presence or absence of specific query parameters:

- **All inventory summaries** with available details are returned when `startDateTime`, `sellerSkus`, and `sellerSku` parameters are omitted.
- **Inventory summaries with changes** after a specified date/time are returned when `startDateTime` is provided.
- **Inventory summaries for specific SKUs** are returned when `sellerSkus` parameter is provided (up to 50 SKUs).
- **Inventory summaries for a single SKU** are returned when `sellerSku` parameter is provided.

**Important:** To avoid errors with SKUs when encoding URLs, refer to [URL Encoding](https://developer-docs.amazon.com/sp-api/docs/url-encoding) guidelines.

## Endpoint

```
GET https://sellingpartnerapi-na.amazon.com/fba/inventory/v1/summaries
```

## Usage Plan

| Rate (requests per second) | Burst |
|---------------------------|-------|
| 2                         | 2     |

The `x-amzn-RateLimit-Limit` response header returns the usage plan rate limits that were applied to the requested operation, when available. The table above indicates the default rate and burst values for this operation. Selling partners whose business demands require higher throughput may see higher rate and burst values than those shown here.

For more information, see [Usage Plans and Rate Limits](https://developer-docs.amazon.com/sp-api/docs/usage-plans-and-rate-limits) in the Selling Partner API documentation.

## Authentication

This API requires authentication using the [Selling Partner API authentication flow](https://developer-docs.amazon.com/sp-api/docs/connecting-to-the-selling-partner-api).

## Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `details` | boolean | No | Set to `true` to return inventory summaries with additional summarized inventory details and quantities. Defaults to `false`. | `true` |
| `granularityType` | string | **Yes** | The granularity type for the inventory aggregation level. | `Marketplace` |
| `granularityId` | string | **Yes** | The granularity ID for the inventory aggregation level. | `A1F83G8C2ARO7P` |
| `startDateTime` | date-time | No | A start date and time in ISO8601 format. If specified, all inventory summaries that have changed since then are returned. Must be no earlier than 18 months prior to the request. **Note:** Changes in `inboundWorkingQuantity`, `inboundShippedQuantity` and `inboundReceivingQuantity` are not detected. | `2023-01-01T00:00:00Z` |
| `sellerSkus` | array of strings | No | A list of seller SKUs for which to return inventory summaries. You may specify up to 50 SKUs. | `["SKU001","SKU002"]` |
| `sellerSku` | string | No | A single seller SKU used for querying the specified seller SKU inventory summaries. | `SKU001` |
| `nextToken` | string | No | String token returned in the response of your previous request. The string token will expire 30 seconds after being created. | `nextToken123` |
| `marketplaceIds` | array of strings | **Yes** | The marketplace ID for the marketplace for which to return inventory summaries. Maximum length: 1. | `["A1F83G8C2ARO7P"]` |

### Granularity Types

| Value | Description |
|-------|-------------|
| `Marketplace` | Aggregates inventory data by marketplace |

### Marketplace IDs

Common marketplace IDs include:
- `A1F83G8C2ARO7P` - United Kingdom
- `ATVPDKIKX0DER` - United States
- `A1AM78C8D3NZFA` - Canada
- `A1PA6795UKMFR9` - Germany
- `A1RKKUPIHCS9HS` - Spain
- `A13V1IB3VIYZZH` - France
- `APJ6JRA9NG5V4` - Italy

## Responses

### 200 OK

**Response body schema:**

```json
{
  "payload": {
    "granularity": {
      "granularityType": "string",
      "granularityId": "string"
    },
    "inventorySummaries": [
      {
        "asin": "string",
        "fnSku": "string",
        "sellerSku": "string",
        "condition": "string",
        "inventoryDetails": {
          "fulfillableQuantity": 0,
          "inboundWorkingQuantity": 0,
          "inboundShippedQuantity": 0,
          "inboundReceivingQuantity": 0,
          "reservedQuantity": {
            "totalReservedQuantity": 0,
            "pendingCustomerOrderQuantity": 0,
            "pendingTransshipmentQuantity": 0,
            "fcProcessingQuantity": 0
          },
          "researchingQuantity": {
            "totalResearchingQuantity": 0,
            "researchingQuantityBreakdown": [
              {
                "name": "researchingQuantityInShortTerm",
                "quantity": 0
              }
            ]
          },
          "unfulfillableQuantity": {
            "totalUnfulfillableQuantity": 0,
            "customerDamagedQuantity": 0,
            "warehouseDamagedQuantity": 0,
            "distributorDamagedQuantity": 0,
            "carrierDamagedQuantity": 0,
            "defectiveQuantity": 0,
            "expiredQuantity": 0
          }
        },
        "lastUpdatedTime": "2025-10-13T04:18:10.465Z",
        "productName": "string",
        "totalQuantity": 0,
        "stores": [
          "string"
        ]
      }
    ]
  },
  "pagination": {
    "nextToken": "string"
  },
  "errors": [
    {
      "code": "string",
      "message": "string",
      "details": "string"
    }
  ]
}
```

**Response Schema Details:**

#### Payload Object
- `granularity` (object, required): Describes a granularity at which inventory data can be aggregated
- `inventorySummaries` (array, required): A list of inventory summaries

#### Inventory Summary Object
- `asin` (string): The Amazon Standard Identification Number (ASIN) of an item
- `fnSku` (string): Amazon's fulfillment network SKU identifier
- `sellerSku` (string): The seller SKU of the item
- `condition` (string): The condition of the item as described by the seller
- `inventoryDetails` (object): Summarized inventory details (only present if `details=true`)
- `lastUpdatedTime` (date-time): The date and time that any quantity was last updated
- `productName` (string): The localized language product title of the item within the specific marketplace
- `totalQuantity` (integer): The total number of units in an inbound shipment or in Amazon fulfillment centers
- `stores` (array of strings): A list of seller-enrolled stores that apply to this seller SKU

#### Inventory Details Object
- `fulfillableQuantity` (integer): Available inventory that can be fulfilled
- `inboundWorkingQuantity` (integer): Inventory currently being prepared for fulfillment
- `inboundShippedQuantity` (integer): Inventory that has been shipped to Amazon
- `inboundReceivingQuantity` (integer): Inventory currently being received at Amazon
- `reservedQuantity` (object): Inventory reserved for existing orders
- `researchingQuantity` (object): Inventory currently being researched for potential issues
- `unfulfillableQuantity` (object): Inventory that cannot be fulfilled due to various issues

#### Pagination Object
- `nextToken` (string): Token for retrieving the next page of results (expires in 30 seconds)

### Error Responses

#### 400 Bad Request
Request has missing or invalid parameters and cannot be parsed.

#### 403 Forbidden
Indicates access to the resource is forbidden. Possible reasons include:
- Access Denied
- Unauthorized
- Expired Token
- Invalid Signature
- Resource Not Found

#### 404 Not Found
The specified resource does not exist.

#### 429 Too Many Requests
The frequency of requests was greater than allowed.

#### 500 Internal Server Error
An unexpected condition occurred that prevented the server from fulfilling the request.

#### 503 Service Unavailable
Temporary overloading or maintenance of the server.

## Response Headers

| Header | Description |
|--------|-------------|
| `x-amzn-RateLimit-Limit` | Your rate limit (requests per second) for this operation |
| `x-amzn-RequestId` | Unique request reference identifier |

## Usage Examples

### Shell (curl)

```bash
curl --request GET \
     --url 'https://sellingpartnerapi-na.amazon.com/fba/inventory/v1/summaries?details=true&granularityType=Marketplace&granularityId=A1F83G8C2ARO7P&marketplaceIds=A1F83G8C2ARO7P' \
     --header 'accept: application/json' \
     --header 'x-amz-access-token: YOUR_ACCESS_TOKEN'
```

### Python (using existing amazon_api.py)

```python
from amazon_api import AmazonAPI
from config import AmazonCredentials
import json

# Initialize API client
credentials = AmazonCredentials()
api = AmazonAPI(credentials)

def get_inventory_summaries(detailed=False, seller_skus=None, start_date=None):
    """Get inventory summaries with optional filtering"""

    # Build query parameters
    params = {
        'details': 'true' if detailed else 'false',
        'granularityType': 'Marketplace',
        'granularityId': credentials.marketplace_id,
        'marketplaceIds': [credentials.marketplace_id]
    }

    # Add optional parameters
    if seller_skus:
        if len(seller_skus) == 1:
            params['sellerSku'] = seller_skus[0]
        else:
            params['sellerSkus'] = seller_skus

    if start_date:
        params['startDateTime'] = start_date.isoformat()

    # Build query string
    query_parts = []
    for key, value in params.items():
        if isinstance(value, list):
            for item in value:
                query_parts.append(f"{key}={item}")
        else:
            query_parts.append(f"{key}={value}")

    query_string = '&'.join(query_parts)
    endpoint = f"/fba/inventory/v1/summaries?{query_string}"

    try:
        response = api._make_api_request('GET', endpoint)
        return response

    except Exception as e:
        print(f"Error getting inventory summaries: {e}")
        raise

# Example usage
if __name__ == "__main__":
    # Get all inventory summaries with details
    all_summaries = get_inventory_summaries(detailed=True)
    print(f"Found {len(all_summaries.get('inventorySummaries', []))} inventory items")

    # Get specific SKUs
    sku_summaries = get_inventory_summaries(
        detailed=True,
        seller_skus=['SKU001', 'SKU002']
    )

    # Get summaries changed since date
    from datetime import datetime, timedelta
    since_date = datetime.now() - timedelta(days=7)
    recent_summaries = get_inventory_summaries(
        detailed=True,
        start_date=since_date
    )
```

### Python (Enhanced existing method)

```python
def get_inventory_summaries_advanced(self, **kwargs):
    """
    Enhanced method to get inventory summaries with full parameter support

    Args:
        details (bool): Include detailed inventory information
        granularity_type (str): Inventory aggregation level (default: 'Marketplace')
        granularity_id (str): Specific granularity identifier
        start_date_time (datetime): Get summaries changed since this time
        seller_skus (list): List of seller SKUs to query (max 50)
        seller_sku (str): Single seller SKU to query
        next_token (str): Token for pagination
        marketplace_ids (list): Marketplace IDs (required)

    Returns:
        dict: API response with inventory summaries
    """
    # Build query parameters
    params = []

    if kwargs.get('details', False):
        params.append('details=true')
    else:
        params.append('details=false')

    granularity_type = kwargs.get('granularity_type', 'Marketplace')
    granularity_id = kwargs.get('granularity_id', self.credentials.marketplace_id)

    params.append(f'granularityType={granularity_type}')
    params.append(f'granularityId={granularity_id}')

    # Handle SKU parameters (mutually exclusive)
    seller_skus = kwargs.get('seller_skus')
    seller_sku = kwargs.get('seller_sku')

    if seller_skus and seller_sku:
        raise ValueError("Cannot specify both seller_skus and seller_sku")

    if seller_skus:
        if len(seller_skus) > 50:
            raise ValueError("Maximum 50 seller SKUs allowed")
        sku_params = ','.join(seller_skus)
        params.append(f'sellerSkus={sku_params}')

    if seller_sku:
        params.append(f'sellerSku={seller_sku}')

    # Handle date filtering
    start_date_time = kwargs.get('start_date_time')
    if start_date_time:
        from datetime import datetime
        if isinstance(start_date_time, datetime):
            start_date_time = start_date_time.isoformat()
        params.append(f'startDateTime={start_date_time}')

    # Handle pagination
    next_token = kwargs.get('next_token')
    if next_token:
        params.append(f'nextToken={next_token}')

    # Handle marketplace IDs
    marketplace_ids = kwargs.get('marketplace_ids', [self.credentials.marketplace_id])
    if len(marketplace_ids) > 1:
        raise ValueError("Maximum 1 marketplace ID allowed")

    for marketplace_id in marketplace_ids:
        params.append(f'marketplaceIds={marketplace_id}')

    # Build endpoint
    query_string = '&'.join(params)
    endpoint = f"/fba/inventory/v1/summaries?{query_string}"

    return self._make_api_request('GET', endpoint)

# Usage examples in existing amazon_api.py context:
# api.get_inventory_summaries_advanced(details=True)
# api.get_inventory_summaries_advanced(seller_skus=['SKU001', 'SKU002'])
# api.get_inventory_summaries_advanced(start_date_time=datetime.now())
```

### Node.js

```javascript
const axios = require('axios');

async function getInventorySummaries(accessToken, options = {}) {
    const {
        details = false,
        granularityType = 'Marketplace',
        granularityId = 'A1F83G8C2ARO7P',
        marketplaceIds = ['A1F83G8C2ARO7P'],
        sellerSkus = null,
        sellerSku = null,
        startDateTime = null,
        nextToken = null
    } = options;

    // Build query parameters
    const params = new URLSearchParams({
        details: details.toString(),
        granularityType,
        granularityId,
        marketplaceIds: marketplaceIds.join(',')
    });

    if (sellerSkus && sellerSkus.length > 0) {
        if (sellerSkus.length === 1) {
            params.append('sellerSku', sellerSkus[0]);
        } else {
            params.append('sellerSkus', sellerSkus.join(','));
        }
    }

    if (sellerSku) {
        params.append('sellerSku', sellerSku);
    }

    if (startDateTime) {
        params.append('startDateTime', startDateTime.toISOString());
    }

    if (nextToken) {
        params.append('nextToken', nextToken);
    }

    try {
        const response = await axios.get(
            `https://sellingpartnerapi-na.amazon.com/fba/inventory/v1/summaries?${params}`,
            {
                headers: {
                    'x-amz-access-token': accessToken,
                    'Content-Type': 'application/json'
                }
            }
        );

        return response.data;
    } catch (error) {
        console.error('Error fetching inventory summaries:', error.response?.data || error.message);
        throw error;
    }
}

// Usage examples
// Get all summaries with details
// const summaries = await getInventorySummaries(accessToken, { details: true });

// Get specific SKUs
// const skuSummaries = await getInventorySummaries(accessToken, {
//     sellerSkus: ['SKU001', 'SKU002'],
//     details: true
// });
```

### Ruby

```ruby
require 'net/http'
require 'uri'
require 'json'

def get_inventory_summaries(access_token, options = {})
  details = options.fetch(:details, false)
  granularity_type = options.fetch(:granularity_type, 'Marketplace')
  granularity_id = options.fetch(:granularity_id, 'A1F83G8C2ARO7P')
  marketplace_ids = options.fetch(:marketplace_ids, ['A1F83G8C2ARO7P'])
  seller_skus = options[:seller_skus]
  seller_sku = options[:seller_sku]
  start_date_time = options[:start_date_time]
  next_token = options[:next_token]

  # Build query parameters
  params = {
    'details' => details.to_s,
    'granularityType' => granularity_type,
    'granularityId' => granularity_id,
    'marketplaceIds' => marketplace_ids.join(',')
  }

  if seller_skus && !seller_skus.empty?
    if seller_skus.length == 1
      params['sellerSku'] = seller_skus.first
    else
      params['sellerSkus'] = seller_skus.join(',')
    end
  elsif seller_sku
    params['sellerSku'] = seller_sku
  end

  params['startDateTime'] = start_date_time.iso8601 if start_date_time
  params['nextToken'] = next_token if next_token

  uri = URI('https://sellingpartnerapi-na.amazon.com/fba/inventory/v1/summaries')
  uri.query = URI.encode_www_form(params)

  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = true

  request = Net::HTTP::Get.new(uri)
  request['x-amz-access-token'] = access_token
  request['Content-Type'] = 'application/json'

  response = http.request(request)

  unless response.code == '200'
    raise "API Error: #{response.code} - #{response.body}"
  end

  JSON.parse(response.body)
end

# Usage examples
# Get all summaries
# summaries = get_inventory_summaries(access_token, details: true)

# Get specific SKUs
# sku_summaries = get_inventory_summaries(access_token,
#   seller_skus: ['SKU001', 'SKU002'],
#   details: true
# )
```

### PHP

```php
<?php

function getInventorySummaries($accessToken, $options = []) {
    $details = $options['details'] ?? false;
    $granularityType = $options['granularityType'] ?? 'Marketplace';
    $granularityId = $options['granularityId'] ?? 'A1F83G8C2ARO7P';
    $marketplaceIds = $options['marketplaceIds'] ?? ['A1F83G8C2ARO7P'];
    $sellerSkus = $options['sellerSkus'] ?? null;
    $sellerSku = $options['sellerSku'] ?? null;
    $startDateTime = $options['startDateTime'] ?? null;
    $nextToken = $options['nextToken'] ?? null;

    // Build query parameters
    $params = [
        'details' => $details ? 'true' : 'false',
        'granularityType' => $granularityType,
        'granularityId' => $granularityId,
        'marketplaceIds' => implode(',', $marketplaceIds)
    ];

    if ($sellerSkus && count($sellerSkus) > 0) {
        if (count($sellerSkus) === 1) {
            $params['sellerSku'] = $sellerSkus[0];
        } else {
            $params['sellerSkus'] = implode(',', $sellerSkus);
        }
    } elseif ($sellerSku) {
        $params['sellerSku'] = $sellerSku;
    }

    if ($startDateTime) {
        $params['startDateTime'] = $startDateTime->format('Y-m-d\TH:i:s\Z');
    }

    if ($nextToken) {
        $params['nextToken'] = $nextToken;
    }

    $url = 'https://sellingpartnerapi-na.amazon.com/fba/inventory/v1/summaries?' .
           http_build_query($params);

    $headers = [
        'x-amz-access-token: ' . $accessToken,
        'Content-Type: application/json'
    ];

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'GET');

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);

    if (curl_errno($ch)) {
        throw new Exception('Request Error: ' . curl_error($ch));
    }

    curl_close($ch);

    if ($httpCode !== 200) {
        throw new Exception("API Error: {$httpCode} - {$response}");
    }

    return json_decode($response, true);
}

// Usage examples
try {
    // Get all summaries with details
    $summaries = getInventorySummaries($accessToken, ['details' => true]);

    // Get specific SKUs
    $skuSummaries = getInventorySummaries($accessToken, [
        'sellerSkus' => ['SKU001', 'SKU002'],
        'details' => true
    ]);

    // Get summaries changed in last 7 days
    $recentDate = new DateTime('-7 days');
    $recentSummaries = getInventorySummaries($accessToken, [
        'startDateTime' => $recentDate,
        'details' => true
    ]);

} catch (Exception $e) {
    echo 'Error: ' . $e->getMessage();
}
?>
```

## Integration with Existing Codebase

### Enhanced FBA Inventory Check

The existing `check_fba_inventory` method in `amazon_api.py` can be enhanced to use the full capabilities of this API:

```python
def check_fba_inventory_enhanced(self, sku: str, include_details: bool = False) -> Dict:
    """Enhanced FBA inventory check with full API capabilities"""
    try:
        response = self.get_inventory_summaries_advanced(
            seller_sku=sku,
            details=include_details,
            marketplace_ids=[self.credentials.marketplace_id]
        )

        inventory_summaries = response.get('inventorySummaries', [])

        if inventory_summaries:
            inventory = inventory_summaries[0]
            details = inventory.get('inventoryDetails', {})

            return {
                'sellerSku': inventory.get('sellerSku', ''),
                'asin': inventory.get('asin', ''),
                'productName': inventory.get('productName', ''),
                'condition': inventory.get('condition', ''),
                'totalQuantity': inventory.get('totalQuantity', 0),
                'lastUpdatedTime': inventory.get('lastUpdatedTime', ''),
                'fulfillableQuantity': details.get('fulfillableQuantity', 0),
                'inboundWorkingQuantity': details.get('inboundWorkingQuantity', 0),
                'inboundShippedQuantity': details.get('inboundShippedQuantity', 0),
                'inboundReceivingQuantity': details.get('inboundReceivingQuantity', 0),
                'reservedQuantity': details.get('reservedQuantity', {}),
                'unfulfillableQuantity': details.get('unfulfillableQuantity', {})
            }
        else:
            return {
                'sellerSku': sku,
                'totalQuantity': 0,
                'fulfillableQuantity': 0,
                'inboundWorkingQuantity': 0,
                'inboundShippedQuantity': 0,
                'inboundReceivingQuantity': 0
            }

    except Exception as e:
        logger.error(f"Enhanced FBA inventory check failed for {sku}: {e}")
        # Fallback to simple method for compatibility
        return self.check_fba_inventory(sku)
```

### Batch Inventory Checking

```python
def check_multiple_skus_inventory(self, skus: List[str], include_details: bool = False) -> List[Dict]:
    """Check inventory for multiple SKUs efficiently"""
    if len(skus) > 50:
        # Split into batches of 50 (API limit)
        batches = [skus[i:i+50] for i in range(0, len(skus), 50)]
        results = []

        for batch in batches:
            batch_results = self._check_sku_batch_inventory(batch, include_details)
            results.extend(batch_results)
            time.sleep(1)  # Rate limiting

        return results
    else:
        return self._check_sku_batch_inventory(skus, include_details)

def _check_sku_batch_inventory(self, skus: List[str], include_details: bool) -> List[Dict]:
    """Check inventory for a batch of SKUs"""
    try:
        response = self.get_inventory_summaries_advanced(
            seller_skus=skus,
            details=include_details,
            marketplace_ids=[self.credentials.marketplace_id]
        )

        inventory_summaries = response.get('inventorySummaries', [])
        return [
            {
                'sellerSku': item.get('sellerSku', ''),
                'asin': item.get('asin', ''),
                'productName': item.get('productName', ''),
                'totalQuantity': item.get('totalQuantity', 0),
                'fulfillableQuantity': item.get('inventoryDetails', {}).get('fulfillableQuantity', 0),
                'lastUpdatedTime': item.get('lastUpdatedTime', '')
            }
            for item in inventory_summaries
        ]

    except Exception as e:
        logger.error(f"Batch inventory check failed for {len(skus)} SKUs: {e}")
        # Return empty results for all SKUs in batch
        return [{'sellerSku': sku, 'totalQuantity': 0} for sku in skus]
```

## Best Practices

1. **Rate Limiting**: Respect the 2 requests/second limit. Implement delays between requests.
2. **Pagination**: Always handle `nextToken` for large result sets.
3. **Error Handling**: Implement proper error handling for 429 (rate limit) and 500 (server) errors.
4. **Parameter Validation**: Validate SKU parameters and marketplace IDs before making requests.
5. **Caching**: Consider caching inventory data for frequently accessed SKUs.
6. **URL Encoding**: Ensure SKUs are properly URL-encoded to handle special characters.
7. **Date Filtering**: Use `startDateTime` for incremental updates rather than fetching all data repeatedly.

## Troubleshooting

### Common Issues

**"Invalid parameters" (400)**
- Check that `granularityType` and `granularityId` are valid
- Verify `marketplaceIds` contains a valid marketplace ID
- Ensure SKU parameters don't exceed length limits

**"Rate limit exceeded" (429)**
- Implement delays between requests (minimum 500ms)
- Reduce request frequency during peak hours
- Use batch processing with appropriate delays

**"Unauthorized" (403)**
- Verify access token is valid and not expired
- Check that the selling partner has FBA inventory permissions
- Ensure correct marketplace access

**"Not found" (404)**
- Verify SKU exists in your catalog
- Check that the SKU is available in the specified marketplace

### Debug Logging

Enable debug logging to troubleshoot API issues:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# The existing amazon_api.py already includes comprehensive error logging
# Check logs/sku_cleanup.log for detailed error information
```
