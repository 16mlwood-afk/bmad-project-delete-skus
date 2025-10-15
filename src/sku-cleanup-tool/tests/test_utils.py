"""
Tests for utility functions in utils.py
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open
import os
import tempfile

from core.utils import (
    parse_amazon_date,
    format_duration,
    safe_int,
    safe_float,
    format_file_size,
    create_directory_if_not_exists,
    get_timestamp,
    validate_sku_format,
    chunk_list,
    retry_on_exception
)


class TestDateParsing:
    """Test Amazon date parsing functionality"""

    def test_parse_valid_amazon_date(self):
        """Test parsing valid DD/MM/YYYY date format"""
        result = parse_amazon_date("25/12/2023")
        expected = datetime(2023, 12, 25)
        assert result == expected

    def test_parse_empty_date(self):
        """Test parsing empty date returns None"""
        assert parse_amazon_date("") is None
        assert parse_amazon_date(None) is None

    def test_parse_invalid_date_format(self):
        """Test parsing invalid date formats"""
        assert parse_amazon_date("2023-12-25") is None  # Wrong format
        assert parse_amazon_date("32/12/2023") is None  # Invalid day
        assert parse_amazon_date("25/13/2023") is None  # Invalid month
        assert parse_amazon_date("29/02/2023") is None  # Invalid leap year date

    def test_parse_date_with_slashes_only(self):
        """Test parsing date with only slashes"""
        assert parse_amazon_date("25/12") is None
        assert parse_amazon_date("/") is None


class TestDurationFormatting:
    """Test duration formatting functionality"""

    def test_format_seconds(self):
        """Test formatting seconds"""
        assert format_duration(30.5) == "30.50s"
        assert format_duration(59.9) == "59.90s"

    def test_format_minutes(self):
        """Test formatting minutes and seconds"""
        assert format_duration(90) == "1m 30s"
        assert format_duration(125.7) == "2m 6s"

    def test_format_hours(self):
        """Test formatting hours and minutes"""
        assert format_duration(3661) == "1h 1m"
        assert format_duration(7323) == "2h 2m"


class TestSafeConversion:
    """Test safe type conversion functions"""

    def test_safe_int_valid(self):
        """Test safe integer conversion with valid inputs"""
        assert safe_int("123") == 123
        assert safe_int("0") == 0
        assert safe_int("") == 0  # Default when empty
        assert safe_int(None) == 0  # Default when None

    def test_safe_int_invalid(self):
        """Test safe integer conversion with invalid inputs"""
        assert safe_int("abc") == 0
        assert safe_int("12.34") == 0
        assert safe_int("123abc") == 0

    def test_safe_int_custom_default(self):
        """Test safe integer conversion with custom default"""
        assert safe_int("abc", 999) == 999
        assert safe_int("", 555) == 555

    def test_safe_float_valid(self):
        """Test safe float conversion with valid inputs"""
        assert safe_float("123.45") == 123.45
        assert safe_float("0.0") == 0.0
        assert safe_float("") == 0.0
        assert safe_float(None) == 0.0

    def test_safe_float_invalid(self):
        """Test safe float conversion with invalid inputs"""
        assert safe_float("abc") == 0.0
        assert safe_float("12.34.56") == 0.0

    def test_safe_float_custom_default(self):
        """Test safe float conversion with custom default"""
        assert safe_float("abc", 99.9) == 99.9


class TestFileSizeFormatting:
    """Test file size formatting functionality"""

    def test_format_bytes(self):
        """Test formatting bytes"""
        assert format_file_size(512) == "512.0B"

    def test_format_kilobytes(self):
        """Test formatting kilobytes"""
        assert format_file_size(1536) == "1.5KB"

    def test_format_megabytes(self):
        """Test formatting megabytes"""
        assert format_file_size(1048576) == "1.0MB"

    def test_format_gigabytes(self):
        """Test formatting gigabytes"""
        assert format_file_size(1073741824) == "1.0GB"

    def test_format_terabytes(self):
        """Test formatting terabytes"""
        assert format_file_size(1099511627776) == "1.0TB"


class TestDirectoryOperations:
    """Test directory creation functionality"""

    def test_create_existing_directory(self):
        """Test creating a directory that already exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should not raise an exception
            create_directory_if_not_exists(temp_dir)

    def test_create_new_directory(self):
        """Test creating a new directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = os.path.join(temp_dir, "new_subdir")
            create_directory_if_not_exists(new_dir)
            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)


class TestTimestampGeneration:
    """Test timestamp generation functionality"""

    def test_get_timestamp_format(self):
        """Test timestamp format is ISO format"""
        timestamp = get_timestamp()
        # Should be parseable as ISO format
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert isinstance(parsed, datetime)

    def test_get_timestamp_is_string(self):
        """Test timestamp returns a string"""
        timestamp = get_timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0


class TestSKUValidation:
    """Test SKU format validation"""

    def test_valid_skus(self):
        """Test validation of valid SKUs"""
        assert validate_sku_format("ABC123") is True
        assert validate_sku_format("SKU-001") is True
        assert validate_sku_format("A") is True  # Single character

    def test_invalid_skus(self):
        """Test validation of invalid SKUs"""
        assert validate_sku_format("") is False
        assert validate_sku_format(None) is False
        assert validate_sku_format(123) is False  # Not a string
        assert validate_sku_format("   ") is False  # Only whitespace


class TestListChunking:
    """Test list chunking functionality"""

    def test_chunk_empty_list(self):
        """Test chunking an empty list"""
        result = chunk_list([], 5)
        assert result == []

    def test_chunk_smaller_than_size(self):
        """Test chunking list smaller than chunk size"""
        items = [1, 2, 3]
        result = chunk_list(items, 5)
        assert result == [[1, 2, 3]]

    def test_chunk_exact_division(self):
        """Test chunking with exact division"""
        items = [1, 2, 3, 4, 5, 6]
        result = chunk_list(items, 3)
        assert result == [[1, 2, 3], [4, 5, 6]]

    def test_chunk_uneven_division(self):
        """Test chunking with uneven division"""
        items = [1, 2, 3, 4, 5]
        result = chunk_list(items, 2)
        assert result == [[1, 2], [3, 4], [5]]

    def test_chunk_size_one(self):
        """Test chunking with size 1"""
        items = [1, 2, 3]
        result = chunk_list(items, 1)
        assert result == [[1], [2], [3]]


class TestRetryDecorator:
    """Test retry decorator functionality"""

    def test_retry_success_first_attempt(self):
        """Test successful function on first attempt"""
        call_count = 0

        @retry_on_exception(max_attempts=3, delay=0.1)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_success_after_failures(self):
        """Test successful function after some failures"""
        call_count = 0

        @retry_on_exception(max_attempts=3, delay=0.1)
        def eventually_successful_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "success"

        result = eventually_successful_function()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhaust_all_attempts(self):
        """Test function that fails all attempts"""
        call_count = 0

        @retry_on_exception(max_attempts=2, delay=0.1)
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Attempt {call_count} failed")

        with pytest.raises(ValueError) as exc_info:
            always_failing_function()

        assert "Attempt 2 failed" in str(exc_info.value)
        assert call_count == 2

    def test_retry_with_custom_parameters(self):
        """Test retry decorator with custom parameters"""
        call_count = 0

        @retry_on_exception(max_attempts=5, delay=0.05)
        def custom_retry_function():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise RuntimeError(f"Attempt {call_count} failed")
            return "custom success"

        result = custom_retry_function()
        assert result == "custom success"
        assert call_count == 4
