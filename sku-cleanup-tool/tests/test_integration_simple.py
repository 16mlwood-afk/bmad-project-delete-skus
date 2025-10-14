"""
Simplified integration tests for complete SKU cleanup workflows
Tests end-to-end scenarios and component interactions
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta

from data_processor import DataProcessor
from report_generator import ReportGenerator
from monitoring_example import ProductionMonitor


class TestSimpleWorkflowIntegration:
    """Test complete end-to-end workflows with simplified scenarios"""

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

    def test_basic_cleanup_workflow(self):
        """Test basic workflow from data processing to report generation"""
        # Simple test data
        sku_data = [
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
                'created_date': (datetime.now() - timedelta(days=15)).strftime('%d/%m/%Y'),  # Too new
                'fulfillment_channel': 'MERCHANT',
                'quantity': 5,
                'status': 'Active'
            }
        ]

        # Process the SKU data
        processed_skus = self.processor.process_sku_data(sku_data)
        assert len(processed_skus) == 2

        # Identify deletable SKUs
        deletable_skus = self.processor.identify_deletable_skus(processed_skus)
        assert len(deletable_skus) == 1
        assert deletable_skus[0]['sku'] == 'OLD-SKU-001'

        # Generate report
        results = {
            'total_processed': len(processed_skus),
            'eligible_for_deletion': len(deletable_skus),
            'deleted': deletable_skus,
            'skipped': [
                {'sku': 'NEW-SKU-001', 'reason': 'too_new'}
            ],
            'errors': [],
            'execution_time': 2.5
        }

        report_path = self.report_generator.generate_report(results)
        assert os.path.exists(report_path)

        with open(report_path, 'r') as f:
            content = f.read()

        assert 'SKU Cleanup Report' in content
        assert '**Total SKUs Processed:** 2' in content
        assert '**Eligible for Deletion:** 1' in content

    def test_workflow_with_monitoring(self):
        """Test workflow with monitoring enabled"""
        # Process some test data while monitoring
        sku_data = [
            {'sku': 'SKU001', 'created_date': '01/01/2023', 'fulfillment_channel': 'MERCHANT', 'quantity': 0},
            {'sku': 'SKU002', 'created_date': (datetime.now() - timedelta(days=15)).strftime('%d/%m/%Y'), 'fulfillment_channel': 'MERCHANT', 'quantity': 0},
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

    def test_error_handling_workflow(self):
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
            }
        ]

        # Process should handle errors gracefully
        processed_skus = self.processor.process_sku_data(problematic_sku_data)

        # Should only process valid SKUs (1 valid, 1 with empty SKU gets skipped)
        assert len(processed_skus) == 1
        assert processed_skus[0]['sku'] == 'VALID-SKU'

    def test_component_interaction(self):
        """Test interactions between different components"""
        # Test with real utility functions
        sku_data = [{
            'sku': 'TEST-SKU',
            'asin': 'B0123456789',
            'created_date': '15/06/2023',  # Valid Amazon date format
            'fulfillment_channel': 'MERCHANT',
            'quantity': 0,
            'status': 'Active'
        }]

        processed_skus = self.processor.process_sku_data(sku_data)
        assert len(processed_skus) == 1

        sku = processed_skus[0]
        # Should have parsed the date correctly and calculated age
        assert sku['age_days'] > 300  # Should be more than 300 days old

    def test_performance_with_medium_dataset(self):
        """Test performance with a medium-sized dataset"""
        # Generate medium dataset (not too large to avoid slow tests)
        sku_data = []
        for i in range(100):
            # Mix of old and new SKUs
            age_days = 400 if i % 3 == 0 else 15
            created_date = (datetime.now() - timedelta(days=age_days)).strftime('%d/%m/%Y')

            sku_data.append({
                'sku': f'SKU-{i:03d}',
                'asin': f'B0{i:08d}',
                'created_date': created_date,
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0,
                'status': 'Active'
            })

        # Process dataset
        processed_skus = self.processor.process_sku_data(sku_data)
        assert len(processed_skus) == 100

        # Identify deletable SKUs
        deletable_skus = self.processor.identify_deletable_skus(processed_skus)

        # Should have approximately 100/3 = 33 old SKUs
        assert len(deletable_skus) > 25
        assert len(deletable_skus) < 45

        # Generate report
        results = {
            'total_processed': len(processed_skus),
            'eligible_for_deletion': len(deletable_skus),
            'deleted': deletable_skus[:5],  # Only show first 5 in report
            'skipped': [],
            'errors': [],
            'execution_time': 5.0
        }

        report_path = self.report_generator.generate_report(results)
        assert os.path.exists(report_path)

        # Verify report content
        with open(report_path, 'r') as f:
            content = f.read()

        assert '**Total SKUs Processed:** 100' in content
        assert f'**Successfully Deleted:** 5' in content
