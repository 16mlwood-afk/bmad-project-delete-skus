"""
Amazon SP-API integration for SKU Cleanup Tool
Handles authentication, report generation, and SKU operations with API resilience
"""
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
import boto3
from botocore.exceptions import ClientError
from urllib.parse import quote

from .config import AmazonCredentials, config
from .resilience import (
    exponential_backoff,
    CircuitBreaker,
    CircuitBreakerConfig,
    create_session_with_pool,
    get_api_session,
    ErrorType
)

logger = logging.getLogger(__name__)

class AmazonAPI:
    """Amazon Selling Partner API integration with resilience patterns"""

    def __init__(self, credentials: AmazonCredentials):
        self.credentials = credentials
        self.access_token = None
        self.token_expiry = None

        # Initialize AWS clients
        self._init_aws_clients()

        # Initialize resilience components
        self._init_resilience()

    def _init_resilience(self):
        """Initialize circuit breakers and session management"""
        # Create circuit breakers for different API endpoints
        cb_config = CircuitBreakerConfig(
            failure_threshold=config.settings.resilience.circuit_breaker_failure_threshold,
            recovery_timeout=config.settings.resilience.circuit_breaker_recovery_timeout
        )

        self.circuit_breakers = {
            'reports': CircuitBreaker('reports_api', cb_config),
            'fba_inventory': CircuitBreaker('fba_inventory_api', cb_config),
            'listings': CircuitBreaker('listings_api', cb_config),
            'auth': CircuitBreaker('auth_api', cb_config)
        }

        # Use shared session for connection pooling
        self.session = get_api_session()

    def _init_aws_clients(self):
        """Initialize AWS clients for SP-API"""
        try:
            self.sp_client = boto3.client(
                's3',  # We'll use S3 for downloading reports
                aws_access_key_id=self.credentials.access_key_id,
                aws_secret_access_key=self.credentials.secret_access_key,
                region_name='us-east-1'  # SP-API uses us-east-1
            )
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            raise

    @exponential_backoff(
        max_retries=config.settings.resilience.max_retries,
        base_delay=config.settings.resilience.base_delay,
        max_delay=config.settings.resilience.max_delay,
        backoff_factor=config.settings.resilience.backoff_factor,
        jitter=config.settings.resilience.jitter
    )
    def _get_access_token(self) -> str:
        """Get or refresh access token for SP-API with circuit breaker protection"""
        now = datetime.utcnow()

        # Check if we have a valid token
        if (self.access_token and self.token_expiry and
            now < self.token_expiry - timedelta(minutes=5)):
            return self.access_token

        logger.info("Getting new access token...")

        token_url = "https://api.amazon.com/auth/o2/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.credentials.lwa_refresh_token,
            'client_id': self.credentials.lwa_client_id,
            'client_secret': self.credentials.lwa_client_secret
        }

        try:
            response = self.session.post(
                token_url,
                headers=headers,
                data=data,
                timeout=(config.settings.resilience.connection_timeout, config.settings.resilience.read_timeout)
            )
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data['access_token']
            # Token is valid for 1 hour (3600 seconds)
            self.token_expiry = now + timedelta(seconds=token_data['expires_in'])

            logger.info("Successfully obtained access token")
            return self.access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get access token: {e}")
            raise

    def _get_base_url_for_marketplace(self) -> str:
        """Determine the correct base URL based on marketplace ID"""
        marketplace_id = self.credentials.marketplace_id

        # EU marketplaces
        eu_marketplaces = [
            'A1F83G8C2ARO7P',  # UK
            'A1PA6795UKMFR9',  # UK (another one)
            'A1RKKUPIHCS9HS',  # Spain
            'A13V1IB3VIYZZH',  # France
            'A1JEUMLCLC2WX2',  # Germany
            'A1805IZSGTT6HS',  # Italy
            'A2NODRKZP88ZB9',  # Sweden
            'A1C3SOZRARQ6R3',  # Poland
            'A17E79C6D8DWNP',  # Netherlands
            'AE08WJ6YKNBMC',   # Belgium
        ]

        # NA marketplaces
        na_marketplaces = [
            'ATVPDKIKX0DER',   # US
            'A1AM78C64UM0Y8',  # Canada
            'A2Q3Y263D00KWC',  # Brazil
            'APJ6JRA9NG5V4',   # Mexico
        ]

        # FE marketplaces
        fe_marketplaces = [
            'A2EUQ1WTGCTBG2',  # Australia
            'A1VC38T7YXB528',  # Japan
            'A39IBJ37TRP1C6',   # Turkey
            'AAHKV2XAUZCBG',    # India
            'A19VAU5U5O7RUS',  # Singapore
            'A2ZV50J4W1RKNI',  # UAE
        ]

        if marketplace_id in eu_marketplaces:
            return 'https://sellingpartnerapi-eu.amazon.com'
        elif marketplace_id in na_marketplaces:
            return 'https://sellingpartnerapi-na.amazon.com'
        elif marketplace_id in fe_marketplaces:
            return 'https://sellingpartnerapi-fe.amazon.com'
        else:
            # Default to EU for UK marketplace as fallback
            logger.warning(f"Unknown marketplace ID: {marketplace_id}, defaulting to EU endpoint")
            return 'https://sellingpartnerapi-eu.amazon.com'

    def _get_circuit_breaker_for_endpoint(self, endpoint: str) -> str:
        """Determine which circuit breaker to use based on endpoint"""
        if '/reports/' in endpoint:
            return 'reports'
        elif '/fba/inventory/' in endpoint:
            return 'fba_inventory'  # Still return name for logging, but won't use circuit breaker
        elif '/listings/' in endpoint:
            return 'listings'
        else:
            return 'auth'  # Default fallback

    def _make_api_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make authenticated API request to SP-API with resilience patterns"""
        token = self._get_access_token()

        # Extract our custom parameters before passing to requests
        expected_errors = kwargs.pop('expected_errors', [])

        headers = {
            'x-amz-access-token': token,
            'Content-Type': 'application/json',
            **kwargs.get('headers', {})
        }

        base_url = self._get_base_url_for_marketplace()
        url = f"{base_url}{endpoint}"

        # Determine which circuit breaker to use
        circuit_breaker_name = self._get_circuit_breaker_for_endpoint(endpoint)

        # Skip circuit breaker for FBA inventory API since it works when tested individually
        # but fails during bulk operations due to rate limiting
        use_circuit_breaker = circuit_breaker_name != 'fba_inventory'

        try:
            if use_circuit_breaker:
                circuit_breaker = self.circuit_breakers[circuit_breaker_name]

                # Use circuit breaker and exponential backoff for non-FBA endpoints
                @circuit_breaker
                @exponential_backoff(
                    max_retries=config.settings.resilience.max_retries,
                    base_delay=config.settings.resilience.base_delay,
                    max_delay=config.settings.resilience.max_delay,
                    backoff_factor=config.settings.resilience.backoff_factor,
                    jitter=config.settings.resilience.jitter
                )
                def _execute_request():
                    response = self.session.request(
                        method,
                        url,
                        headers=headers,
                        timeout=(config.settings.resilience.connection_timeout, config.settings.resilience.read_timeout),
                        **kwargs
                    )

                    # Check for expected error codes that should not raise exceptions
                    if response.status_code in expected_errors:
                        return {'_status_code': response.status_code, '_response_text': response.text}

                    response.raise_for_status()
                    return response.json()

                return _execute_request()
            else:
                # Use only exponential backoff for FBA inventory API (no circuit breaker)
                @exponential_backoff(
                    max_retries=config.settings.resilience.max_retries,
                    base_delay=config.settings.resilience.base_delay,
                    max_delay=config.settings.resilience.max_delay,
                    backoff_factor=config.settings.resilience.backoff_factor,
                    jitter=config.settings.resilience.jitter
                )
                def _execute_request_no_cb():
                    response = self.session.request(
                        method,
                        url,
                        headers=headers,
                        timeout=(config.settings.resilience.connection_timeout, config.settings.resilience.read_timeout),
                        **kwargs
                    )

                    # Check for expected error codes that should not raise exceptions
                    if response.status_code in expected_errors:
                        return {'_status_code': response.status_code, '_response_text': response.text}

                    response.raise_for_status()
                    return response.json()

                return _execute_request_no_cb()

        except Exception as e:
            logger.error(f"API request failed after resilience patterns: {method} {endpoint} - {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")

            # If circuit breaker is open, log that information
            if "Circuit breaker" in str(e):
                logger.error(f"Circuit breaker '{circuit_breaker_name}' is preventing requests")

            raise

    def get_merchant_listings(self) -> List[Dict]:
        """Get all merchant listings using Reports API"""
        logger.info("Creating merchant listings report...")

        # Step 1: Create report request
        endpoint = "/reports/2021-06-30/reports"
        payload = {
            "reportType": "GET_MERCHANT_LISTINGS_ALL_DATA",
            "marketplaceIds": [self.credentials.marketplace_id]
        }

        response = self._make_api_request('POST', endpoint, json=payload)
        report_id = response['reportId']
        logger.info(f"Created report with ID: {report_id}")

        # Step 2: Poll for report completion
        logger.info("Waiting for report to be ready...")
        report_document_id = self._poll_report_completion(report_id)

        # Step 3: Download report
        logger.info("Downloading report data...")
        return self._download_report(report_document_id)

    def _poll_report_completion(self, report_id: str, max_attempts: int = 30) -> str:
        """Poll report status until completion"""
        endpoint = f"/reports/2021-06-30/reports/{report_id}"

        for attempt in range(max_attempts):
            response = self._make_api_request('GET', endpoint)
            status = response['processingStatus']

            if status == 'DONE':
                logger.info(f"Report completed after {attempt + 1} attempts")
                return response['reportDocumentId']
            elif status in ['FATAL', 'CANCELLED']:
                raise Exception(f"Report failed with status: {status}")

            logger.debug(f"Report status: {status} (attempt {attempt + 1}/{max_attempts})")
            time.sleep(30)  # Wait 30 seconds between checks

        raise Exception(f"Report did not complete within {max_attempts * 30} seconds")

    def _download_report(self, report_document_id: str) -> List[Dict]:
        """Download and parse report data"""
        # Get download URL
        endpoint = f"/reports/2021-06-30/documents/{report_document_id}"
        response = self._make_api_request('GET', endpoint)

        # Download from S3 URL
        download_url = response['url']
        logger.debug(f"Downloading from: {download_url}")

        download_response = self.session.get(
            download_url,
            timeout=(config.settings.resilience.connection_timeout, config.settings.resilience.read_timeout)
        )
        download_response.raise_for_status()

        # Parse TSV data
        import csv
        import io

        content = download_response.text
        reader = csv.DictReader(io.StringIO(content), delimiter='\t')

        skus = []
        for row in reader:
            # Clean up the data and convert types
            sku_data = {
                'sku': row.get('seller-sku', '').strip(),  # Fix: use 'seller-sku' not 'sku'
                'asin': row.get('asin1', '').strip(),  # Fix: use 'asin1' not 'asin'
                'created_date': row.get('open-date', '').strip(),  # Fix: use 'open-date' not 'created-date'
                'fulfillment_channel': row.get('fulfillment-channel', '').strip(),
                'quantity': int(row.get('quantity', 0) or 0),
                'item_name': row.get('item-name', '').strip(),
                'open_date': row.get('open-date', '').strip(),
                'image_url': row.get('image-url', '').strip(),
                'item_description': row.get('item-description', '').strip(),
                'listing_id': row.get('listing-id', '').strip(),
                'seller_sku': row.get('seller-sku', '').strip()
            }
            skus.append(sku_data)

        logger.info(f"Parsed {len(skus)} SKUs from report")
        return skus

    def check_fba_inventory(self, sku: str) -> Dict:
        """Check FBA inventory for a specific SKU using optimized API parameters"""
        from urllib.parse import quote

        # Use the most reliable method based on production testing
        # Method 2 (no startDateTime) proved most reliable for individual SKU lookups
        params = [
            'details=true',
            'granularityType=Marketplace',
            f'granularityId={self.credentials.marketplace_id}',
            f'marketplaceIds={self.credentials.marketplace_id}',
            f'sellerSku={quote(sku)}'
        ]

        query_string = '&'.join(params)
        endpoint = f"/fba/inventory/v1/summaries?{query_string}"

        logger.info(f"Checking FBA inventory for SKU: {sku} with endpoint: {endpoint} (optimized method)")

        try:
            response = self._make_api_request('GET', endpoint, expected_errors=[400, 404])
            logger.info(f"Raw FBA API response for {sku}: {response}")

            return self._process_fba_response(sku, response)

        except Exception as e:
            logger.error(f"FBA inventory check failed for {sku}: {e}")
            # Return safe default on any failure
            return {
                'sellerSku': sku,
                'fulfillableQuantity': 0,
                'inboundQuantity': 0,
                'reservedQuantity': 0,
                'error': str(e)
            }

    def _process_fba_response(self, sku, response):
        """Process FBA API response and extract inventory data for specific SKU"""
        # Check if we got an expected error response
        if '_status_code' in response:
            if response['_status_code'] in [400, 404]:
                # SKU not found in FBA inventory - treat as safe for deletion
                logger.debug(f"SKU {sku} not found in FBA inventory (status {response['_status_code']}) - safe for deletion")
                return {
                    'sellerSku': sku,
                    'fulfillableQuantity': 0,
                    'inboundQuantity': 0,
                    'reservedQuantity': 0
                }

        # Extract inventory information from successful response
        payload = response.get('payload', {})
        inventory_summaries = payload.get('inventorySummaries', [])

        logger.info(f"FBA response for {sku} contains {len(inventory_summaries)} inventory summaries")

        if inventory_summaries:
            # Find the specific SKU in the response
            inventory = None
            for summary in inventory_summaries:
                if summary.get('sellerSku') == sku:
                    inventory = summary
                    logger.info(f"Successfully matched SKU '{sku}' in response")
                    break

            if inventory:
                # Use detailed inventory information if available
                inventory_details = inventory.get('inventoryDetails', {})

                result = {
                    'sellerSku': inventory.get('sellerSku', ''),
                    'asin': inventory.get('asin', ''),
                    'productName': inventory.get('productName', ''),
                    'condition': inventory.get('condition', ''),
                    'totalQuantity': inventory.get('totalQuantity', 0),
                    'lastUpdatedTime': inventory.get('lastUpdatedTime', '')
                }

                # Extract detailed inventory quantities
                if inventory_details:
                    result.update({
                        'fulfillableQuantity': inventory_details.get('fulfillableQuantity', 0),
                        'inboundWorkingQuantity': inventory_details.get('inboundWorkingQuantity', 0),
                        'inboundShippedQuantity': inventory_details.get('inboundShippedQuantity', 0),
                        'inboundReceivingQuantity': inventory_details.get('inboundReceivingQuantity', 0),
                        'reservedQuantity': inventory_details.get('reservedQuantity', {}).get('totalReservedQuantity', 0),
                        'unfulfillableQuantity': inventory_details.get('unfulfillableQuantity', {}).get('totalUnfulfillableQuantity', 0)
                    })
                else:
                    # Fallback to basic quantities if details not available
                    result.update({
                        'fulfillableQuantity': inventory.get('fulfillableQuantity', 0),
                        'inboundQuantity': inventory.get('inboundQuantity', 0),
                        'reservedQuantity': inventory.get('reservedQuantity', 0)
                    })

                logger.debug(f"SKU {sku} FBA inventory: fulfillable={result['fulfillableQuantity']}, inbound={result.get('inboundWorkingQuantity', 0)}")
                return result
            else:
                # SKU not found in response - treat as no inventory
                logger.warning(f"SKU {sku} not found in FBA inventory response")
                return {
                    'sellerSku': sku,
                    'fulfillableQuantity': 0,
                    'inboundQuantity': 0,
                    'reservedQuantity': 0
                }
        else:
            # No inventory found
            logger.debug(f"No inventory data found for SKU {sku}")
            return {
                'sellerSku': sku,
                'fulfillableQuantity': 0,
                'inboundQuantity': 0,
                'reservedQuantity': 0
            }

    def check_listing_inventory(self, sku: str) -> Dict:
        """Check listing inventory using Listings API as alternative to FBA Inventory API"""
        endpoint = f"/listings/2021-08-01/items/{self.credentials.seller_id}/{sku}"

        params = {
            'marketplaceIds': [self.credentials.marketplace_id],
            'includedData': 'summaries,fulfillmentAvailability'
        }

        try:
            response = self._make_api_request('GET', endpoint, params=params)

            # Extract fulfillment availability information
            fulfillment_availability = response.get('fulfillmentAvailability', [])

            total_quantity = 0
            fba_quantity = 0

            for fulfillment in fulfillment_availability:
                quantity = fulfillment.get('quantity', 0)
                total_quantity += quantity

                # Check if this is FBA fulfillment
                fulfillment_code = fulfillment.get('fulfillmentChannelCode', '')
                if fulfillment_code in ['AMAZON', 'DEFAULT']:  # DEFAULT often means FBA
                    fba_quantity += quantity

            return {
                'sellerSku': sku,
                'total_quantity': total_quantity,
                'fba_quantity': fba_quantity,
                'fulfillment_availability': fulfillment_availability,
                'has_inventory': total_quantity > 0
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [400, 404]:
                # SKU not found in listings (may already be deleted or never existed)
                logger.info(f"SKU {sku}: Not found in listings (status {e.response.status_code}) - safe for deletion")
                return {
                    'sellerSku': sku,
                    'total_quantity': 0,
                    'fba_quantity': 0,
                    'fulfillment_availability': [],
                    'has_inventory': False
                }
            else:
                logger.error(f"Listing check failed for {sku} (status {e.response.status_code}): {e}")
                logger.debug(f"Listing check error details - URL: {e.response.url}, Headers: {dict(e.response.headers)}")
                # For safety, assume has inventory if API fails
                return {
                    'sellerSku': sku,
                    'total_quantity': 999,  # High number to be conservative
                    'fba_quantity': 999,
                    'fulfillment_availability': [],
                    'has_inventory': True,
                    'error': str(e)
                }

    def delete_sku(self, sku: str) -> Dict:
        """Delete a SKU using Listings API"""
        endpoint = f"/listings/2021-08-01/items/{self.credentials.seller_id}/{sku}"

        params = {
            'marketplaceIds': [self.credentials.marketplace_id]
        }

        try:
            logger.info(f"Sending DELETE request for SKU: {sku} to endpoint: {endpoint}")
            response = self._make_api_request('DELETE', endpoint, params=params)
            logger.info(f"DELETE API response for {sku}: {response}")

            # Check if response indicates success
            if response.get('status') == 'ACCEPTED':
                logger.info(f"✅ SKU {sku} deletion accepted by Amazon")
            elif response.get('status') == 'INVALID':
                logger.warning(f"❌ SKU {sku} deletion rejected as invalid: {response.get('issues', [])}")
            else:
                logger.warning(f"⚠️ SKU {sku} deletion status unclear: {response.get('status', 'unknown')}")

            return response

        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ DELETE API call failed for {sku}: HTTP {e.response.status_code} - {e.response.text if hasattr(e.response, 'text') else str(e)}")
            if e.response.status_code == 404:
                logger.warning(f"SKU {sku} not found (may already be deleted)")
                return {'sku': sku, 'status': 'not_found'}
            else:
                logger.error(f"Delete failed for {sku}: {e}")
                raise
