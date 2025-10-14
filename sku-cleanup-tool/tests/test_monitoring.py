"""
Tests for monitoring functionality in monitoring_example.py
"""
import pytest
import time
from unittest.mock import patch

from monitoring_example import ProductionMonitor


class TestProductionMonitor:
    """Test ProductionMonitor class functionality"""

    def test_init(self):
        """Test ProductionMonitor initialization"""
        monitor = ProductionMonitor()

        assert monitor.metrics == {}
        assert monitor.start_time > 0
        assert isinstance(monitor.start_time, float)

    def test_log_api_call_success(self):
        """Test logging successful API calls"""
        monitor = ProductionMonitor()

        monitor.log_api_call('merchant_listings', True, 0.5)

        assert monitor.metrics['api_merchant_listings_calls'] == 1
        assert monitor.metrics['api_merchant_listings_success'] == 1
        assert monitor.metrics['api_merchant_listings_latency'] == 0.5

    def test_log_api_call_failure(self):
        """Test logging failed API calls"""
        monitor = ProductionMonitor()

        monitor.log_api_call('inventory_check', False, 2.0)

        assert monitor.metrics['api_inventory_check_calls'] == 1
        assert monitor.metrics['api_inventory_check_success'] == 0
        assert monitor.metrics['api_inventory_check_latency'] == 2.0

    def test_log_multiple_api_calls(self):
        """Test logging multiple API calls"""
        monitor = ProductionMonitor()

        # Log several calls
        monitor.log_api_call('merchant_listings', True, 0.3)
        monitor.log_api_call('merchant_listings', True, 0.4)
        monitor.log_api_call('inventory_check', False, 1.0)
        monitor.log_api_call('inventory_check', True, 0.8)

        assert monitor.metrics['api_merchant_listings_calls'] == 2
        assert monitor.metrics['api_merchant_listings_success'] == 2
        assert monitor.metrics['api_merchant_listings_latency'] == 0.7

        assert monitor.metrics['api_inventory_check_calls'] == 2
        assert monitor.metrics['api_inventory_check_success'] == 1
        assert monitor.metrics['api_inventory_check_latency'] == 1.8

    def test_log_sku_processed_eligible(self):
        """Test logging eligible SKUs"""
        monitor = ProductionMonitor()

        monitor.log_sku_processed('SKU001', True, 'old_enough')

        assert monitor.metrics['skus_processed'] == 1
        assert monitor.metrics['skus_eligible'] == 1

    def test_log_sku_processed_not_eligible(self):
        """Test logging non-eligible SKUs"""
        monitor = ProductionMonitor()

        monitor.log_sku_processed('SKU002', False, 'has_fba_offers')

        assert monitor.metrics['skus_processed'] == 1
        assert monitor.metrics['skus_eligible'] == 0
        assert monitor.metrics['skus_not_eligible_has_fba_offers'] == 1

    def test_log_sku_processed_no_reason(self):
        """Test logging SKU without specific reason"""
        monitor = ProductionMonitor()

        monitor.log_sku_processed('SKU003', False)

        assert monitor.metrics['skus_processed'] == 1
        assert monitor.metrics['skus_eligible'] == 0
        assert monitor.metrics['skus_not_eligible_other'] == 1

    def test_log_multiple_skus(self):
        """Test logging multiple SKUs with different statuses"""
        monitor = ProductionMonitor()

        # Process various SKUs
        monitor.log_sku_processed('SKU001', True, 'old_enough')
        monitor.log_sku_processed('SKU002', False, 'has_fba_offers')
        monitor.log_sku_processed('SKU003', False, 'too_new')
        monitor.log_sku_processed('SKU004', True, 'old_enough')
        monitor.log_sku_processed('SKU005', False)  # No reason

        assert monitor.metrics['skus_processed'] == 5
        assert monitor.metrics['skus_eligible'] == 2
        assert monitor.metrics['skus_not_eligible_has_fba_offers'] == 1
        assert monitor.metrics['skus_not_eligible_too_new'] == 1
        assert monitor.metrics['skus_not_eligible_other'] == 1

    def test_get_summary_basic(self):
        """Test basic summary generation"""
        monitor = ProductionMonitor()

        # Add some metrics
        monitor.log_api_call('test_endpoint', True, 1.0)
        monitor.log_sku_processed('SKU001', True)

        summary = monitor.get_summary()

        assert 'execution_time' in summary
        assert 'api_calls_total' in summary
        assert 'api_success_rate' in summary
        assert 'skus_processed' in summary
        assert 'skus_eligible' in summary
        assert 'skus_eligible_rate' in summary

        assert summary['api_calls_total'] == 1
        assert summary['api_success_rate'] == 100.0
        assert summary['skus_processed'] == 1
        assert summary['skus_eligible'] == 1
        assert summary['skus_eligible_rate'] == 100.0

    def test_get_summary_no_data(self):
        """Test summary generation with no data"""
        monitor = ProductionMonitor()

        summary = monitor.get_summary()

        assert summary['execution_time'] >= 0
        assert summary['api_calls_total'] == 0
        assert summary['api_success_rate'] == 0.0  # 0/1 * 100 when no calls
        assert summary['skus_processed'] == 0
        assert summary['skus_eligible'] == 0
        assert summary['skus_eligible_rate'] == 0.0

    def test_get_summary_mixed_success_rate(self):
        """Test summary with mixed API success rates"""
        monitor = ProductionMonitor()

        # 3 calls: 2 successful, 1 failed
        monitor.log_api_call('endpoint1', True, 0.5)
        monitor.log_api_call('endpoint1', True, 0.3)
        monitor.log_api_call('endpoint1', False, 1.0)

        summary = monitor.get_summary()

        assert summary['api_calls_total'] == 3
        assert summary['api_success_rate'] == (2/3) * 100  # 66.67%

    def test_get_summary_partial_eligibility(self):
        """Test summary with partial SKU eligibility"""
        monitor = ProductionMonitor()

        # 4 SKUs: 3 eligible, 1 not eligible
        monitor.log_sku_processed('SKU001', True)
        monitor.log_sku_processed('SKU002', True)
        monitor.log_sku_processed('SKU003', True)
        monitor.log_sku_processed('SKU004', False, 'has_fba_offers')

        summary = monitor.get_summary()

        assert summary['skus_processed'] == 4
        assert summary['skus_eligible'] == 3
        assert summary['skus_eligible_rate'] == 75.0  # 3/4 * 100

    def test_calculate_success_rate_no_calls(self):
        """Test success rate calculation with no API calls"""
        monitor = ProductionMonitor()

        # Test the private method indirectly through get_summary
        summary = monitor.get_summary()
        assert summary['api_success_rate'] == 0.0

    def test_calculate_success_rate_all_success(self):
        """Test success rate calculation with all successful calls"""
        monitor = ProductionMonitor()

        monitor.log_api_call('endpoint1', True, 0.5)
        monitor.log_api_call('endpoint2', True, 0.3)

        summary = monitor.get_summary()
        assert summary['api_success_rate'] == 100.0

    def test_calculate_success_rate_all_failures(self):
        """Test success rate calculation with all failed calls"""
        monitor = ProductionMonitor()

        monitor.log_api_call('endpoint1', False, 1.0)
        monitor.log_api_call('endpoint2', False, 2.0)

        summary = monitor.get_summary()
        assert summary['api_success_rate'] == 0.0

    def test_execution_time_calculation(self):
        """Test that execution time is calculated correctly"""
        monitor = ProductionMonitor()

        # Small delay to ensure measurable time difference
        time.sleep(0.01)

        summary = monitor.get_summary()
        assert summary['execution_time'] > 0

        # Should be approximately the time since monitor creation
        assert 0.005 <= summary['execution_time'] <= 1.0  # Reasonable bounds


class TestProductionMonitorIntegration:
    """Test integration scenarios"""

    def test_realistic_workflow_simulation(self):
        """Test a realistic workflow scenario"""
        monitor = ProductionMonitor()

        # Simulate a typical workflow
        # API calls
        monitor.log_api_call('merchant_listings', True, 0.8)
        monitor.log_api_call('inventory_check', True, 0.6)
        monitor.log_api_call('inventory_check', False, 2.0)  # One failure

        # SKU processing
        skus = [
            ('SKU001', True, 'old_enough'),
            ('SKU002', False, 'has_fba_offers'),
            ('SKU003', True, 'old_enough'),
            ('SKU004', False, 'too_new'),
            ('SKU005', True, 'old_enough'),
        ]

        for sku, eligible, reason in skus:
            monitor.log_sku_processed(sku, eligible, reason)

        summary = monitor.get_summary()

        # Verify totals
        assert summary['api_calls_total'] == 3
        assert summary['api_success_rate'] == (2/3) * 100  # 2 successes out of 3
        assert summary['skus_processed'] == 5
        assert summary['skus_eligible'] == 3
        assert summary['skus_eligible_rate'] == 60.0  # 3/5 * 100

    def test_monitor_with_time_delay(self):
        """Test monitor behavior over time"""
        monitor = ProductionMonitor()

        start_time = time.time()

        # Add some initial metrics
        monitor.log_api_call('test', True, 0.1)
        monitor.log_sku_processed('SKU001', True)

        # Wait a bit
        time.sleep(0.05)

        summary = monitor.get_summary()

        # Execution time should be greater than the delay
        assert summary['execution_time'] >= 0.04

        # But should be based on monitor start time, not this function's start time
        assert summary['execution_time'] > 0

    def test_monitor_reset_behavior(self):
        """Test that creating a new monitor resets metrics"""
        # First monitor
        monitor1 = ProductionMonitor()
        monitor1.log_api_call('test', True, 0.1)
        monitor1.log_sku_processed('SKU001', True)

        # Second monitor should start fresh
        monitor2 = ProductionMonitor()
        summary2 = monitor2.get_summary()

        assert summary2['api_calls_total'] == 0
        assert summary2['skus_processed'] == 0

    def test_monitor_with_large_numbers(self):
        """Test monitor with large numbers of operations"""
        monitor = ProductionMonitor()

        # Simulate processing many SKUs
        for i in range(1000):
            eligible = i % 3 == 0  # Every 3rd SKU is eligible
            monitor.log_sku_processed(f'SKU{i:03d}', eligible)

        # Add some API calls
        for i in range(100):
            success = i % 10 != 0  # 90% success rate
            monitor.log_api_call('batch_api', success, 0.1)

        summary = monitor.get_summary()

        assert summary['skus_processed'] == 1000
        assert summary['skus_eligible'] == 334  # 1000/3 ≈ 333.33, rounds to 334?
        assert summary['skus_eligible_rate'] == 33.4  # Approximately 33.4%

        assert summary['api_calls_total'] == 100
        assert summary['api_success_rate'] == 90.0  # 90% success rate
