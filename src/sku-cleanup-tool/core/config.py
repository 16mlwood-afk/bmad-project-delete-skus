"""
Configuration management for SKU Cleanup Tool
Handles environment variables and application settings
"""
import os
from typing import List, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class AmazonCredentials:
    """Amazon API credentials and configuration"""
    access_key_id: str
    secret_access_key: str
    seller_id: str
    marketplace_id: str
    lwa_client_id: str
    lwa_client_secret: str
    lwa_refresh_token: str

@dataclass
class ResilienceSettings:
    """API resilience configuration"""
    # Exponential backoff settings
    max_retries: int = 2  # Reduced for faster processing
    base_delay: float = 0.5  # Reduced delay
    max_delay: float = 30.0  # Maximum delay in seconds
    backoff_factor: float = 2.0  # Exponential backoff multiplier
    jitter: bool = True  # Add random jitter to prevent thundering herd

    # Connection pooling settings
    max_connections: int = 20  # Increased for better parallelism
    connection_timeout: float = 15.0  # Reduced timeout
    read_timeout: float = 30.0  # Reduced timeout

    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 50  # Much more tolerant for bulk operations
    circuit_breaker_recovery_timeout: int = 60  # Longer recovery time
    circuit_breaker_error_rate_threshold: float = 0.5  # 50% error rate before opening

@dataclass
class CleanupSettings:
    """Application configuration settings"""
    dry_run: bool
    age_threshold_days: int
    batch_size: int
    log_level: str
    skip_skus: List[str]
    resilience: ResilienceSettings = field(default_factory=ResilienceSettings)

    # Testing modes
    # test_mode: Use sample of SKUs for testing (implies dry_run=True for safety)
    test_mode: bool = False
    test_sample_size: int = 10  # Number of SKUs to process in test mode
    test_seed_skus: List[str] = field(default_factory=list)  # Specific SKUs to test with

class Config:
    """Main configuration class"""

    def __init__(self):
        self.credentials = self._load_credentials()
        self.settings = self._load_settings()

    def _load_credentials(self) -> AmazonCredentials:
        """Load Amazon API credentials from environment variables"""
        return AmazonCredentials(
            access_key_id=self._get_env_var('AWS_ACCESS_KEY_ID', required=True),
            secret_access_key=self._get_env_var('AWS_SECRET_ACCESS_KEY', required=True),
            seller_id=self._get_env_var('AMAZON_SELLER_ID', required=True),
            marketplace_id=self._get_env_var('MARKETPLACE_ID', 'A1F83G8C2ARO7P'),
            lwa_client_id=self._get_env_var('LWA_CLIENT_ID', required=True),
            lwa_client_secret=self._get_env_var('LWA_CLIENT_SECRET', required=True),
            lwa_refresh_token=self._get_env_var('LWA_REFRESH_TOKEN', required=True)
        )

    def _load_settings(self) -> CleanupSettings:
        """Load application settings from environment variables"""
        resilience = ResilienceSettings(
            max_retries=self._get_env_int('MAX_RETRIES', 2),
            base_delay=self._get_env_float('BASE_DELAY', 0.5),
            max_delay=self._get_env_float('MAX_DELAY', 30.0),
            backoff_factor=self._get_env_float('BACKOFF_FACTOR', 2.0),
            jitter=self._get_env_bool('JITTER', True),
            max_connections=self._get_env_int('MAX_CONNECTIONS', 20),
            connection_timeout=self._get_env_float('CONNECTION_TIMEOUT', 15.0),
            read_timeout=self._get_env_float('READ_TIMEOUT', 30.0),
            circuit_breaker_failure_threshold=self._get_env_int('CIRCUIT_BREAKER_FAILURE_THRESHOLD', 50),
            circuit_breaker_recovery_timeout=self._get_env_int('CIRCUIT_BREAKER_RECOVERY_TIMEOUT', 60),
            circuit_breaker_error_rate_threshold=self._get_env_float('CIRCUIT_BREAKER_ERROR_RATE_THRESHOLD', 0.5)
        )

        return CleanupSettings(
            dry_run=self._get_env_bool('DRY_RUN', True),
            age_threshold_days=self._get_env_int('AGE_THRESHOLD_DAYS', 30),
            batch_size=self._get_env_int('BATCH_SIZE', 100),
            log_level=self._get_env_var('LOG_LEVEL', 'INFO').upper(),
            skip_skus=self._parse_skip_skus(),
            resilience=resilience,
            test_mode=self._get_env_bool('TEST_MODE', False),
            test_sample_size=self._get_env_int('TEST_SAMPLE_SIZE', 10),
            test_seed_skus=self._parse_test_seed_skus()
        )

    def _get_env_var(self, key: str, default: str = '', required: bool = False) -> str:
        """Get environment variable with optional default and required check"""
        value = os.getenv(key, default)
        if required and not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value

    def _get_env_bool(self, key: str, default: bool) -> bool:
        """Get boolean environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')

    def _get_env_int(self, key: str, default: int) -> int:
        """Get integer environment variable"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            raise ValueError(f"Environment variable {key} must be a valid integer")

    def _get_env_float(self, key: str, default: float) -> float:
        """Get float environment variable"""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            raise ValueError(f"Environment variable {key} must be a valid float")

    def _parse_skip_skus(self) -> List[str]:
        """Parse comma-separated skip SKUs list"""
        skip_skus_str = os.getenv('SKIP_SKUS', '')
        if not skip_skus_str:
            return []
        return [sku.strip() for sku in skip_skus_str.split(',') if sku.strip()]

    def _parse_test_seed_skus(self) -> List[str]:
        """Parse comma-separated test seed SKUs list"""
        test_seed_skus_str = os.getenv('TEST_SEED_SKUS', '')
        if not test_seed_skus_str:
            return []
        return [sku.strip() for sku in test_seed_skus_str.split(',') if sku.strip()]

# Global configuration instance
config = Config()
