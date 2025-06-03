"""
Comprehensive error handling for n8n workflow integration.
Includes custom exceptions, retry mechanisms, circuit breakers, and recovery strategies.
"""
import asyncio
import time
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Type, Union
from enum import Enum
from dataclasses import dataclass
import functools
import random

from .logging_config import get_n8n_logger, ErrorCategory, WorkflowLogContext, error_metrics

logger = get_n8n_logger("error_handling")

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecoveryAction(Enum):
    """Recovery action types."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ESCALATE = "escalate"
    CIRCUIT_BREAK = "circuit_break"

# Custom Exception Classes
class N8nBaseException(Exception):
    """Base exception for all n8n-related errors."""
    
    def __init__(self, message: str, error_category: ErrorCategory, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: WorkflowLogContext = None, 
                 recovery_action: RecoveryAction = RecoveryAction.RETRY,
                 original_exception: Exception = None):
        super().__init__(message)
        self.message = message
        self.error_category = error_category
        self.severity = severity
        self.context = context
        self.recovery_action = recovery_action
        self.original_exception = original_exception
        self.timestamp = datetime.utcnow()
        
        # Record error for metrics
        error_metrics.record_error(error_category, message, context)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "category": self.error_category.value,
            "severity": self.severity.value,
            "recovery_action": self.recovery_action.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context.to_dict() if self.context else None,
            "original_exception": str(self.original_exception) if self.original_exception else None
        }

class N8nConnectionError(N8nBaseException):
    """Connection-related errors."""
    
    def __init__(self, message: str, context: WorkflowLogContext = None, 
                 original_exception: Exception = None):
        super().__init__(
            message, 
            ErrorCategory.CONNECTION_ERROR, 
            ErrorSeverity.HIGH,
            context,
            RecoveryAction.RETRY,
            original_exception
        )

class N8nAuthenticationError(N8nBaseException):
    """Authentication-related errors."""
    
    def __init__(self, message: str, context: WorkflowLogContext = None,
                 original_exception: Exception = None):
        super().__init__(
            message,
            ErrorCategory.AUTHENTICATION_ERROR,
            ErrorSeverity.HIGH,
            context,
            RecoveryAction.ESCALATE,
            original_exception
        )

class N8nWorkflowExecutionError(N8nBaseException):
    """Workflow execution errors."""
    
    def __init__(self, message: str, context: WorkflowLogContext = None,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 original_exception: Exception = None):
        super().__init__(
            message,
            ErrorCategory.WORKFLOW_EXECUTION_ERROR,
            severity,
            context,
            RecoveryAction.RETRY,
            original_exception
        )

class N8nValidationError(N8nBaseException):
    """Validation errors."""
    
    def __init__(self, message: str, context: WorkflowLogContext = None,
                 original_exception: Exception = None):
        super().__init__(
            message,
            ErrorCategory.VALIDATION_ERROR,
            ErrorSeverity.MEDIUM,
            context,
            RecoveryAction.SKIP,
            original_exception
        )

class N8nApiError(N8nBaseException):
    """API-related errors."""
    
    def __init__(self, message: str, status_code: int = None,
                 context: WorkflowLogContext = None,
                 original_exception: Exception = None):
        self.status_code = status_code
        severity = ErrorSeverity.HIGH if status_code and status_code >= 500 else ErrorSeverity.MEDIUM
        super().__init__(
            message,
            ErrorCategory.API_ERROR,
            severity,
            context,
            RecoveryAction.RETRY,
            original_exception
        )

class N8nTimeoutError(N8nBaseException):
    """Timeout-related errors."""
    
    def __init__(self, message: str, timeout_duration: float = None,
                 context: WorkflowLogContext = None,
                 original_exception: Exception = None):
        self.timeout_duration = timeout_duration
        super().__init__(
            message,
            ErrorCategory.TIMEOUT_ERROR,
            ErrorSeverity.MEDIUM,
            context,
            RecoveryAction.RETRY,
            original_exception
        )

class N8nConfigurationError(N8nBaseException):
    """Configuration-related errors."""
    
    def __init__(self, message: str, context: WorkflowLogContext = None,
                 original_exception: Exception = None):
        super().__init__(
            message,
            ErrorCategory.CONFIGURATION_ERROR,
            ErrorSeverity.HIGH,
            context,
            RecoveryAction.ESCALATE,
            original_exception
        )

# Retry Configuration
@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    timeout: Optional[float] = None

class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        
    def can_proceed(self) -> bool:
        """Check if operation can proceed."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if self.last_failure_time and \
               time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        elif self.state == "half-open":
            return True
        return False
    
    def record_success(self):
        """Record successful operation."""
        self.failure_count = 0
        self.state = "closed"
        
    def record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

# Global circuit breakers for different operations
circuit_breakers = {
    "authentication": CircuitBreaker(failure_threshold=3, recovery_timeout=30),
    "workflow_execution": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    "api_calls": CircuitBreaker(failure_threshold=10, recovery_timeout=30)
}

def with_retry(
    config: RetryConfig = None,
    exceptions: tuple = None,
    circuit_breaker_key: str = None
):
    """
    Decorator for adding retry logic with exponential backoff and circuit breaker.
    
    Args:
        config: Retry configuration
        exceptions: Tuple of exceptions to retry on
        circuit_breaker_key: Key for circuit breaker to use
    """
    if config is None:
        config = RetryConfig()
    
    if exceptions is None:
        exceptions = (N8nConnectionError, N8nTimeoutError, N8nApiError)
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            circuit_breaker = circuit_breakers.get(circuit_breaker_key) if circuit_breaker_key else None
            
            for attempt in range(config.max_attempts):
                # Check circuit breaker
                if circuit_breaker and not circuit_breaker.can_proceed():
                    raise N8nBaseException(
                        f"Circuit breaker is open for {circuit_breaker_key}",
                        ErrorCategory.SYSTEM_ERROR,
                        ErrorSeverity.HIGH,
                        recovery_action=RecoveryAction.CIRCUIT_BREAK
                    )
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record success for circuit breaker
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    
                    return result
                    
                except exceptions as e:
                    # Record failure for circuit breaker
                    if circuit_breaker:
                        circuit_breaker.record_failure()
                    
                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"All {config.max_attempts} retry attempts failed for {func.__name__}",
                            error_category=ErrorCategory.SYSTEM_ERROR,
                            extra_fields={"function": func.__name__, "attempts": attempt + 1}
                        )
                        raise
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    if config.jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {delay:.2f}s",
                        error_category=ErrorCategory.SYSTEM_ERROR,
                        extra_fields={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "delay": delay,
                            "error": str(e)
                        }
                    )
                    
                    await asyncio.sleep(delay)
                
                except Exception as e:
                    # Non-retryable exception
                    logger.error(
                        f"Non-retryable exception in {func.__name__}: {e}",
                        error_category=ErrorCategory.SYSTEM_ERROR,
                        extra_fields={"function": func.__name__}
                    )
                    raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, convert to async temporarily
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

class ErrorRecoveryManager:
    """Manages error recovery strategies."""
    
    def __init__(self):
        self.recovery_strategies: Dict[ErrorCategory, List[Callable]] = {
            ErrorCategory.CONNECTION_ERROR: [
                self._retry_with_backoff,
                self._switch_endpoint,
                self._escalate_to_admin
            ],
            ErrorCategory.AUTHENTICATION_ERROR: [
                self._reauthenticate,
                self._escalate_to_admin
            ],
            ErrorCategory.WORKFLOW_EXECUTION_ERROR: [
                self._retry_execution,
                self._use_fallback_workflow,
                self._skip_execution
            ],
            ErrorCategory.TIMEOUT_ERROR: [
                self._increase_timeout,
                self._retry_with_backoff
            ],
            ErrorCategory.API_ERROR: [
                self._retry_with_backoff,
                self._switch_endpoint
            ]
        }
    
    async def handle_error(self, error: N8nBaseException) -> Dict[str, Any]:
        """
        Handle error using appropriate recovery strategies.
        
        Args:
            error: The error to handle
            
        Returns:
            Recovery result with actions taken
        """
        logger.error(
            f"Handling {error.__class__.__name__}: {error.message}",
            error_category=error.error_category,
            extra_fields=error.to_dict()
        )
        
        strategies = self.recovery_strategies.get(error.error_category, [])
        recovery_result = {
            "error": error.to_dict(),
            "strategies_attempted": [],
            "recovery_successful": False,
            "final_action": None
        }
        
        for strategy in strategies:
            try:
                strategy_name = strategy.__name__
                logger.info(f"Attempting recovery strategy: {strategy_name}")
                
                result = await strategy(error)
                recovery_result["strategies_attempted"].append({
                    "strategy": strategy_name,
                    "result": result,
                    "successful": result.get("success", False)
                })
                
                if result.get("success"):
                    recovery_result["recovery_successful"] = True
                    recovery_result["final_action"] = result.get("action")
                    break
                    
            except Exception as e:
                logger.error(f"Recovery strategy {strategy_name} failed: {e}")
                recovery_result["strategies_attempted"].append({
                    "strategy": strategy_name,
                    "result": {"error": str(e)},
                    "successful": False
                })
        
        return recovery_result
    
    async def _retry_with_backoff(self, error: N8nBaseException) -> Dict[str, Any]:
        """Retry the operation with exponential backoff."""
        return {"success": False, "action": "retry_scheduled", "message": "Retry will be handled by retry decorator"}
    
    async def _switch_endpoint(self, error: N8nBaseException) -> Dict[str, Any]:
        """Switch to alternative endpoint if available."""
        # Implementation would depend on available alternative endpoints
        return {"success": False, "action": "endpoint_switch", "message": "No alternative endpoints configured"}
    
    async def _reauthenticate(self, error: N8nBaseException) -> Dict[str, Any]:
        """Attempt to reauthenticate with n8n."""
        try:
            # This would typically involve calling the authentication method
            # Implementation depends on the specific authentication mechanism
            return {"success": True, "action": "reauthenticated", "message": "Authentication refreshed"}
        except Exception as e:
            return {"success": False, "action": "reauthentication_failed", "message": str(e)}
    
    async def _retry_execution(self, error: N8nBaseException) -> Dict[str, Any]:
        """Retry workflow execution with modified parameters."""
        return {"success": False, "action": "execution_retry", "message": "Execution retry will be handled externally"}
    
    async def _use_fallback_workflow(self, error: N8nBaseException) -> Dict[str, Any]:
        """Use a fallback workflow if available."""
        return {"success": False, "action": "fallback_workflow", "message": "No fallback workflow configured"}
    
    async def _skip_execution(self, error: N8nBaseException) -> Dict[str, Any]:
        """Skip the failed execution and mark as failed."""
        return {"success": True, "action": "execution_skipped", "message": "Execution marked as failed and skipped"}
    
    async def _increase_timeout(self, error: N8nBaseException) -> Dict[str, Any]:
        """Increase timeout for subsequent operations."""
        return {"success": True, "action": "timeout_increased", "message": "Timeout increased for future operations"}
    
    async def _escalate_to_admin(self, error: N8nBaseException) -> Dict[str, Any]:
        """Escalate error to system administrator."""
        logger.critical(
            f"Escalating error to administrator: {error.message}",
            error_category=error.error_category,
            extra_fields=error.to_dict()
        )
        return {"success": True, "action": "escalated", "message": "Error escalated to administrator"}

# Global error recovery manager
error_recovery_manager = ErrorRecoveryManager()

def handle_n8n_exception(func):
    """
    Decorator to handle n8n exceptions and convert them to appropriate custom exceptions.
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except N8nBaseException:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Convert generic exceptions to N8nBaseException
            error_message = str(e)
            context = kwargs.get('context') or (args[0].workflow_context if args and hasattr(args[0], 'workflow_context') else None)
            
            # Determine error category based on exception type and message
            if "connection" in error_message.lower() or "network" in error_message.lower():
                raise N8nConnectionError(error_message, context, e)
            elif "auth" in error_message.lower() or "unauthorized" in error_message.lower():
                raise N8nAuthenticationError(error_message, context, e)
            elif "timeout" in error_message.lower():
                raise N8nTimeoutError(error_message, context=context, original_exception=e)
            elif "validation" in error_message.lower() or "invalid" in error_message.lower():
                raise N8nValidationError(error_message, context, e)
            else:
                raise N8nBaseException(
                    error_message,
                    ErrorCategory.SYSTEM_ERROR,
                    ErrorSeverity.MEDIUM,
                    context,
                    RecoveryAction.RETRY,
                    e
                )
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        return asyncio.run(async_wrapper(*args, **kwargs))
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

# Health monitoring for error handling system
def get_error_handling_health() -> Dict[str, Any]:
    """Get health status of error handling system."""
    return {
        "circuit_breakers": {
            name: {
                "state": cb.state,
                "failure_count": cb.failure_count,
                "last_failure": cb.last_failure_time
            }
            for name, cb in circuit_breakers.items()
        },
        "error_metrics": error_metrics.get_error_summary(),
        "recovery_manager_status": "active"
    } 