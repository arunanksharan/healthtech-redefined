"""
Circuit Breaker pattern for event publishing
Prevents cascading failures by temporarily blocking requests to failing services
"""
import time
from enum import Enum
from typing import Callable, Optional
from loguru import logger


class CircuitState(str, Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker implementation for event publishing

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failures exceed threshold, requests blocked
    - HALF_OPEN: Testing if service recovered, limited requests pass

    Transitions:
    - CLOSED -> OPEN: When failure rate exceeds threshold
    - OPEN -> HALF_OPEN: After timeout period
    - HALF_OPEN -> CLOSED: When test requests succeed
    - HALF_OPEN -> OPEN: When test requests fail
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        half_open_max_requests: int = 3,
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes to close circuit from half-open
            timeout: Seconds to wait before trying half-open state
            half_open_max_requests: Max concurrent requests in half-open state
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.half_open_max_requests = half_open_max_requests

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_requests = 0

    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function through circuit breaker

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result if successful

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception from function
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Failed {self.failure_count} times."
                )

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_requests >= self.half_open_max_requests:
                raise CircuitBreakerOpenError(
                    "Circuit breaker is HALF_OPEN with max concurrent requests"
                )
            self.half_open_requests += 1

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
        finally:
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_requests -= 1

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return False
        return (time.time() - self.last_failure_time) >= self.timeout

    def _transition_to_half_open(self):
        """Transition from OPEN to HALF_OPEN"""
        logger.info("Circuit breaker transitioning to HALF_OPEN state")
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.half_open_requests = 0

    def _on_success(self):
        """Handle successful request"""
        if self.state == CircuitState.CLOSED:
            self.failure_count = 0
        elif self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._transition_to_closed()

    def _on_failure(self):
        """Handle failed request"""
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()

    def _transition_to_open(self):
        """Transition to OPEN state"""
        logger.warning(
            f"Circuit breaker OPEN after {self.failure_count} failures. "
            f"Will retry in {self.timeout} seconds."
        )
        self.state = CircuitState.OPEN
        self.success_count = 0

    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        logger.info(
            f"Circuit breaker CLOSED after {self.success_count} successes"
        )
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def reset(self):
        """Manually reset circuit breaker to CLOSED state"""
        logger.info("Circuit breaker manually reset to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_requests = 0

    @property
    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self.state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed"""
        return self.state == CircuitState.CLOSED


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""

    pass
