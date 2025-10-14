"""
Unit tests for Amazon API integration
Tests API calls, error handling, and response parsing
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException, ConnectionError, Timeout

from amazon_api import AmazonAPI


class TestAmazonAPI:
    """Test Amazon API functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.credentials = Mock()
        self.credentials.aws_access_key_id = 'test_key'
        self.credentials.aws_secret_access_key = 'test_secret'
        self.credentials.aws_region = 'us-east-1'

        with patch('boto3.Session'):
            self.api = AmazonAPI(self.credentials)

    def test_api_initialization(self):
        """Test that AmazonAPI initializes correctly"""
        assert self.api.credentials == self.credentials
        assert self.api.session is not None

    @patch('amazon_api.AmazonAPI._make_api_request')
    def test_check_fba_inventory_success(self, mock_request):
        """Test successful FBA inventory check"""
        # Mock successful API response - structure matches actual API response
        mock_response = {
            'payload': {
                'inventorySummaries': [
                    {
                        'sellerSku': 'TEST-SKU',
                        'inventoryDetails': {
                            'fulfillableQuantity': 5,
                            'inboundWorkingQuantity': 0,
                            'inboundShippedQuantity': 0,
                            'inboundReceivingQuantity': 0,
                            'reservedQuantity': {'totalReservedQuantity': 0}
                        }
                    }
                ]
            }
        }
        mock_request.return_value = mock_response

        result = self.api.check_fba_inventory('TEST-SKU')

        mock_request.assert_called_once()
        assert result['sellerSku'] == 'TEST-SKU'
        assert result['fulfillableQuantity'] == 5

    @patch('amazon_api.AmazonAPI._make_api_request')
    def test_check_fba_inventory_empty_response(self, mock_request):
        """Test FBA inventory check with empty response"""
        mock_request.return_value = {'payload': {'inventorySummaries': []}}

        result = self.api.check_fba_inventory('NONEXISTENT-SKU')

        mock_request.assert_called_once()
        # Should return default values for non-existent SKU
        assert result['sellerSku'] == 'NONEXISTENT-SKU'
        assert result['fulfillableQuantity'] == 0

    @patch('amazon_api.AmazonAPI._make_api_request')
    def test_check_fba_inventory_api_error(self, mock_request):
        """Test FBA inventory check with API error"""
        mock_request.side_effect = RequestException("API Error")

        result = self.api.check_fba_inventory('TEST-SKU')

        # When exception occurs, method returns safe defaults
        assert result['sellerSku'] == 'TEST-SKU'
        assert result['fulfillableQuantity'] == 0

    @patch('amazon_api.AmazonAPI._make_api_request')
    def test_check_fba_inventory_rate_limit(self, mock_request):
        """Test FBA inventory check with rate limiting"""
        # Create a mock response that indicates rate limiting
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = RequestException("Too Many Requests")
        mock_request.side_effect = RequestException("Too Many Requests")

        result = self.api.check_fba_inventory('TEST-SKU')

        # Should return safe defaults when rate limited
        assert result['sellerSku'] == 'TEST-SKU'
        assert result['fulfillableQuantity'] == 0

    def test_aws_client_initialization(self):
        """Test AWS client initialization for SP-API"""
        with patch('boto3.client') as mock_client:
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance

            # Create new API instance to trigger AWS client setup
            api = AmazonAPI(self.credentials)

            # Verify boto3 client was created with correct parameters
            mock_client.assert_called_once()
            call_args = mock_client.call_args

            # Check that correct service and credentials were used
            assert call_args[0][0] == 's3'  # SP-API uses S3 for reports
            assert call_args[1]['aws_access_key_id'] == self.credentials.access_key_id
            assert call_args[1]['aws_secret_access_key'] == self.credentials.secret_access_key
            assert call_args[1]['region_name'] == 'us-east-1'

    def test_api_request_method_exists(self):
        """Test that the main API request method exists"""
        # Verify that the main API request method exists and is callable
        assert hasattr(self.api, '_make_api_request')
        assert callable(getattr(self.api, '_make_api_request'))

    def test_response_parsing_robustness(self):
        """Test that response parsing handles various edge cases"""
        # Test with malformed response
        malformed_response = {'payload': 'not a dict'}

        with patch.object(self.api, '_make_api_request') as mock_request:
            mock_request.return_value = malformed_response

            result = self.api.check_fba_inventory('TEST-SKU')

            # Should handle malformed response gracefully and return safe defaults
            assert result['sellerSku'] == 'TEST-SKU'
            assert result['fulfillableQuantity'] == 0


class TestAmazonAPIErrorHandling:
    """Test error handling in Amazon API"""

    def setup_method(self):
        """Set up error handling test fixtures"""
        self.credentials = Mock()
        self.credentials.aws_access_key_id = 'test_key'
        self.credentials.aws_secret_access_key = 'test_secret'
        self.credentials.aws_region = 'us-east-1'

        with patch('boto3.Session'):
            self.api = AmazonAPI(self.credentials)

    def test_network_timeout_handling(self):
        """Test handling of network timeouts"""
        with patch.object(self.api, '_make_api_request') as mock_request:
            mock_request.side_effect = Timeout("Connection timed out")

            result = self.api.check_fba_inventory('TEST-SKU')

            # Should return safe defaults when timeout occurs
            assert result['sellerSku'] == 'TEST-SKU'
            assert result['fulfillableQuantity'] == 0

    def test_connection_error_handling(self):
        """Test handling of connection errors"""
        with patch.object(self.api, '_make_api_request') as mock_request:
            mock_request.side_effect = ConnectionError("Connection failed")

            result = self.api.check_fba_inventory('TEST-SKU')

            # Should return safe defaults when connection fails
            assert result['sellerSku'] == 'TEST-SKU'
            assert result['fulfillableQuantity'] == 0

    def test_authentication_error_handling(self):
        """Test handling of authentication errors"""
        with patch.object(self.api, '_make_api_request') as mock_request:
            auth_error = RequestException("401 Unauthorized")
            mock_request.side_effect = auth_error

            result = self.api.check_fba_inventory('TEST-SKU')

            # Should return safe defaults when authentication fails
            assert result['sellerSku'] == 'TEST-SKU'
            assert result['fulfillableQuantity'] == 0

    def test_server_error_handling(self):
        """Test handling of server errors (5xx)"""
        with patch.object(self.api, '_make_api_request') as mock_request:
            server_error = RequestException("500 Internal Server Error")
            mock_request.side_effect = server_error

            result = self.api.check_fba_inventory('TEST-SKU')

            # Should return safe defaults when server error occurs
            assert result['sellerSku'] == 'TEST-SKU'
            assert result['fulfillableQuantity'] == 0


class TestAmazonAPIBatchOperations:
    """Test batch operations in Amazon API"""

    def setup_method(self):
        """Set up batch operations test fixtures"""
        self.credentials = Mock()
        self.credentials.aws_access_key_id = 'test_key'
        self.credentials.aws_secret_access_key = 'test_secret'
        self.credentials.aws_region = 'us-east-1'

        with patch('boto3.Session'):
            self.api = AmazonAPI(self.credentials)

    def test_multiple_inventory_checks(self):
        """Test checking inventory for multiple SKUs individually"""
        sku_list = ['SKU-001', 'SKU-002', 'SKU-003']

        # Test each SKU individually since the API method handles single SKUs
        results = []
        for sku in sku_list:
            with patch.object(self.api, '_make_api_request') as mock_request:
                mock_response = {
                    'payload': {
                        'inventorySummaries': [
                            {
                                'sellerSku': sku,
                                'inventoryDetails': {
                                    'fulfillableQuantity': 10 if sku != 'SKU-002' else 0,
                                    'inboundWorkingQuantity': 0,
                                    'inboundShippedQuantity': 0,
                                    'inboundReceivingQuantity': 0,
                                    'reservedQuantity': {'totalReservedQuantity': 0}
                                }
                            }
                        ]
                    }
                }
                mock_request.return_value = mock_response
                result = self.api.check_fba_inventory(sku)
                results.append(result)

        # Verify results for each SKU
        assert len(results) == 3
        sku_001_result = next(r for r in results if r['sellerSku'] == 'SKU-001')
        sku_002_result = next(r for r in results if r['sellerSku'] == 'SKU-002')
        sku_003_result = next(r for r in results if r['sellerSku'] == 'SKU-003')

        assert sku_001_result['fulfillableQuantity'] == 10
        assert sku_002_result['fulfillableQuantity'] == 0
        assert sku_003_result['fulfillableQuantity'] == 10
