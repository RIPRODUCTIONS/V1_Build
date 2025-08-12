from __future__ import annotations

import enum
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.obs.metrics import record_manager_failure


class FailureReason(enum.Enum):
    """Standardized failure reasons for automation runs."""

    VALIDATION = 'VALIDATION'  # Input validation failed
    DEPENDENCY = 'DEPENDENCY'  # Required dependency unavailable
    RUNTIME = 'RUNTIME'  # Runtime execution error
    INTEGRATION = 'INTEGRATION'  # External service integration failed
    TIMEOUT = 'TIMEOUT'  # Operation timed out
    RESOURCE = 'RESOURCE'  # Resource exhaustion (CPU, memory, etc.)
    NETWORK = 'NETWORK'  # Network connectivity issues
    AUTHENTICATION = 'AUTHENTICATION'  # Authentication/authorization failed
    RATE_LIMIT = 'RATE_LIMIT'  # Rate limit exceeded
    UNKNOWN = 'UNKNOWN'  # Unknown/unclassified error


@dataclass
class RetryPolicy:
    """Retry policy configuration for different failure types."""

    max_attempts: int
    base_delay: float  # seconds
    max_delay: float  # seconds
    backoff_factor: float = 2.0
    jitter: bool = True

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a specific attempt."""
        if attempt >= self.max_attempts:
            return 0

        delay = self.base_delay * (self.backoff_factor**attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add ±25% jitter to prevent thundering herd
            import random

            jitter_factor = 0.75 + (random.random() * 0.5)
            delay *= jitter_factor

        return delay


class RetryPolicies:
    """Predefined retry policies for different failure types."""

    # Quick retries for transient issues
    QUICK = RetryPolicy(max_attempts=3, base_delay=0.1, max_delay=1.0)

    # Standard retries for most operations
    STANDARD = RetryPolicy(max_attempts=5, base_delay=1.0, max_delay=30.0)

    # Aggressive retries for critical operations
    AGGRESSIVE = RetryPolicy(max_attempts=10, base_delay=2.0, max_delay=300.0)

    # No retries for validation errors
    NONE = RetryPolicy(max_attempts=1, base_delay=0.0, max_delay=0.0)

    @classmethod
    def get_policy_for_reason(cls, reason: FailureReason) -> RetryPolicy:
        """Get appropriate retry policy for a failure reason."""
        policy_map = {
            FailureReason.VALIDATION: cls.NONE,
            FailureReason.DEPENDENCY: cls.STANDARD,
            FailureReason.RUNTIME: cls.STANDARD,
            FailureReason.INTEGRATION: cls.AGGRESSIVE,
            FailureReason.TIMEOUT: cls.QUICK,
            FailureReason.RESOURCE: cls.STANDARD,
            FailureReason.NETWORK: cls.AGGRESSIVE,
            FailureReason.AUTHENTICATION: cls.NONE,
            FailureReason.RATE_LIMIT: cls.STANDARD,
            FailureReason.UNKNOWN: cls.STANDARD,
        }
        return policy_map.get(reason, cls.STANDARD)


@dataclass
class AutomationError:
    """Structured error information for automation runs."""

    reason: FailureReason
    message: str
    details: dict[str, Any] | None = None
    original_exception: Exception | None = None
    attempt: int = 1
    max_attempts: int = 1
    retryable: bool = True

    def __post_init__(self):
        """Set retryable based on reason."""
        if self.reason in [FailureReason.VALIDATION, FailureReason.AUTHENTICATION]:
            self.retryable = False

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            'reason': self.reason.value,
            'message': self.message,
            'details': self.details or {},
            'attempt': self.attempt,
            'max_attempts': self.max_attempts,
            'retryable': self.retryable,
            'timestamp': time.time(),
        }


class ErrorHandler:
    """Central error handling and retry logic."""

    def __init__(self):
        self.error_counts = {reason: 0 for reason in FailureReason}

    def classify_error(self, exception: Exception, context: dict[str, Any]) -> FailureReason:
        """Classify an exception into a failure reason."""
        error_str = str(exception).lower()

        # Check for specific error patterns
        error_patterns = [
            (['connection', 'timeout', 'network', 'unreachable'], FailureReason.NETWORK),
            (['auth', 'unauthorized', 'forbidden', 'token'], FailureReason.AUTHENTICATION),
            (['rate limit', 'throttle', 'quota', '429'], FailureReason.RATE_LIMIT),
            (['memory', 'cpu', 'disk', 'resource'], FailureReason.RESOURCE),
            (['timeout', 'timed out', 'deadline'], FailureReason.TIMEOUT),
            (['validation', 'invalid', 'malformed', 'schema'], FailureReason.VALIDATION),
            (['dependency', 'service unavailable', '503'], FailureReason.DEPENDENCY),
            (['api', 'external', 'integration', 'service'], FailureReason.INTEGRATION),
        ]

        for patterns, reason in error_patterns:
            if any(pattern in error_str for pattern in patterns):
                return reason

        return FailureReason.UNKNOWN

    def create_error(
        self, exception: Exception, context: dict[str, Any], attempt: int = 1
    ) -> AutomationError:
        """Create a structured error from an exception."""
        reason = self.classify_error(exception, context)
        policy = RetryPolicies.get_policy_for_reason(reason)

        return AutomationError(
            reason=reason,
            message=str(exception),
            details=context,
            original_exception=exception,
            attempt=attempt,
            max_attempts=policy.max_attempts,
            retryable=attempt < policy.max_attempts
            and reason not in [FailureReason.VALIDATION, FailureReason.AUTHENTICATION],
        )

    def should_retry(self, error: AutomationError) -> bool:
        """Determine if an error should be retried."""
        if not error.retryable:
            return False

        policy = RetryPolicies.get_policy_for_reason(error.reason)
        return error.attempt < policy.max_attempts

    def get_retry_delay(self, error: AutomationError) -> float:
        """Get delay before next retry attempt."""
        policy = RetryPolicies.get_policy_for_reason(error.reason)
        return policy.get_delay(error.attempt - 1)

    def record_error(self, error: AutomationError, context: dict[str, Any]):
        """Record error for metrics and monitoring."""
        self.error_counts[error.reason] += 1

        # Record in metrics
        intent = context.get('intent', 'unknown')
        department = context.get('department', 'unknown')
        record_manager_failure(error.reason.value, intent, department)

        # Log error details
        print(f'Automation error recorded: {error.reason.value} - {error.message}')
        print(f'Context: {context}')
        print(f'Attempt {error.attempt}/{error.max_attempts}')

    def get_error_summary(self) -> dict[str, Any]:
        """Get summary of all errors recorded."""
        return {
            'total_errors': sum(self.error_counts.values()),
            'errors_by_reason': self.error_counts,
            'most_common': max(self.error_counts.items(), key=lambda x: x[1])[0].value,
        }


def with_retry(
    func: Callable,
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    context: dict[str, Any] | None = None,
) -> Callable:
    """Decorator to add retry logic to functions."""

    def wrapper(*args, **kwargs):
        error_handler = ErrorHandler()
        context_data = context or {}

        for attempt in range(1, max_attempts + 1):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                # Create structured error
                error = error_handler.create_error(e, context_data, attempt)

                # Record error
                error_handler.record_error(error, context_data)

                # Check if we should retry
                if not error_handler.should_retry(error):
                    raise e

                # Get delay before retry
                delay = error_handler.get_retry_delay(error)
                if delay > 0:
                    print(f'Retrying in {delay:.2f} seconds (attempt {attempt}/{max_attempts})')
                    time.sleep(delay)

                # Update context for next attempt
                context_data['attempt'] = attempt
                context_data['last_error'] = error.to_dict()

        # If we get here, all retries failed
        raise RuntimeError(f'Function {func.__name__} failed after {max_attempts} attempts')

    return wrapper


# Global error handler instance
error_handler = ErrorHandler()


def handle_automation_error(
    exception: Exception, context: dict[str, Any], attempt: int = 1
) -> AutomationError:
    """Convenience function to handle automation errors."""
    return error_handler.create_error(exception, context, attempt)


def is_retryable_error(error: AutomationError) -> bool:
    """Check if an error can be retried."""
    return error_handler.should_retry(error)


def get_retry_delay(error: AutomationError) -> float:
    """Get delay before next retry attempt."""
    return error_handler.get_retry_delay(error)
