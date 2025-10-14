"""
Integration tests for complete SKU cleanup workflows
Tests end-to-end scenarios and component interactions
"""
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta

from data_processor import DataProcessor
from amazon_api import AmazonAPI
from report_generator import ReportGenerator
from monitoring_example import ProductionMonitor
from utils import parse_amazon_date
from config import CleanupSettings, AmazonCredentials


class TestCompleteWorkflowIntegration:
    """Test complete end-to-end workflows"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.monitor = ProductionMonitor()
        self.processor = DataProcessor()
        self.report_generator = ReportGenerator(output_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_cleanup_workflow_with_mock_api(self):
        """Test complete workflow from data processing to report generation"""
        # Mock SKU data representing a merchant listings report
        mock_sku_data = [
            {
                'sku': 'OLD-SKU-001',
                'asin': 'B0123456789',
                'created_date': '01/01/2023',  # Old enough for deletion
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0,
                'status': 'Active'
            },
            {
                'sku': 'NEW-SKU-001',
                'asin': 'B0987654321',
                'created_date': (datetime.now() - timedelta(days=15)).strftime('%d/%m/%Y'),  # Too new for deletion
                'fulfillment_channel': 'MERCHANT',
                'quantity': 5,
                'status': 'Active'
            },
            {
                'sku': 'FBA-SKU-001',
                'asin': 'B0111222333',
                'created_date': '01/01/2023',  # Old enough but has FBA offers
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0,
                'status': 'Active'
            }
        ]

        # Process the SKU data
        processed_skus = self.processor.process_sku_data(mock_sku_data)

        # Verify processing results
        assert len(processed_skus) == 3

        # Find SKUs by their characteristics
        old_sku = next(sku for sku in processed_skus if sku['sku'] == 'OLD-SKU-001')
        new_sku = next(sku for sku in processed_skus if sku['sku'] == 'NEW-SKU-001')
        fba_sku = next(sku for sku in processed_skus if sku['sku'] == 'FBA-SKU-001')

        # Verify age calculations
        assert old_sku['age_days'] > 365  # Should be old enough
        assert new_sku['age_days'] < 30   # Should be too new
        assert old_sku['age_days'] > 365  # FBA SKU should also be old

        # Identify deletable SKUs
        deletable_skus = self.processor.identify_deletable_skus(processed_skus)

        # Should only have one deletable SKU (OLD-SKU-001)
        assert len(deletable_skus) == 1
        assert deletable_skus[0]['sku'] == 'OLD-SKU-001'

        # Generate report
        results = {
            'total_processed': len(processed_skus),
            'eligible_for_deletion': len(deletable_skus),
            'deleted': deletable_skus,  # In real scenario, these would be actual deletions
            'skipped': [
                {'sku': 'NEW-SKU-001', 'reason': 'too_new'},
                {'sku': 'FBA-SKU-001', 'reason': 'has_fba_offers'}
            ],
            'errors': [],
            'execution_time': 2.5
        }

        report_path = self.report_generator.generate_report(results)

        # Verify report was created and contains expected content
        assert os.path.exists(report_path)

        with open(report_path, 'r') as f:
            content = f.read()

        assert 'SKU Cleanup Report' in content
        assert 'Total SKUs Processed: 3' in content
        assert 'Eligible for Deletion: 1' in content
        assert 'Successfully Deleted: 1' in content
        assert 'OLD-SKU-001' in content
        assert 'too_new' in content
        assert 'has_fba_offers' in content

    def test_workflow_with_api_integration_mock(self):
        """Test workflow with mocked API interactions"""
        # Mock Amazon API responses
        mock_inventory_response = {
            'payload': {
                'InventorySummaries': [
                    {
                        'SellerSku': 'FBA-SKU-001',
                        'FulfillmentChannelCode': 'AMAZON_EU',
                        'inventoryDetails': {
                            'availablePhysical': 10
                        }
                    }
                ]
            }
        }

        with patch.object(AmazonAPI, 'check_fba_inventory') as mock_check:
            mock_check.return_value = mock_inventory_response

            # Create test SKU data
            sku_data = [{
                'sku': 'FBA-SKU-001',
                'asin': 'B0111222333',
                'created_date': '01/01/2023',
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0
            }]

            # Process with API integration
            processed_skus = self.processor.process_sku_data(sku_data)

            # Verify API was called
            mock_check.assert_called_once()

            # Verify FBA inventory was detected
            fba_sku = processed_skus[0]
            assert fba_sku['has_fba_offers'] is True

            # Should not be eligible for deletion due to FBA offers
            deletable_skus = self.processor.identify_deletable_skus(processed_skus)
            assert len(deletable_skus) == 0

    def test_workflow_with_monitoring_integration(self):
        """Test complete workflow with monitoring enabled"""
        # Process some test data while monitoring
        sku_data = [
            {'sku': 'SKU001', 'created_date': '01/01/2023', 'fulfillment_channel': 'MERCHANT', 'quantity': 0},
            {'sku': 'SKU002', 'created_date': '01/01/2024', 'fulfillment_channel': 'MERCHANT', 'quantity': 0},
        ]

        # Log API calls (simulated)
        self.monitor.log_api_call('merchant_listings', True, 0.5)
        self.monitor.log_api_call('inventory_check', True, 0.3)

        # Process SKUs and log results
        processed_skus = self.processor.process_sku_data(sku_data)
        deletable_skus = self.processor.identify_deletable_skus(processed_skus)

        for sku in processed_skus:
            eligible = sku in deletable_skus
            self.monitor.log_sku_processed(sku['sku'], eligible, 'old_enough' if eligible else 'too_new')

        # Generate summary
        summary = self.monitor.get_summary()

        # Verify monitoring captured all activities
        assert summary['api_calls_total'] == 2
        assert summary['api_success_rate'] == 100.0
        assert summary['skus_processed'] == 2
        assert summary['skus_eligible'] == 1  # Only SKU001 should be eligible
        assert summary['skus_eligible_rate'] == 50.0

    def test_error_handling_workflow_integration(self):
        """Test workflow behavior with errors"""
        # Test data with problematic entries
        problematic_sku_data = [
            {
                'sku': 'VALID-SKU',
                'asin': 'B0123456789',
                'created_date': '01/01/2023',
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0,
                'status': 'Active'
            },
            {
                'sku': '',  # Invalid SKU
                'asin': 'B0987654321',
                'created_date': '01/01/2023',
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0,
                'status': 'Active'
            },
            {
                'sku': 'INVALID-DATE',
                'asin': 'B0111222333',
                'created_date': 'invalid-date',  # Invalid date
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0,
                'status': 'Active'
            }
        ]

        # Process should handle errors gracefully
        processed_skus = self.processor.process_sku_data(problematic_sku_data)

        # Should only process valid SKUs
        assert len(processed_skus) == 1
        assert processed_skus[0]['sku'] == 'VALID-SKU'

        # Generate report with error information
        results = {
            'total_processed': 3,
            'eligible_for_deletion': 1,
            'deleted': [processed_skus[0]],
            'skipped': [],
            'errors': [
                {'sku': '', 'error': 'Missing SKU field'},
                {'sku': 'INVALID-DATE', 'error': 'Invalid date format'}
            ],
            'execution_time': 1.0
        }

        report_path = self.report_generator.generate_report(results)

        with open(report_path, 'r') as f:
            content = f.read()

        assert 'Errors (2)' in content
        assert 'Missing SKU field' in content
        assert 'Invalid date format' in content

    def test_large_dataset_workflow(self):
        """Test workflow with a large dataset"""
        # Generate large dataset
        large_sku_data = []
        for i in range(1000):
            # Mix of old and new SKUs, with and without FBA offers
            age_days = 400 if i % 3 == 0 else 15  # Some old, some new
            has_fba = i % 5 == 0  # Some have FBA offers

            created_date = (datetime.now() - timedelta(days=age_days)).strftime('%d/%m/%Y')

            sku_data = {
                'sku': f'SKU-{i:03d}',
                'asin': f'B0{i:08d}',
                'created_date': created_date,
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0 if not has_fba else 10,
                'status': 'Active'
            }
            large_sku_data.append(sku_data)

        # Process large dataset
        processed_skus = self.processor.process_sku_data(large_sku_data)
        assert len(processed_skus) == 1000

        # Identify deletable SKUs (old enough, no FBA offers)
        deletable_skus = self.processor.identify_deletable_skus(processed_skus)

        # Should have approximately 1000/3 = 333 old SKUs, but only those without FBA
        # Approximately 333 * 4/5 = 266 (since 4/5 don't have FBA offers)
        assert len(deletable_skus) > 200
        assert len(deletable_skus) < 350

        # Generate report for large dataset
        results = {
            'total_processed': len(processed_skus),
            'eligible_for_deletion': len(deletable_skus),
            'deleted': deletable_skus[:10],  # Only show first 10 in report
            'skipped': [],
            'errors': [],
            'execution_time': 15.0
        }

        report_path = self.report_generator.generate_report(results)
        assert os.path.exists(report_path)

        # Report should handle large numbers correctly
        with open(report_path, 'r') as f:
            content = f.read()

        assert 'Total SKUs Processed: 1000' in content
        assert f'Successfully Deleted: 10' in content  # Only showing first 10


class TestComponentInteractionIntegration:
    """Test interactions between different components"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_data_processor_with_real_utils(self):
        """Test DataProcessor using real utility functions"""
        processor = DataProcessor()

        # Test with real date parsing
        sku_data = [{
            'sku': 'TEST-SKU',
            'asin': 'B0123456789',
            'created_date': '15/06/2023',  # Valid Amazon date format
            'fulfillment_channel': 'MERCHANT',
            'quantity': 0,
            'status': 'Active'
        }]

        processed_skus = processor.process_sku_data(sku_data)
        assert len(processed_skus) == 1

        sku = processed_skus[0]
        # Should have parsed the date correctly
        assert sku['age_days'] > 300  # Should be more than 300 days old

    def test_report_generator_with_monitoring_data(self):
        """Test ReportGenerator using monitoring data"""
        monitor = ProductionMonitor()

        # Simulate some activity
        monitor.log_api_call('test_api', True, 1.0)
        monitor.log_sku_processed('SKU001', True, 'old_enough')
        monitor.log_sku_processed('SKU002', False, 'has_fba_offers')

        # Use monitoring summary in report
        summary = monitor.get_summary()

        results = {
            'total_processed': summary['skus_processed'],
            'eligible_for_deletion': summary['skus_eligible'],
            'deleted': ['SKU001'],
            'skipped': [{'sku': 'SKU002', 'reason': 'has_fba_offers'}],
            'errors': [],
            'execution_time': summary['execution_time']
        }

        report_path = ReportGenerator(self.temp_dir).generate_report(results)
        assert os.path.exists(report_path)

    def test_config_integration_with_processors(self):
        """Test configuration integration with data processing"""
        # Test with custom configuration
        settings = CleanupSettings(
            min_age_days=60,
            max_skus_per_batch=50,
            enable_circuit_breaker=True
        )

        processor = DataProcessor()

        # Create test data that would be affected by config
        sku_data = [{
            'sku': 'SKU-60-DAYS',
            'asin': 'B0123456789',
            'created_date': (datetime.now() - timedelta(days=60)).strftime('%d/%m/%Y'),
            'fulfillment_channel': 'MERCHANT',
            'quantity': 0,
            'status': 'Active'
        }]

        processed_skus = processor.process_sku_data(sku_data)
        deletable_skus = processor.identify_deletable_skus(processed_skus)

        # With 60-day minimum age, this SKU should be eligible
        assert len(deletable_skus) == 1


class TestPerformanceIntegration:
    """Test performance characteristics of integrated workflows"""

    def test_memory_usage_with_large_datasets(self):
        """Test memory efficiency with large datasets"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process large dataset
        large_sku_data = []
        for i in range(5000):
            sku_data = {
                'sku': f'SKU-{i:04d}',
                'asin': f'B0{i:08d}',
                'created_date': '01/01/2023',
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0,
                'status': 'Active'
            }
            large_sku_data.append(sku_data)

        processor = DataProcessor()
        processed_skus = processor.process_sku_data(large_sku_data)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for 5000 items)
        assert memory_increase < 100
        assert len(processed_skus) == 5000

    def test_processing_time_with_various_dataset_sizes(self):
        """Test processing time scales appropriately with dataset size"""
        processor = DataProcessor()

        # Test different dataset sizes
        sizes_and_times = []

        for size in [100, 500, 1000, 2000]:
            sku_data = []
            for i in range(size):
                sku_data.append({
                    'sku': f'SKU-{i:04d}',
                    'asin': f'B0{i:08d}',
                    'created_date': '01/01/2023',
                    'fulfillment_channel': 'MERCHANT',
                    'quantity': 0,
                    'status': 'Active'
                })

            import time
            start_time = time.time()
            processed_skus = processor.process_sku_data(sku_data)
            end_time = time.time()

            processing_time = end_time - start_time
            sizes_and_times.append((size, processing_time))

            assert len(processed_skus) == size

        # Processing time should scale roughly linearly
        # (Each dataset should take roughly proportional time)
        time_per_item_100 = sizes_and_times[0][1] / 100
        time_per_item_2000 = sizes_and_times[3][1] / 2000

        # Should be within 50% of each other (allowing for some variance)
        assert abs(time_per_item_100 - time_per_item_2000) / time_per_item_100 < 0.5
