"""
Unit tests for data processing logic
Tests SKU data validation, age calculation, and deletion eligibility
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from data_processor import DataProcessor


class TestDataProcessor:
    """Test data processing functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.processor = DataProcessor()
        # Mock the amazon_api to avoid actual API calls
        self.mock_api = Mock()
        self.processor.amazon_api = self.mock_api

    def test_process_empty_sku_list(self):
        """Test processing empty SKU list"""
        result = self.processor.process_sku_data([])
        assert result == []

    def test_process_sku_with_missing_sku_field(self):
        """Test processing SKU with missing SKU field"""
        sku_data = [{'created_date': '01/01/2020', 'fulfillment_channel': 'AMAZON'}]
        result = self.processor.process_sku_data(sku_data)

        # Should skip invalid SKUs
        assert len(result) == 0

    def test_process_valid_sku_basic(self):
        """Test processing a valid SKU with basic data"""
        # Create SKU data that's old enough for deletion (use DD/MM/YYYY format as expected by parser)
        old_date = datetime.now() - timedelta(days=60)
        sku_data = [{
            'sku': 'TEST-SKU-001',
            'created_date': old_date.strftime('%d/%m/%Y'),
            'fulfillment_channel': 'AMAZON'
        }]

        # Mock FBA API to return no inventory (returns safe defaults)
        self.mock_api.check_fba_inventory.return_value = {
            'sellerSku': 'TEST-SKU-001',
            'fulfillableQuantity': 0,
            'inboundQuantity': 0,
            'reservedQuantity': 0
        }

        result = self.processor.process_sku_data(sku_data)

        assert len(result) == 1
        processed_sku = result[0]
        assert processed_sku['sku'] == 'TEST-SKU-001'
        assert processed_sku['is_eligible_for_deletion'] is True
        assert processed_sku['age_days'] >= 30
        assert 'fba_inventory_check' in processed_sku

    def test_process_sku_with_fba_inventory(self):
        """Test processing SKU that has FBA inventory"""
        old_date = datetime.now() - timedelta(days=60)
        sku_data = [{
            'sku': 'TEST-SKU-WITH-INVENTORY',
            'created_date': old_date.strftime('%d/%m/%Y'),
            'fulfillment_channel': 'AMAZON'
        }]

        # Mock FBA API to return inventory
        self.mock_api.check_fba_inventory.return_value = {
            'sellerSku': 'TEST-SKU-WITH-INVENTORY',
            'fulfillableQuantity': 5,
            'inboundQuantity': 0,
            'reservedQuantity': 0
        }

        result = self.processor.process_sku_data(sku_data)

        assert len(result) == 1
        processed_sku = result[0]
        assert processed_sku['sku'] == 'TEST-SKU-WITH-INVENTORY'
        assert processed_sku['is_eligible_for_deletion'] is False  # Has inventory
        assert processed_sku['fba_inventory_check']['fulfillable_quantity'] == 5
        assert processed_sku['fba_inventory_check']['has_inventory'] is True

    def test_process_sku_too_young(self):
        """Test processing SKU that's too young for deletion"""
        young_date = datetime.now() - timedelta(days=15)  # Less than 30 days
        sku_data = [{
            'sku': 'YOUNG-SKU',
            'created_date': young_date.strftime('%d/%m/%Y'),
            'fulfillment_channel': 'AMAZON'
        }]

        self.mock_api.check_fba_inventory.return_value = {
            'inventory': [],
            'error': None,
            'error_type': None
        }

        result = self.processor.process_sku_data(sku_data)

        assert len(result) == 1
        processed_sku = result[0]
        assert processed_sku['is_eligible_for_deletion'] is False  # Too young
        assert processed_sku['age_days'] < 30
        assert 'fba_inventory_check' in processed_sku

    def test_process_mixed_fulfillment_channels(self):
        """Test processing SKUs with different fulfillment channels"""
        old_date = datetime.now() - timedelta(days=60)
        sku_data = [
            {
                'sku': 'AMAZON-SKU',
                'created_date': old_date.strftime('%d/%m/%Y'),
                'fulfillment_channel': 'AMAZON'
            },
            {
                'sku': 'MERCHANT-SKU',
                'created_date': old_date.strftime('%d/%m/%Y'),
                'fulfillment_channel': 'MERCHANT'
            }
        ]

        self.mock_api.check_fba_inventory.return_value = {
            'sellerSku': 'AMAZON-SKU',
            'fulfillableQuantity': 0,
            'inboundQuantity': 0,
            'reservedQuantity': 0
        }

        result = self.processor.process_sku_data(sku_data)

        assert len(result) == 2

        # Amazon SKU should be eligible (after FBA check)
        amazon_sku = next(sku for sku in result if sku['sku'] == 'AMAZON-SKU')
        assert amazon_sku['fulfillment_channel'] == 'AMAZON'

        # Merchant SKU should not need FBA check
        merchant_sku = next(sku for sku in result if sku['sku'] == 'MERCHANT-SKU')
        assert merchant_sku['fulfillment_channel'] == 'MERCHANT'
        # Merchant SKUs don't get FBA checks (only Amazon fulfillment channels do)
        assert merchant_sku['listing_inventory_check'] == 'not_applicable'

    def test_age_calculation(self):
        """Test SKU age calculation accuracy"""
        # Test exact 30-day boundary
        thirty_days_ago = datetime.now() - timedelta(days=30)
        sku_data = [{
            'sku': 'EXACTLY-30-DAYS',
            'created_date': thirty_days_ago.strftime('%d/%m/%Y'),
            'fulfillment_channel': 'AMAZON'
        }]

        self.mock_api.check_fba_inventory.return_value = {
            'sellerSku': 'EXACTLY-30-DAYS',
            'fulfillableQuantity': 0,
            'inboundQuantity': 0,
            'reservedQuantity': 0
        }

        result = self.processor.process_sku_data(sku_data)
        assert result[0]['age_days'] >= 30

    def test_error_handling_in_processing(self):
        """Test error handling during SKU processing"""
        sku_data = [{
            'sku': 'ERROR-SKU',
            'created_date': 'invalid-date',
            'fulfillment_channel': 'AMAZON'
        }]

        # Should not raise an exception, should handle gracefully
        result = self.processor.process_sku_data(sku_data)

        # Should either skip the SKU or mark it appropriately
        assert len(result) <= 1
        if result:
            # If processed, should indicate the error
            assert 'error' in result[0] or not result[0]['is_eligible_for_deletion']


class TestDataProcessorIntegration:
    """Integration tests for data processor with real dependencies"""

    def test_processor_with_real_api_mock(self):
        """Test processor with realistic API behavior"""
        processor = DataProcessor()

        # Simulate API failure
        processor.amazon_api = Mock()
        processor.amazon_api.check_fba_inventory.side_effect = Exception("API Error")

        sku_data = [{
            'sku': 'API-ERROR-SKU',
            'created_date': '01/01/2020',
            'fulfillment_channel': 'AMAZON'
        }]

        result = processor.process_sku_data(sku_data)

        # Should handle API error gracefully
        assert len(result) == 1
        assert result[0]['is_eligible_for_deletion'] is False  # Conservative approach
        assert 'error' in result[0]['fba_inventory_check']
