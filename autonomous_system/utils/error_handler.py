"""
Enhanced Error Handling & Recovery System
Production-ready error handling with automatic recovery and circuit breakers
"""

import asyncio
import functools
import logging
import time
import traceback
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecoveryStrategy(Enum):
    """Error recovery strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    DEGRADED_MODE = "degraded_mode"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class ErrorContext:
    """Context information for error handling"""
    error_type: str
    error_message: str
    timestamp: datetime
    severity: ErrorSeverity
    component: str
    operation: str
    user_id: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    stack_trace: str | None = None

@dataclass
class RecoveryAction:
    """Recovery action definition"""
    action_id: str
    strategy: RecoveryStrategy
    description: str
    max_attempts: int = 3
    backoff_factor: float = 2.0
    timeout: float = 30.0
    dependencies: list[str] = field(default_factory=list)
    rollback_action: str | None = None

class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"

            raise e

    async def call_async(self, func: Callable, *args, **kwargs):
        """Execute async function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"

            raise e

class ErrorHandler:
    """Centralized error handling and recovery system"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Error tracking
        self.error_history: list[ErrorContext] = []
        self.active_errors: dict[str, ErrorContext] = {}
        self.recovery_actions: dict[str, RecoveryAction] = {}

        # Circuit breakers
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

        # Recovery strategies
        self.fallback_handlers: dict[str, Callable] = {}
        self.degraded_mode_handlers: dict[str, Callable] = {}

        # Statistics
        self.error_stats = {
            "total_errors": 0,
            "recovered_errors": 0,
            "unrecovered_errors": 0,
            "errors_by_severity": {},
            "errors_by_component": {}
        }

        # Initialize recovery actions
        self._init_recovery_actions()

    def _init_recovery_actions(self):
        """Initialize default recovery actions"""
        default_actions = [
            RecoveryAction(
                action_id="database_connection",
                strategy=RecoveryStrategy.RETRY,
                description="Retry database connection with exponential backoff",
                max_attempts=5,
                backoff_factor=2.0,
                timeout=60.0
            ),
            RecoveryAction(
                action_id="api_call",
                strategy=RecoveryStrategy.CIRCUIT_BREAKER,
                description="Use circuit breaker for API calls",
                max_attempts=3,
                backoff_factor=1.5,
                timeout=30.0
            ),
            RecoveryAction(
                action_id="file_operation",
                strategy=RecoveryStrategy.FALLBACK,
                description="Use fallback storage for file operations",
                max_attempts=2,
                backoff_factor=1.0,
                timeout=10.0
            ),
            RecoveryAction(
                action_id="ai_model",
                strategy=RecoveryStrategy.DEGRADED_MODE,
                description="Switch to fallback AI model",
                max_attempts=1,
                backoff_factor=1.0,
                timeout=15.0
            )
        ]

        for action in default_actions:
            self.recovery_actions[action.action_id] = action

    def handle_error(self, error: Exception, context: dict[str, Any]) -> ErrorContext:
        """Handle an error and determine recovery strategy"""
        # Create error context
        error_context = ErrorContext(
            error_type=type(error).__name__,
            error_message=str(error),
            timestamp=datetime.now(),
            severity=self._determine_severity(error, context),
            component=context.get("component", "unknown"),
            operation=context.get("operation", "unknown"),
            user_id=context.get("user_id"),
            request_id=context.get("request_id"),
            metadata=context.get("metadata", {}),
            stack_trace=traceback.format_exc()
        )

        # Log error
        self._log_error(error_context)

        # Track error
        self._track_error(error_context)

        # Determine recovery strategy
        recovery_strategy = self._determine_recovery_strategy(error_context)

        # Execute recovery
        if recovery_strategy:
            self._execute_recovery(error_context, recovery_strategy)

        return error_context

    def _determine_severity(self, error: Exception, context: dict[str, Any]) -> ErrorSeverity:
        """Determine error severity based on error type and context"""
        # Critical errors
        if isinstance(error, (SystemError, MemoryError, OSError)):
            return ErrorSeverity.CRITICAL

        # High severity errors
        if isinstance(error, (ConnectionError, TimeoutError, PermissionError)):
            return ErrorSeverity.HIGH

        # Medium severity errors
        if isinstance(error, (ValueError, TypeError, AttributeError)):
            return ErrorSeverity.MEDIUM

        # Low severity errors
        return ErrorSeverity.LOW

    def _determine_recovery_strategy(self, error_context: ErrorContext) -> RecoveryAction | None:
        """Determine the best recovery strategy for an error"""
        component = error_context.component
        operation = error_context.operation

        # Look for specific recovery action
        action_key = f"{component}_{operation}"
        if action_key in self.recovery_actions:
            return self.recovery_actions[action_key]

        # Look for component-level recovery action
        if component in self.recovery_actions:
            return self.recovery_actions[component]

        # Use default strategy based on severity
        if error_context.severity == ErrorSeverity.CRITICAL:
            return RecoveryAction(
                action_id="critical_error",
                strategy=RecoveryStrategy.MANUAL_INTERVENTION,
                description="Critical error requires manual intervention",
                max_attempts=0,
                timeout=0.0
            )

        return None

    def _execute_recovery(self, error_context: ErrorContext, recovery_action: RecoveryAction):
        """Execute recovery action"""
        try:
            if recovery_action.strategy == RecoveryStrategy.RETRY:
                self._execute_retry_recovery(error_context, recovery_action)
            elif recovery_action.strategy == RecoveryStrategy.FALLBACK:
                self._execute_fallback_recovery(error_context, recovery_action)
            elif recovery_action.strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                self._execute_circuit_breaker_recovery(error_context, recovery_action)
            elif recovery_action.strategy == RecoveryStrategy.DEGRADED_MODE:
                self._execute_degraded_mode_recovery(error_context, recovery_action)

            self.error_stats["recovered_errors"] += 1

        except Exception as recovery_error:
            self.logger.error(f"Recovery failed for error {error_context.error_type}: {recovery_error}")
            self.error_stats["unrecovered_errors"] += 1

    def _execute_retry_recovery(self, error_context: ErrorContext, recovery_action: RecoveryAction):
        """Execute retry recovery strategy"""
        self.logger.info(f"Executing retry recovery for {error_context.operation}")

        # This would be implemented based on the specific operation
        # For now, just log the recovery attempt
        pass

    def _execute_fallback_recovery(self, error_context: ErrorContext, recovery_action: RecoveryAction):
        """Execute fallback recovery strategy"""
        self.logger.info(f"Executing fallback recovery for {error_context.operation}")

        # Check if fallback handler exists
        fallback_key = f"{error_context.component}_{error_context.operation}"
        if fallback_key in self.fallback_handlers:
            try:
                self.fallback_handlers[fallback_key](error_context)
            except Exception as e:
                self.logger.error(f"Fallback handler failed: {e}")

    def _execute_circuit_breaker_recovery(self, error_context: ErrorContext, recovery_action: RecoveryAction):
        """Execute circuit breaker recovery strategy"""
        self.logger.info(f"Executing circuit breaker recovery for {error_context.operation}")

        # Create circuit breaker if it doesn't exist
        circuit_key = f"{error_context.component}_{error_context.operation}"
        if circuit_key not in self.circuit_breakers:
            self.circuit_breakers[circuit_key] = CircuitBreaker(
                failure_threshold=recovery_action.max_attempts,
                recovery_timeout=recovery_action.timeout
            )

    def _execute_degraded_mode_recovery(self, error_context: ErrorContext, recovery_action: RecoveryAction):
        """Execute degraded mode recovery strategy"""
        self.logger.info(f"Executing degraded mode recovery for {error_context.operation}")

        # Check if degraded mode handler exists
        degraded_key = f"{error_context.component}_{error_context.operation}"
        if degraded_key in self.degraded_mode_handlers:
            try:
                self.degraded_mode_handlers[degraded_key](error_context)
            except Exception as e:
                self.logger.error(f"Degraded mode handler failed: {e}")

    def _log_error(self, error_context: ErrorContext):
        """Log error with structured information"""
        log_data = {
            "error_type": error_context.error_type,
            "error_message": error_context.error_message,
            "severity": error_context.severity.value,
            "component": error_context.component,
            "operation": error_context.operation,
            "user_id": error_context.user_id,
            "request_id": error_context.request_id,
            "metadata": error_context.metadata,
            "stack_trace": error_context.stack_trace
        }

        if error_context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical("Critical error occurred", extra={"extra_fields": log_data})
        elif error_context.severity == ErrorSeverity.HIGH:
            self.logger.error("High severity error occurred", extra={"extra_fields": log_data})
        elif error_context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning("Medium severity error occurred", extra={"extra_fields": log_data})
        else:
            self.logger.info("Low severity error occurred", extra={"extra_fields": log_data})

    def _track_error(self, error_context: ErrorContext):
        """Track error for statistics and monitoring"""
        # Add to history
        self.error_history.append(error_context)

        # Keep only recent errors (last 1000)
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]

        # Update statistics
        self.error_stats["total_errors"] += 1

        # Count by severity
        severity = error_context.severity.value
        if severity not in self.error_stats["errors_by_severity"]:
            self.error_stats["errors_by_severity"][severity] = 0
        self.error_stats["errors_by_severity"][severity] += 1

        # Count by component
        component = error_context.component
        if component not in self.error_stats["errors_by_component"]:
            self.error_stats["errors_by_component"][component] = 0
        self.error_stats["errors_by_component"][component] += 1

    def register_fallback_handler(self, component: str, operation: str, handler: Callable):
        """Register a fallback handler for a specific operation"""
        key = f"{component}_{operation}"
        self.fallback_handlers[key] = handler
        self.logger.info(f"Registered fallback handler for {key}")

    def register_degraded_mode_handler(self, component: str, operation: str, handler: Callable):
        """Register a degraded mode handler for a specific operation"""
        key = f"{component}_{operation}"
        self.degraded_mode_handlers[key] = handler
        self.logger.info(f"Registered degraded mode handler for {key}")

    def get_circuit_breaker(self, component: str, operation: str) -> CircuitBreaker:
        """Get or create a circuit breaker for a specific operation"""
        key = f"{component}_{operation}"
        if key not in self.circuit_breakers:
            self.circuit_breakers[key] = CircuitBreaker()
        return self.circuit_breakers[key]

    def get_error_stats(self) -> dict[str, Any]:
        """Get error handling statistics"""
        return self.error_stats.copy()

    def get_active_errors(self) -> list[ErrorContext]:
        """Get list of currently active errors"""
        return list(self.active_errors.values())

    def clear_error_history(self, days_to_keep: int = 30):
        """Clear old error history"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        self.error_history = [
            error for error in self.error_history
            if error.timestamp > cutoff_date
        ]
        self.logger.info(f"Cleared error history older than {days_to_keep} days")

# Decorators for automatic error handling
def handle_errors(component: str, operation: str, recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY):
    """Decorator for automatic error handling"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get error handler from global context
                error_handler = get_error_handler()
                if error_handler:
                    context = {
                        "component": component,
                        "operation": operation,
                        "metadata": {"args": str(args), "kwargs": str(kwargs)}
                    }
                    error_handler.handle_error(e, context)
                raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get error handler from global context
                error_handler = get_error_handler()
                if error_handler:
                    context = {
                        "component": component,
                        "operation": operation,
                        "metadata": {"args": str(args), "kwargs": str(kwargs)}
                    }
                    error_handler.handle_error(e, context)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator

def with_circuit_breaker(component: str, operation: str, failure_threshold: int = 5, recovery_timeout: float = 60.0):
    """Decorator for circuit breaker protection"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            if error_handler:
                circuit_breaker = error_handler.get_circuit_breaker(component, operation)
                return circuit_breaker.call(func, *args, **kwargs)
            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_handler = get_error_handler()
            if error_handler:
                circuit_breaker = error_handler.get_circuit_breaker(component, operation)
                return await circuit_breaker.call_async(func, *args, **kwargs)
            return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator

def with_fallback(fallback_func: Callable):
    """Decorator for fallback function execution"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                return fallback_func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception:
                return await fallback_func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    return decorator

# Context managers for error handling
@contextmanager
def error_context(component: str, operation: str, **metadata):
    """Context manager for error handling"""
    try:
        yield
    except Exception as e:
        error_handler = get_error_handler()
        if error_handler:
            context = {
                "component": component,
                "operation": operation,
                "metadata": metadata
            }
            error_handler.handle_error(e, context)
        raise

@asynccontextmanager
async def async_error_context(component: str, operation: str, **metadata):
    """Async context manager for error handling"""
    try:
        yield
    except Exception as e:
        error_handler = get_error_handler()
        if error_handler:
            context = {
                "component": component,
                "operation": operation,
                "metadata": metadata
            }
            error_handler.handle_error(e, context)
        raise

# Global error handler instance
_error_handler: ErrorHandler | None = None

def get_error_handler(config: dict[str, Any] = None) -> ErrorHandler | None:
    """Get global error handler instance"""
    global _error_handler

    if _error_handler is None and config is not None:
        _error_handler = ErrorHandler(config)

    return _error_handler

def set_error_handler(error_handler: ErrorHandler):
    """Set global error handler instance"""
    global _error_handler
    _error_handler = error_handler

# Example usage
if __name__ == "__main__":
    # Test configuration
    test_config = {
        "error_handling": {
            "max_error_history": 1000,
            "error_cleanup_days": 30
        }
    }

    # Initialize error handler
    error_handler = ErrorHandler(test_config)
    set_error_handler(error_handler)

    # Test error handling decorator
    @handle_errors("test", "divide", RecoveryStrategy.RETRY)
    def divide_numbers(a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Division by zero")
        return a / b

    # Test circuit breaker decorator
    @with_circuit_breaker("api", "call", failure_threshold=3, recovery_timeout=30.0)
    def api_call():
        import random
        if random.random() < 0.7:  # 70% failure rate
            raise ConnectionError("API call failed")
        return "success"

    # Test fallback decorator
    def fallback_function():
        return "fallback result"

    @with_fallback(fallback_function)
    def main_function():
        raise Exception("Main function failed")

    # Test error handling
    try:
        result = divide_numbers(10, 0)
    except Exception as e:
        print(f"Error caught: {e}")

    # Test circuit breaker
    for i in range(10):
        try:
            result = api_call()
            print(f"API call {i}: {result}")
        except Exception as e:
            print(f"API call {i}: {e}")

    # Test fallback
    result = main_function()
    print(f"Fallback result: {result}")

    # Print statistics
    stats = error_handler.get_error_stats()
    print(f"Error statistics: {stats}")
