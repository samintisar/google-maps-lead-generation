"""
Comprehensive logging configuration for n8n workflow integration.
Provides structured logging, error categorization, and monitoring capabilities.
"""
import logging
import logging.handlers
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import sys
import os

class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorCategory(Enum):
    """Error categorization for better monitoring and debugging."""
    CONNECTION_ERROR = "connection_error"
    AUTHENTICATION_ERROR = "authentication_error"
    WORKFLOW_EXECUTION_ERROR = "workflow_execution_error"
    VALIDATION_ERROR = "validation_error"
    API_ERROR = "api_error"
    TIMEOUT_ERROR = "timeout_error"
    CONFIGURATION_ERROR = "configuration_error"
    DATA_ERROR = "data_error"
    SYSTEM_ERROR = "system_error"

class WorkflowLogContext:
    """Context manager for workflow-specific logging."""
    
    def __init__(self, workflow_id: str = None, execution_id: str = None, 
                 lead_id: int = None, organization_id: int = None):
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.lead_id = lead_id
        self.organization_id = organization_id
        self.start_time = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging."""
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "lead_id": self.lead_id,
            "organization_id": self.organization_id,
            "timestamp": self.start_time.isoformat()
        }

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add workflow context if available
        if hasattr(record, 'workflow_context'):
            log_data["workflow_context"] = record.workflow_context
            
        # Add error category if available
        if hasattr(record, 'error_category'):
            log_data["error_category"] = record.error_category.value
            
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
            
        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_data, default=str, ensure_ascii=False)

class N8nLogger:
    """Enhanced logger for n8n workflow operations."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.workflow_context: Optional[WorkflowLogContext] = None
        
    def set_context(self, context: WorkflowLogContext):
        """Set workflow context for subsequent log messages."""
        self.workflow_context = context
        
    def clear_context(self):
        """Clear workflow context."""
        self.workflow_context = None
        
    def _log_with_context(self, level: int, message: str, 
                         error_category: ErrorCategory = None,
                         extra_fields: Dict[str, Any] = None,
                         exc_info: bool = False):
        """Log message with context and categorization."""
        extra = {}
        
        if self.workflow_context:
            extra['workflow_context'] = self.workflow_context.to_dict()
            
        if error_category:
            extra['error_category'] = error_category
            
        if extra_fields:
            extra['extra_fields'] = extra_fields
            
        self.logger.log(level, message, exc_info=exc_info, extra=extra)
        
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
        
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, message, **kwargs)
        
    def warning(self, message: str, error_category: ErrorCategory = None, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, error_category, **kwargs)
        
    def error(self, message: str, error_category: ErrorCategory = None, 
              exc_info: bool = True, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, message, error_category, exc_info=exc_info, **kwargs)
        
    def critical(self, message: str, error_category: ErrorCategory = None,
                exc_info: bool = True, **kwargs):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, error_category, exc_info=exc_info, **kwargs)

class LoggingConfig:
    """Centralized logging configuration."""
    
    @staticmethod
    def setup_logging(
        log_level: str = "INFO",
        log_dir: str = "logs",
        enable_console: bool = True,
        enable_file: bool = True,
        enable_structured: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        Set up comprehensive logging configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files
            enable_console: Enable console logging
            enable_file: Enable file logging
            enable_structured: Enable structured JSON logging
            max_bytes: Maximum size per log file
            backup_count: Number of backup files to keep
        """
        # Create log directory
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            if enable_structured:
                console_handler.setFormatter(StructuredFormatter())
            else:
                console_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                )
            root_logger.addHandler(console_handler)
        
        # File handlers
        if enable_file:
            # General log file
            file_handler = logging.handlers.RotatingFileHandler(
                log_path / "n8n_integration.log",
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            if enable_structured:
                file_handler.setFormatter(StructuredFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                    )
                )
            root_logger.addHandler(file_handler)
            
            # Error-specific log file
            error_handler = logging.handlers.RotatingFileHandler(
                log_path / "n8n_errors.log",
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(StructuredFormatter() if enable_structured 
                                     else logging.Formatter(
                                         '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                                     ))
            root_logger.addHandler(error_handler)
            
            # Workflow execution log file
            workflow_handler = logging.handlers.RotatingFileHandler(
                log_path / "workflow_executions.log",
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            workflow_handler.addFilter(lambda record: hasattr(record, 'workflow_context'))
            workflow_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(workflow_handler)
        
        # Set specific logger levels
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        
        # Create n8n-specific logger
        n8n_logger = logging.getLogger("n8n_integration")
        return n8n_logger

def get_n8n_logger(name: str) -> N8nLogger:
    """Get an enhanced n8n logger instance."""
    return N8nLogger(f"n8n_integration.{name}")

# Error monitoring and metrics
class ErrorMetrics:
    """Track error metrics for monitoring."""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_categories: Dict[ErrorCategory, int] = {}
        self.last_errors: List[Dict[str, Any]] = []
        self.max_last_errors = 100
        
    def record_error(self, error_category: ErrorCategory, error_message: str,
                    context: WorkflowLogContext = None):
        """Record an error for metrics tracking."""
        error_key = f"{error_category.value}:{error_message[:50]}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.error_categories[error_category] = self.error_categories.get(error_category, 0) + 1
        
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": error_category.value,
            "message": error_message,
            "context": context.to_dict() if context else None
        }
        
        self.last_errors.append(error_record)
        if len(self.last_errors) > self.max_last_errors:
            self.last_errors = self.last_errors[-self.max_last_errors:]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary for monitoring."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_categories": {cat.value: count for cat, count in self.error_categories.items()},
            "top_errors": sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "recent_errors": self.last_errors[-10:]
        }

# Global error metrics instance
error_metrics = ErrorMetrics()

# Health check for logging system
def check_logging_health() -> Dict[str, Any]:
    """Check logging system health."""
    try:
        test_logger = get_n8n_logger("health_check")
        test_logger.info("Logging health check")
        
        # Check log directory
        log_dir = Path("logs")
        log_files = list(log_dir.glob("*.log")) if log_dir.exists() else []
        
        return {
            "status": "healthy",
            "log_directory_exists": log_dir.exists(),
            "log_files_count": len(log_files),
            "log_files": [f.name for f in log_files],
            "error_metrics": error_metrics.get_error_summary()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        } 