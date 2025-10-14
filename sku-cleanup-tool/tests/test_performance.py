"""
Performance and load testing for SKU cleanup tool
Tests scalability, memory usage, and processing speed with large datasets
"""
import pytest
import time
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

# Try to import psutil for enhanced monitoring, but make it optional
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from data_processor import DataProcessor
from report_generator import ReportGenerator
from amazon_api import AmazonAPI


class TestPerformanceMetrics:
    """Test performance characteristics and benchmarks"""

    def test_processing_speed_benchmarks(self):
        """Benchmark processing speed for different dataset sizes"""
        processor = DataProcessor()
        benchmarks = []

        # Test various dataset sizes
        sizes = [100, 500, 1000, 2500, 5000]

        for size in sizes:
            # Generate test data
            sku_data = self._generate_test_sku_data(size)

            # Measure processing time
            start_time = time.perf_counter()
            processed_skus = processor.process_sku_data(sku_data)
            end_time = time.perf_counter()

            processing_time = end_time - start_time
            time_per_sku = processing_time / size

            benchmarks.append({
                'size': size,
                'processing_time': processing_time,
                'time_per_sku': time_per_sku,
                'skus_per_second': size / processing_time
            })

            # Verify all SKUs were processed
            assert len(processed_skus) == size

        # Verify performance scaling
        # Processing time should scale roughly linearly with dataset size
        small_time = benchmarks[0]['processing_time']  # 100 SKUs
        large_time = benchmarks[4]['processing_time']  # 5000 SKUs

        # Large dataset should take proportionally more time
        # Allow for some variance in performance (±50%)
        expected_ratio = 5000 / 100  # 50x more data
        actual_ratio = large_time / small_time

        assert 30 <= actual_ratio <= 75, f"Performance scaling issue: expected ~50x, got {actual_ratio}x"

        # Time per SKU should remain relatively consistent
        time_per_sku_small = benchmarks[0]['time_per_sku']
        time_per_sku_large = benchmarks[4]['time_per_sku']

        # Should be within 2x of each other (allowing for optimization effects)
        assert time_per_sku_large < time_per_sku_small * 2

    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available for memory monitoring")
    def test_memory_usage_scaling(self):
        """Test memory usage scales appropriately with dataset size"""
        processor = DataProcessor()

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        sizes = [1000, 2500, 5000]
        memory_usage = []

        for size in sizes:
            # Generate and process data
            sku_data = self._generate_test_sku_data(size)
            processed_skus = processor.process_sku_data(sku_data)

            # Measure memory after processing
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory

            memory_usage.append({
                'size': size,
                'memory_increase_mb': memory_increase,
                'memory_per_sku_mb': memory_increase / size
            })

            # Clean up for next iteration
            del processed_skus
            del sku_data

        # Memory usage should scale roughly linearly
        small_memory = memory_usage[0]['memory_increase_mb']  # 1000 SKUs
        large_memory = memory_usage[2]['memory_increase_mb']  # 5000 SKUs

        expected_ratio = 5000 / 1000  # 5x more data
        actual_ratio = large_memory / small_memory

        # Should be within reasonable bounds (3x to 7x for 5x more data)
        assert 3 <= actual_ratio <= 7, f"Memory scaling issue: expected ~5x, got {actual_ratio}x"

        # Memory per SKU should be reasonable (< 1KB per SKU for 5000 items)
        memory_per_sku = memory_usage[2]['memory_per_sku_mb'] * 1024  # Convert to KB
        assert memory_per_sku < 1.0, f"Excessive memory per SKU: {memory_per_sku}KB"

    def test_concurrent_processing_simulation(self):
        """Test processing performance under concurrent load simulation"""
        processor = DataProcessor()

        # Simulate processing multiple batches concurrently
        batch_size = 100
        num_batches = 10

        start_time = time.perf_counter()

        for batch_num in range(num_batches):
            # Generate batch data
            batch_data = self._generate_test_sku_data(batch_size)

            # Process batch
            processed_skus = processor.process_sku_data(batch_data)

            # Verify batch processing
            assert len(processed_skus) == batch_size

            # Clean up
            del processed_skus
            del batch_data

        total_time = time.perf_counter() - start_time
        total_skus = batch_size * num_batches

        # Calculate throughput
        throughput = total_skus / total_time  # SKUs per second

        # Should achieve reasonable throughput (> 100 SKUs/second)
        assert throughput > 100, f"Low throughput: {throughput} SKUs/second"

    def test_processing_consistency(self):
        """Test that processing performance is consistent across runs"""
        processor = DataProcessor()

        # Run multiple processing iterations with same data
        sku_data = self._generate_test_sku_data(100)
        processing_times = []

        for i in range(5):
            start_time = time.perf_counter()
            processed_skus = processor.process_sku_data(sku_data)
            end_time = time.perf_counter()

            processing_time = end_time - start_time
            processing_times.append(processing_time)

            # Verify consistent results
            assert len(processed_skus) == 100

        # Processing times should be consistent across runs
        avg_time = sum(processing_times) / len(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)

        # Variance should be minimal (< 50% of average)
        variance = (max_time - min_time) / avg_time
        assert variance < 0.5, f"Inconsistent processing times: {variance*100}% variance"

    def _generate_test_sku_data(self, count):
        """Generate test SKU data for performance testing"""
        sku_data = []
        for i in range(count):
            # Mix of old and new SKUs to test various scenarios
            age_days = 400 if i % 3 == 0 else 15  # Some old, some new
            created_date = (datetime.now() - timedelta(days=age_days)).strftime('%d/%m/%Y')

            sku_data.append({
                'sku': f'PERF-SKU-{i:05d}',
                'asin': f'B{i:011d}',
                'created_date': created_date,
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0,
                'status': 'Active'
            })

        return sku_data


class TestLoadTesting:
    """Test system behavior under heavy load"""

    def test_large_dataset_processing(self):
        """Test processing of very large datasets"""
        processor = DataProcessor()

        # Test with large dataset (10,000 SKUs)
        large_dataset_size = 10000
        sku_data = self._generate_large_sku_dataset(large_dataset_size)

        start_time = time.perf_counter()
        processed_skus = processor.process_sku_data(sku_data)
        end_time = time.perf_counter()

        processing_time = end_time - start_time

        # Verify all SKUs processed
        assert len(processed_skus) == large_dataset_size

        # Calculate performance metrics
        throughput = large_dataset_size / processing_time
        time_per_sku = processing_time / large_dataset_size

        # Should achieve reasonable throughput (> 500 SKUs/second for large datasets)
        assert throughput > 500, f"Low throughput for large dataset: {throughput} SKUs/second"

        # Time per SKU should be reasonable (< 2ms per SKU)
        assert time_per_sku < 0.002, f"Slow per-SKU processing: {time_per_sku}s per SKU"

    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available for memory monitoring")
    def test_memory_efficiency_large_dataset(self):
        """Test memory efficiency with large datasets"""
        processor = DataProcessor()

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process large dataset
        large_dataset_size = 10000
        sku_data = self._generate_large_sku_dataset(large_dataset_size)

        processed_skus = processor.process_sku_data(sku_data)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be proportional to dataset size
        # For 10,000 SKUs, memory increase should be < 50MB
        assert memory_increase < 50, f"Excessive memory usage: {memory_increase}MB for {large_dataset_size} SKUs"

        # Memory per SKU should be very low (< 5KB per SKU)
        memory_per_sku_kb = (memory_increase * 1024) / large_dataset_size
        assert memory_per_sku_kb < 5, f"High memory per SKU: {memory_per_sku_kb}KB"

    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available for resource monitoring")
    def test_system_resource_monitoring(self):
        """Test system resource usage during processing"""
        processor = DataProcessor()

        # Monitor CPU and memory during processing
        process = psutil.Process(os.getpid())

        # Generate medium-sized dataset
        sku_data = self._generate_large_sku_dataset(2000)

        # Monitor resources during processing
        cpu_percentages = []
        memory_usages = []

        start_time = time.perf_counter()

        # Process in chunks while monitoring
        chunk_size = 200
        for i in range(0, len(sku_data), chunk_size):
            chunk = sku_data[i:i + chunk_size]

            # Sample resource usage
            cpu_percentages.append(process.cpu_percent())
            memory_usages.append(process.memory_info().rss / 1024 / 1024)  # MB

            # Process chunk
            processed_chunk = processor.process_sku_data(chunk)
            assert len(processed_chunk) == len(chunk)

        end_time = time.perf_counter()
        total_time = end_time - start_time

        # Verify resource usage stayed reasonable
        avg_cpu = sum(cpu_percentages) / len(cpu_percentages)
        max_memory = max(memory_usages)
        avg_memory = sum(memory_usages) / len(memory_usages)

        # CPU usage should be reasonable (< 80% average)
        assert avg_cpu < 80, f"High CPU usage: {avg_cpu}% average"

        # Memory usage should be stable (< 100MB peak)
        assert max_memory < 100, f"High memory usage: {max_memory}MB peak"

        # Processing should complete in reasonable time (< 10 seconds for 2000 SKUs)
        assert total_time < 10, f"Slow processing: {total_time}s for 2000 SKUs"

    def _generate_large_sku_dataset(self, count):
        """Generate large SKU dataset for load testing"""
        sku_data = []
        for i in range(count):
            # Create varied but realistic test data
            age_days = 400 if i % 4 == 0 else 15  # 25% old, 75% new
            has_fba = i % 10 == 0  # 10% have FBA offers

            created_date = (datetime.now() - timedelta(days=age_days)).strftime('%d/%m/%Y')

            sku_data.append({
                'sku': f'LOAD-SKU-{i:06d}',
                'asin': f'B{i:011d}',
                'created_date': created_date,
                'fulfillment_channel': 'MERCHANT',
                'quantity': 10 if has_fba else 0,
                'status': 'Active'
            })

        return sku_data


class TestScalabilityTesting:
    """Test system scalability characteristics"""

    def test_linear_scalability_verification(self):
        """Verify that processing time scales linearly with data size"""
        processor = DataProcessor()
        scalability_results = []

        # Test multiple sizes to verify linear scaling
        test_sizes = [500, 1000, 2000, 4000]

        for size in test_sizes:
            sku_data = self._generate_scalable_test_data(size)

            start_time = time.perf_counter()
            processed_skus = processor.process_sku_data(sku_data)
            end_time = time.perf_counter()

            processing_time = end_time - start_time

            scalability_results.append({
                'size': size,
                'time': processing_time,
                'time_per_unit': processing_time / size
            })

            assert len(processed_skus) == size

        # Verify linear scaling by comparing time per unit
        # Time per SKU should remain relatively constant across sizes
        baseline_time_per_unit = scalability_results[0]['time_per_unit']

        for result in scalability_results[1:]:
            time_per_unit = result['time_per_unit']

            # Should be within 50% of baseline (allowing for optimization effects)
            variance = abs(time_per_unit - baseline_time_per_unit) / baseline_time_per_unit
            assert variance < 0.5, f"Non-linear scaling detected: {variance*100}% variance"

    def test_batch_processing_optimization(self):
        """Test optimal batch sizes for processing efficiency"""
        processor = DataProcessor()

        # Test different batch sizes
        batch_sizes = [50, 100, 250, 500]
        batch_results = []

        total_skus = 2000

        for batch_size in batch_sizes:
            num_batches = total_skus // batch_size

            start_time = time.perf_counter()

            for i in range(num_batches):
                # Generate and process batch
                batch_data = self._generate_scalable_test_data(batch_size)
                processed_batch = processor.process_sku_data(batch_data)
                assert len(processed_batch) == batch_size

            end_time = time.perf_counter()
            total_time = end_time - start_time

            batch_results.append({
                'batch_size': batch_size,
                'total_time': total_time,
                'time_per_sku': total_time / total_skus,
                'throughput': total_skus / total_time
            })

        # Find optimal batch size (highest throughput)
        optimal_batch = max(batch_results, key=lambda x: x['throughput'])

        # Optimal batch size should be > 100 SKUs for best throughput
        assert optimal_batch['batch_size'] >= 100, f"Suboptimal batch size: {optimal_batch['batch_size']}"

        # Verify throughput improves with larger batch sizes up to a point
        small_batch_throughput = next(b['throughput'] for b in batch_results if b['batch_size'] == 50)
        large_batch_throughput = optimal_batch['throughput']

        # Larger batches should have better throughput
        assert large_batch_throughput > small_batch_throughput * 0.8  # At least 80% of small batch throughput

    def _generate_scalable_test_data(self, count):
        """Generate test data that scales predictably"""
        sku_data = []
        for i in range(count):
            # Consistent test data pattern
            age_days = 365 if i % 2 == 0 else 30  # Half old, half new
            created_date = (datetime.now() - timedelta(days=age_days)).strftime('%d/%m/%Y')

            sku_data.append({
                'sku': f'SCALE-{i:06d}',
                'asin': f'B{i:011d}',
                'created_date': created_date,
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0,
                'status': 'Active'
            })

        return sku_data


class TestStressTesting:
    """Test system behavior under extreme conditions"""

    def test_extreme_dataset_processing(self):
        """Test processing of extremely large datasets"""
        processor = DataProcessor()

        # Test with very large dataset (25,000 SKUs)
        extreme_size = 25000
        sku_data = []

        for i in range(extreme_size):
            # Generate extreme test data
            age_days = 500 if i % 5 == 0 else 20
            created_date = (datetime.now() - timedelta(days=age_days)).strftime('%d/%m/%Y')

            sku_data.append({
                'sku': f'EXTREME-{i:07d}',
                'asin': f'B{i:011d}',
                'created_date': created_date,
                'fulfillment_channel': 'MERCHANT',
                'quantity': 0,
                'status': 'Active'
            })

        # Process extreme dataset
        start_time = time.perf_counter()
        processed_skus = processor.process_sku_data(sku_data)
        end_time = time.perf_counter()

        processing_time = end_time - start_time

        # Verify processing completed
        assert len(processed_skus) == extreme_size

        # Calculate performance metrics
        throughput = extreme_size / processing_time
        time_per_sku = processing_time / extreme_size

        # Should still achieve reasonable performance even with extreme load
        assert throughput > 200, f"Very low throughput under extreme load: {throughput} SKUs/second"
        assert time_per_sku < 0.005, f"Very slow per-SKU processing: {time_per_sku}s per SKU"

        # Processing time should be reasonable (< 2 minutes for 25k SKUs)
        assert processing_time < 120, f"Excessive processing time: {processing_time}s for {extreme_size} SKUs"

    @pytest.mark.skipif(not HAS_PSUTIL, reason="psutil not available for resource monitoring")
    def test_resource_limits_handling(self):
        """Test system behavior near resource limits"""
        processor = DataProcessor()

        # Monitor system resources
        process = psutil.Process(os.getpid())

        # Generate data that pushes memory limits
        large_sku_data = []
        chunk_size = 1000

        # Process in large chunks
        for chunk_start in range(0, 10000, chunk_size):
            chunk_end = min(chunk_start + chunk_size, 10000)
            chunk_data = []

            for i in range(chunk_start, chunk_end):
                sku_data = {
                    'sku': f'LIMIT-TEST-{i:06d}',
                    'asin': f'B{i:011d}',
                    'created_date': '01/01/2023',
                    'fulfillment_channel': 'MERCHANT',
                    'quantity': 0,
                    'status': 'Active'
                }
                chunk_data.append(sku_data)

            # Process chunk and monitor memory
            before_memory = process.memory_info().rss / 1024 / 1024  # MB

            processed_chunk = processor.process_sku_data(chunk_data)

            after_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = after_memory - before_memory

            # Memory increase per chunk should be reasonable (< 10MB per 1000 SKUs)
            assert memory_increase < 10, f"Excessive memory increase per chunk: {memory_increase}MB"

            # Verify chunk processing
            assert len(processed_chunk) == len(chunk_data)

            large_sku_data.extend(processed_chunk)

        # Verify all data processed
        assert len(large_sku_data) == 10000
