"""
API Resilience utilities for handling Amazon API failures gracefully
Implements exponential backoff, connection pooling, and circuit breaker patterns
"""
import time
import logging
import requests
from typing import Dict, List, Optional, Any, Callable, TypeVar
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ErrorType(Enum):
    """Categorize errors for different retry strategies"""
    RATE_LIMIT = "rate_limit"      # 429 errors
    SERVER_ERROR = "server_error"  # 500, 502, 503 errors
    NETWORK = "network"           # Connection errors
    CLIENT_ERROR = "client_error" # 400 errors
    AUTH = "auth"                 # 401, 403 errors
    NOT_FOUND = "not_found"       # 404 errors
    UNKNOWN = "unknown"           # Other errors

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5  # Number of failures before opening circuit
    recovery_timeout: int = 60  # Seconds before trying half-open
    expected_exception: Exception = requests.RequestException

@dataclass
class RetryConfig:
    """Configuration for retry strategy"""
    max_retries: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    backoff_factor: float = 2.0  # Exponential backoff multiplier
    jitter: bool = True  # Add random jitter to prevent thundering herd

class ResilienceMetrics:
    """Track API call metrics for circuit breaker"""

    def __init__(self):
        self.call_count = 0
        self.error_count = 0
        self.last_error_time = None
        self.circuit_state = CircuitBreakerState.CLOSED
        self.last_state_change = time.time()
        self._lock = Lock()

    def record_call(self):
        """Record a successful API call"""
        with self._lock:
            self.call_count += 1

    def record_error(self, error_type: ErrorType):
        """Record an API call error"""
        with self._lock:
            self.error_count += 1
            self.last_error_time = time.time()

    def get_error_rate(self) -> float:
        """Calculate current error rate"""
        with self._lock:
            if self.call_count == 0:
                return 0.0
            return self.error_count / self.call_count

    def should_attempt_reset(self, config: CircuitBreakerConfig) -> bool:
        """Check if circuit breaker should attempt to reset"""
        with self._lock:
            if self.circuit_state != CircuitBreakerState.OPEN:
                return False

            time_since_last_error = time.time() - (self.last_error_time or 0)
            return time_since_last_error >= config.recovery_timeout

    def reset(self):
        """Reset circuit breaker metrics"""
        with self._lock:
            self.call_count = 0
            self.error_count = 0
            self.last_error_time = None
            self.circuit_state = CircuitBreakerState.CLOSED
            self.last_state_change = time.time()

class CircuitBreaker:
    """Circuit breaker implementation for API resilience"""

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.metrics = ResilienceMetrics()
        self._lock = Lock()

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Check if we should allow the call
            if not self._can_proceed():
                raise Exception(f"Circuit breaker '{self.name}' is OPEN - blocking call to prevent cascade failure")

            try:
                # Execute the function
                result = func(*args, **kwargs)
                self.metrics.record_call()
                return result

            except self.config.expected_exception as e:
                self.metrics.record_error(self._classify_error(e))
                self._check_circuit_state()
                raise
            except Exception as e:
                # Non-expected exceptions don't count toward circuit breaker
                self.metrics.record_call()
                raise

        return wrapper

    def _can_proceed(self) -> bool:
        """Check if call should be allowed through circuit breaker"""
        with self._lock:
            if self.metrics.circuit_state == CircuitBreakerState.CLOSED:
                return True
            elif self.metrics.circuit_state == CircuitBreakerState.OPEN:
                if self.metrics.should_attempt_reset(self.config):
                    # Transition to half-open for testing
                    self.metrics.circuit_state = CircuitBreakerState.HALF_OPEN
                    logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                    return True
                return False
            else:  # HALF_OPEN
                return True

    def _check_circuit_state(self):
        """Check if circuit breaker should change state"""
        with self._lock:
            error_rate = self.metrics.get_error_rate()

            if self.metrics.circuit_state == CircuitBreakerState.HALF_OPEN:
                # In half-open, single error sends us back to open
                if self.metrics.error_count > 0:
                    self.metrics.circuit_state = CircuitBreakerState.OPEN
                    logger.warning(f"Circuit breaker '{self.name}' back to OPEN after error in half-open state")
            elif error_rate >= 0.5:  # 50% error rate threshold
                self.metrics.circuit_state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' opened due to high error rate: {error_rate:.2%}")

    def _classify_error(self, error) -> ErrorType:
        """Classify error type for appropriate handling"""
        if hasattr(error, 'response') and error.response is not None:
            status_code = error.response.status_code
            if status_code == 429:
                return ErrorType.RATE_LIMIT
            elif status_code >= 500:
                return ErrorType.SERVER_ERROR
            elif status_code == 401 or status_code == 403:
                return ErrorType.AUTH
            elif status_code == 404:
                return ErrorType.NOT_FOUND
            elif status_code >= 400:
                return ErrorType.CLIENT_ERROR

        # Check for common network errors
        error_str = str(error).lower()
        if any(term in error_str for term in ['connection', 'timeout', 'network']):
            return ErrorType.NETWORK

        return ErrorType.UNKNOWN

def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True
):
    """Decorator for exponential backoff retry strategy"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except requests.exceptions.RequestException as e:
                    last_exception = e

                    # Don't retry on the last attempt
                    if attempt == max_retries:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)

                    # Add jitter to prevent thundering herd
                    if jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay

                    logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    logger.info(f"Retrying in {delay:.1f} seconds...")

                    time.sleep(delay)

            # If we get here, all retries failed
            logger.error(f"All {max_retries + 1} attempts failed. Last error: {last_exception}")
            raise last_exception

        return wrapper
    return decorator

def create_session_with_pool(max_connections: int = 10, max_retries: int = 3) -> requests.Session:
    """Create a requests session with connection pooling configured"""
    session = requests.Session()

    # Configure connection pooling
    adapter = requests.adapters.HTTPAdapter(
        max_retries=max_retries,
        pool_connections=max_connections,
        pool_maxsize=max_connections * 2,  # Allow more connections per host
        pool_block=False  # Don't block when pool is full
    )

    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session

# Global session for connection pooling
_api_session = None

def get_api_session() -> requests.Session:
    """Get or create global API session with connection pooling"""
    global _api_session
    if _api_session is None:
        _api_session = create_session_with_pool()
    return _api_session
