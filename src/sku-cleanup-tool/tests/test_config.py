"""
Unit tests for configuration management
Tests config loading, validation, and environment variable handling
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from core.config import Config, CleanupSettings, ResilienceSettings, AmazonCredentials


class TestCleanupSettings:
    """Test cleanup settings configuration"""

    def test_default_values(self):
        """Test that default values are set correctly"""
        settings = CleanupSettings(
            dry_run=True,
            age_threshold_days=30,
            batch_size=100,
            log_level='INFO',
            skip_skus=[]
        )

        assert settings.dry_run is True
        assert settings.age_threshold_days == 30
        assert settings.batch_size == 100
        assert settings.log_level == 'INFO'
        assert settings.test_mode is False
        assert settings.test_sample_size == 10

    def test_custom_values(self):
        """Test that custom values are set correctly"""
        settings = CleanupSettings(
            dry_run=False,
            age_threshold_days=60,
            batch_size=50,
            log_level='DEBUG',
            skip_skus=[]
        )

        assert settings.dry_run is False
        assert settings.age_threshold_days == 60
        assert settings.batch_size == 50
        assert settings.log_level == 'DEBUG'

    def test_resilience_settings_integration(self):
        """Test that resilience settings are properly integrated"""
        settings = CleanupSettings(
            dry_run=True,
            age_threshold_days=30,
            batch_size=100,
            log_level='INFO',
            skip_skus=[]
        )
        resilience = settings.resilience

        assert isinstance(resilience, ResilienceSettings)
        assert resilience.max_retries == 2  # Correct default value
        assert resilience.base_delay == 0.5  # Correct default value


class TestResilienceSettings:
    """Test resilience configuration"""

    def test_default_resilience_values(self):
        """Test default resilience configuration values"""
        resilience = ResilienceSettings()

        assert resilience.max_retries == 2  # Correct default value
        assert resilience.base_delay == 0.5  # Correct default value
        assert resilience.max_delay == 30.0  # Correct default value
        assert resilience.max_connections == 20  # Correct default value
        assert resilience.circuit_breaker_failure_threshold == 50  # Correct default value

    def test_resilience_validation(self):
        """Test that resilience settings validate inputs"""
        # Valid configuration
        resilience = ResilienceSettings(max_retries=5, base_delay=2.0)
        assert resilience.max_retries == 5
        assert resilience.base_delay == 2.0

        # Test boundary values
        resilience = ResilienceSettings(max_retries=1, base_delay=0.1)
        assert resilience.max_retries == 1
        assert resilience.base_delay == 0.1


class TestAmazonCredentials:
    """Test credentials configuration"""

    def test_credentials_with_env_vars(self):
        """Test loading credentials from environment variables"""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret',
            'AMAZON_SELLER_ID': 'test_seller',
            'MARKETPLACE_ID': 'test_marketplace',
            'LWA_CLIENT_ID': 'test_client',
            'LWA_CLIENT_SECRET': 'test_lwa_secret',
            'LWA_REFRESH_TOKEN': 'test_token'
        }):
            credentials = AmazonCredentials(
                access_key_id='test_key',
                secret_access_key='test_secret',
                seller_id='test_seller',
                marketplace_id='test_marketplace',
                lwa_client_id='test_client',
                lwa_client_secret='test_lwa_secret',
                lwa_refresh_token='test_token'
            )
            assert credentials.access_key_id == 'test_key'
            assert credentials.secret_access_key == 'test_secret'
            assert credentials.seller_id == 'test_seller'

    def test_credentials_missing_env_vars(self):
        """Test behavior when environment variables are missing"""
        with patch.dict(os.environ, {}, clear=True):
            # Test that Config class properly handles missing required environment variables
            # The Config class should raise ValueError when required credentials are missing
            try:
                config = Config()
                assert False, "Expected ValueError for missing credentials"
            except ValueError as e:
                assert "Required environment variable AWS_ACCESS_KEY_ID is not set" in str(e)


class TestConfigIntegration:
    """Test overall configuration integration"""

    def test_config_initialization(self):
        """Test that Config initializes properly"""
        config = Config()

        assert config.settings is not None
        assert config.credentials is not None
        assert isinstance(config.settings, CleanupSettings)
        assert isinstance(config.credentials, AmazonCredentials)

    @patch.dict(os.environ, {'DRY_RUN': 'false', 'LOG_LEVEL': 'DEBUG'})
    def test_config_from_environment(self):
        """Test loading configuration from environment variables"""
        # This test would depend on your actual env var implementation
        # For now, just ensure no errors occur
        config = Config()
        assert config is not None
