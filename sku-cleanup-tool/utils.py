"""
Utility functions for SKU Cleanup Tool
Helper functions for date parsing, logging, and common operations
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def parse_amazon_date(date_string: str) -> Optional[datetime]:
    """Parse Amazon's DD/MM/YYYY date format"""
    if not date_string:
        return None

    try:
        day, month, year = date_string.split('/')
        return datetime(int(year), int(month), int(day))
    except (ValueError, IndexError):
        logger.warning(f"Invalid date format: {date_string}")
        return None

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.0f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"

def safe_int(value: str, default: int = 0) -> int:
    """Safely convert string to integer"""
    try:
        return int(value) if value else default
    except (ValueError, TypeError):
        return default

def safe_float(value: str, default: float = 0.0) -> float:
    """Safely convert string to float"""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default

def format_file_size(bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024.0
    return f"{bytes:.1f}TB"

def create_directory_if_not_exists(path: str):
    """Create directory if it doesn't exist"""
    import os
    os.makedirs(path, exist_ok=True)

def get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()

def validate_sku_format(sku: str) -> bool:
    """Basic SKU format validation"""
    if not sku or not isinstance(sku, str):
        return False

    # Basic checks - can be made more sophisticated
    return len(sku.strip()) > 0

def chunk_list(items: list, chunk_size: int) -> list:
    """Split list into chunks of specified size"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

def retry_on_exception(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for retrying functions on exceptions"""
    import time
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed. Last error: {e}")

            raise last_exception

        return wrapper
    return decorator
