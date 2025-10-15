"""
Tests for report generation functionality in report_generator.py
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import os
from pathlib import Path

from report_generator import ReportGenerator


class TestReportGenerator:
    """Test ReportGenerator class functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = ReportGenerator(output_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures"""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_output_directory(self):
        """Test that ReportGenerator creates output directory"""
        generator = ReportGenerator(output_dir=self.temp_dir)
        assert Path(self.temp_dir).exists()
        assert Path(self.temp_dir).is_dir()

    def test_init_with_existing_directory(self):
        """Test ReportGenerator with existing directory"""
        # Directory should already exist from setup_method
        generator = ReportGenerator(output_dir=self.temp_dir)
        assert Path(self.temp_dir).exists()

    def test_generate_report_creates_file(self):
        """Test that generate_report creates a markdown file"""
        test_results = {
            'total_processed': 100,
            'eligible_for_deletion': 10,
            'deleted': ['SKU001', 'SKU002'],
            'skipped': [
                {'sku': 'SKU003', 'reason': 'has_fba_offers'},
                {'sku': 'SKU004', 'reason': 'too_new'}
            ],
            'errors': [
                {'sku': 'SKU005', 'error': 'API timeout'}
            ],
            'execution_time': 45.6
        }

        report_path = self.generator.generate_report(test_results)

        # Check file was created
        assert os.path.exists(report_path)
        assert report_path.endswith('.md')

        # Check file contents
        with open(report_path, 'r') as f:
            content = f.read()

        assert '# SKU Cleanup Report' in content
        assert '**Total SKUs Processed:** 100' in content
        assert '**Eligible for Deletion:** 10' in content
        assert '**Successfully Deleted:** 2' in content
        assert 'SKU001' in content
        assert 'SKU002' in content
        assert 'Has Fba Offers' in content
        assert 'API timeout' in content

    def test_generate_report_with_empty_results(self):
        """Test generate_report with empty/minimal results"""
        test_results = {
            'total_processed': 0,
            'eligible_for_deletion': 0,
            'deleted': [],
            'skipped': [],
            'errors': [],
            'execution_time': 0.1
        }

        report_path = self.generator.generate_report(test_results)

        # Check file was created
        assert os.path.exists(report_path)

        # Check file contents
        with open(report_path, 'r') as f:
            content = f.read()

        assert '**Total SKUs Processed:** 0' in content
        assert 'No SKUs were deleted' in content
        assert 'No SKUs were skipped' in content
        assert 'No errors occurred' in content

    def test_generate_report_performance_metrics(self):
        """Test that performance metrics are included"""
        test_results = {
            'total_processed': 1000,
            'eligible_for_deletion': 50,
            'deleted': ['SKU001'] * 50,
            'skipped': [],
            'errors': [],
            'execution_time': 120.5
        }

        report_path = self.generator.generate_report(test_results)

        with open(report_path, 'r') as f:
            content = f.read()

        # Check performance metrics
        assert '**Execution Time:** 120.50 seconds' in content
        assert '**SKUs Processed per Second:** 8.30' in content  # 1000/120.5 ≈ 8.30
        assert '**Success Rate:** 5.0%' in content

    def test_build_report_content_structure(self):
        """Test the structure of generated report content"""
        test_results = {
            'total_processed': 50,
            'eligible_for_deletion': 5,
            'deleted': ['SKU001', 'SKU002'],
            'skipped': [
                {'sku': 'SKU003', 'reason': 'has_fba_offers'}
            ],
            'errors': [
                {'sku': 'SKU004', 'error': 'Connection failed'}
            ],
            'execution_time': 30.0
        }

        content = self.generator._build_report_content(test_results)

        # Check sections are present
        assert '## Summary' in content
        assert '## Deleted SKUs' in content
        assert '## Skipped SKUs' in content
        assert '## Errors' in content
        assert '## Performance Metrics' in content
        assert '## Recommendations' in content

        # Check specific content
        assert '**Total SKUs Processed:** 50' in content
        assert '**Eligible for Deletion:** 5' in content

    def test_cleanup_old_reports(self):
        """Test cleanup of old report files"""
        # Create some test report files with different dates
        reports_dir = Path(self.temp_dir)

        # Create report files with different timestamps
        old_date = datetime.now() - timedelta(days=35)  # Older than default 30 days
        new_date = datetime.now() - timedelta(days=5)   # Within 30 days

        old_report = reports_dir / f"sku-cleanup-report-{old_date.strftime('%Y-%m-%d_%H-%M-%S')}.md"
        new_report = reports_dir / f"sku-cleanup-report-{new_date.strftime('%Y-%m-%d_%H-%M-%S')}.md"

        old_report.write_text("# Old Report")
        new_report.write_text("# New Report")

        # Run cleanup
        self.generator.cleanup_old_reports(keep_days=30)

        # Old report should be deleted, new should remain
        assert not old_report.exists()
        assert new_report.exists()

    def test_cleanup_old_reports_no_directory(self):
        """Test cleanup when reports directory doesn't exist"""
        # Use a non-existent but creatable directory
        nonexistent_dir = os.path.join(self.temp_dir, "subdir", "nonexistent")
        generator = ReportGenerator(output_dir=nonexistent_dir)
        # Should not raise an exception (directory gets created)
        generator.cleanup_old_reports(keep_days=30)

    def test_list_reports_empty_directory(self):
        """Test listing reports in empty directory"""
        reports = self.generator.list_reports()
        assert reports == []

    def test_list_reports_with_files(self):
        """Test listing reports with actual files"""
        # Create test report files
        reports_dir = Path(self.temp_dir)

        report1 = reports_dir / "sku-cleanup-report-2023-12-25_10-30-45.md"
        report2 = reports_dir / "sku-cleanup-report-2023-12-26_14-20-30.md"

        report1.write_text("# Report 1")
        report2.write_text("# Report 2")

        reports = self.generator.list_reports()

        assert len(reports) == 2

        # Check report metadata
        for report in reports:
            assert 'filename' in report
            assert 'timestamp' in report
            assert 'size' in report
            assert 'path' in report
            assert isinstance(report['timestamp'], datetime)

    def test_list_reports_invalid_files(self):
        """Test listing reports with invalid filenames"""
        reports_dir = Path(self.temp_dir)

        # Create invalid report files
        invalid1 = reports_dir / "not-a-report.txt"
        invalid2 = reports_dir / "invalid-report-name.md"
        valid_report = reports_dir / "sku-cleanup-report-2023-12-25_10-30-45.md"

        invalid1.write_text("Not a report")
        invalid2.write_text("Invalid name")
        valid_report.write_text("# Valid Report")

        reports = self.generator.list_reports()

        # Should only return the valid report
        assert len(reports) == 1
        assert reports[0]['filename'] == "sku-cleanup-report-2023-12-25_10-30-45.md"

    def test_generate_summary_report(self):
        """Test generation of summary reports"""
        # This method currently returns a placeholder
        result = self.generator.generate_summary_report([])
        assert "Weekly/Monthly Summary Report" in result
        assert "Feature coming soon" in result


class TestReportGeneratorEdgeCases:
    """Test edge cases and error conditions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_report_with_missing_keys(self):
        """Test generate_report with missing result keys"""
        incomplete_results = {
            'total_processed': 10,
            # Missing other keys
        }

        # Should not raise an exception, should use defaults
        report_path = ReportGenerator(self.temp_dir).generate_report(incomplete_results)
        assert os.path.exists(report_path)

    def test_cleanup_reports_with_invalid_date_format(self):
        """Test cleanup with invalid date formats in filenames"""
        reports_dir = Path(tempfile.mkdtemp())

        try:
            # Create a file with invalid date format
            invalid_report = reports_dir / "sku-cleanup-report-invalid-date.md"
            invalid_report.write_text("# Invalid Report")

            generator = ReportGenerator(output_dir=str(reports_dir))

            # Should not raise an exception, should skip invalid files
            generator.cleanup_old_reports(keep_days=30)

            # Invalid file should still exist (couldn't parse date)
            assert invalid_report.exists()

        finally:
            import shutil
            shutil.rmtree(reports_dir, ignore_errors=True)

    def test_build_report_content_with_large_numbers(self):
        """Test building report content with large numbers"""
        large_results = {
            'total_processed': 1000000,
            'eligible_for_deletion': 100000,
            'deleted': ['SKU%06d' % i for i in range(100000)],
            'skipped': [],
            'errors': [],
            'execution_time': 3600.0
        }

        generator = ReportGenerator(self.temp_dir)
        content = generator._build_report_content(large_results)

        assert '**Total SKUs Processed:** 1000000' in content
        assert '**Successfully Deleted:** 100000' in content
