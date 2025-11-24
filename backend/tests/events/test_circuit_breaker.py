"""
Unit tests for circuit breaker
"""
import pytest
import asyncio
from shared.events import CircuitBreaker, CircuitBreakerOpenError, CircuitState


class TestCircuitBreaker:
    """Test CircuitBreaker class"""

    def test_init(self):
        """Test circuit breaker initialization"""
        cb = CircuitBreaker(failure_threshold=3, timeout=10.0)

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_threshold == 3
        assert cb.timeout == 10.0
        assert cb.failure_count == 0

    def test_successful_calls(self):
        """Test successful calls keep circuit closed"""
        cb = CircuitBreaker(failure_threshold=3)

        def success_func():
            return "success"

        for _ in range(10):
            result = cb.call(success_func)
            assert result == "success"

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_failures_open_circuit(self):
        """Test failures open the circuit"""
        cb = CircuitBreaker(failure_threshold=3)

        def failing_func():
            raise Exception("Test failure")

        # First 3 failures
        for _ in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        # Circuit should now be open
        assert cb.state == CircuitState.OPEN

        # Next call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(failing_func)

    def test_half_open_transition(self):
        """Test transition to half-open after timeout"""
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1)

        def failing_func():
            raise Exception("Test failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        import time
        time.sleep(0.2)

        # Should transition to half-open on next call attempt
        def success_func():
            return "success"

        result = cb.call(success_func)
        assert result == "success"

    def test_half_open_to_closed(self):
        """Test transition from half-open to closed after successes"""
        cb = CircuitBreaker(
            failure_threshold=2,
            success_threshold=2,
            timeout=0.1,
        )

        def failing_func():
            raise Exception("Test failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        import time
        time.sleep(0.2)

        # Successful calls should close circuit
        def success_func():
            return "success"

        for _ in range(2):
            cb.call(success_func)

        assert cb.state == CircuitState.CLOSED

    def test_half_open_to_open_on_failure(self):
        """Test transition back to open on failure in half-open"""
        cb = CircuitBreaker(failure_threshold=2, timeout=0.1)

        def failing_func():
            raise Exception("Test failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        # Wait for timeout
        import time
        time.sleep(0.2)

        # Failure in half-open should reopen circuit
        with pytest.raises(Exception):
            cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

    def test_reset(self):
        """Test manual circuit breaker reset"""
        cb = CircuitBreaker(failure_threshold=2)

        def failing_func():
            raise Exception("Test failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Reset
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_concurrent_calls_in_half_open(self):
        """Test max concurrent calls in half-open state"""
        cb = CircuitBreaker(
            failure_threshold=2,
            timeout=0.1,
            half_open_max_requests=2,
        )

        def failing_func():
            raise Exception("Test failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        # Wait for timeout
        import time
        time.sleep(0.2)

        # Simulate concurrent calls
        def slow_success():
            time.sleep(0.1)
            return "success"

        # This should work but we can't easily test concurrency in sync tests
        result = cb.call(slow_success)
        assert result == "success"
