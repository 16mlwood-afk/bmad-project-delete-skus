#!/usr/bin/env python3
"""
Production Monitoring Enhancement Example
This shows how to quickly improve confidence with monitoring
"""
import logging
import time
from datetime import datetime
from collections import defaultdict

class ProductionMonitor:
    """Enhanced monitoring for production deployment"""

    def __init__(self):
        self.metrics = defaultdict(int)
        self.start_time = time.time()

    def log_api_call(self, endpoint: str, success: bool, response_time: float):
        """Log API call metrics"""
        self.metrics[f'api_{endpoint}_calls'] += 1
        self.metrics[f'api_{endpoint}_success'] += 1 if success else 0
        self.metrics[f'api_{endpoint}_latency'] += response_time

    def log_sku_processed(self, sku: str, eligible: bool, reason: str = None):
        """Log SKU processing metrics"""
        self.metrics['skus_processed'] += 1
        if eligible:
            self.metrics['skus_eligible'] += 1
        else:
            self.metrics[f'skus_not_eligible_{reason or "other"}'] += 1

    def get_summary(self) -> dict:
        """Get monitoring summary"""
        execution_time = time.time() - self.start_time

        return {
            'execution_time': execution_time,
            'api_calls_total': sum(v for k, v in self.metrics.items() if k.endswith('_calls')),
            'api_success_rate': self._calculate_success_rate(),
            'skus_processed': self.metrics['skus_processed'],
            'skus_eligible': self.metrics['skus_eligible'],
            'skus_eligible_rate': (self.metrics['skus_eligible'] / max(self.metrics['skus_processed'], 1)) * 100
        }

    def _calculate_success_rate(self) -> float:
        """Calculate overall API success rate"""
        total_calls = sum(v for k, v in self.metrics.items() if k.endswith('_calls'))
        total_success = sum(v for k, v in self.metrics.items() if k.endswith('_success'))

        return (total_success / max(total_calls, 1)) * 100

# Example usage in main.py
def enhanced_main_with_monitoring():
    """Example of how to integrate monitoring"""
    monitor = ProductionMonitor()

    # Your existing code here...
    logger = logging.getLogger(__name__)

    try:
        # API calls with monitoring
        start_time = time.time()
        # api_call_result = amazon_api.get_merchant_listings()
        response_time = time.time() - start_time
        monitor.log_api_call('merchant_listings', True, response_time)

        # SKU processing with monitoring
        # for sku in processed_skus:
        #     monitor.log_sku_processed(sku['sku'], sku['is_eligible_for_deletion'])

        # Final summary
        summary = monitor.get_summary()
        logger.info(f"📊 Execution Summary: {summary}")

        return summary

    except Exception as e:
        logger.error(f"❌ Execution failed: {e}")
        monitor.log_api_call('error', False, 0)
        raise

if __name__ == "__main__":
    summary = enhanced_main_with_monitoring()
    print(f"✅ Enhanced monitoring active: {summary}")
