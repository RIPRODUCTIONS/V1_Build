"""
Production-Ready Logging System
Structured logging with rotation, formatting, and multiple outputs
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
from structlog.stdlib import LoggerFactory


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for production logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        # Add custom fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                          'relativeCreated', 'thread', 'threadName', 'processName', 'process',
                          'getMessage', 'exc_info', 'exc_text', 'stack_info', 'extra_fields']:
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False, default=str)

class ColoredFormatter(logging.Formatter):
    """Colored formatter for development console output"""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Format message
        message = record.getMessage()

        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return f"{color}[{timestamp}] {record.levelname:8s} {record.name}: {message}{reset}"

class LogManager:
    """Centralized logging manager for the autonomous system"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.loggers: dict[str, logging.Logger] = {}
        self.handlers: dict[str, logging.Handler] = {}

        # Initialize logging system
        self._setup_logging()

    def _setup_logging(self):
        """Setup the logging system"""
        # Get logging configuration
        log_config = self.config.get("monitoring", {}).get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO").upper())
        log_format = log_config.get("format", "json")
        log_file = log_config.get("file", "/app/logs/autonomous_system.log")
        max_size = log_config.get("max_size", "100MB")
        backup_count = log_config.get("backup_count", 5)

        # Create logs directory
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Add console handler
        console_handler = self._create_console_handler(log_format, log_level)
        root_logger.addHandler(console_handler)
        self.handlers["console"] = console_handler

        # Add file handler
        file_handler = self._create_file_handler(log_file, max_size, backup_count, log_format, log_level)
        root_logger.addHandler(file_handler)
        self.handlers["file"] = file_handler

        # Add error file handler for errors and above
        error_handler = self._create_error_handler(log_file, max_size, backup_count, log_format)
        root_logger.addHandler(error_handler)
        self.handlers["error"] = error_handler

        # Setup structlog for structured logging
        if log_format == "json":
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )

        # Log system startup
        logging.info("Logging system initialized", extra={
            "extra_fields": {
                "log_level": log_level,
                "log_format": log_format,
                "log_file": log_file,
                "max_size": max_size,
                "backup_count": backup_count
            }
        })

    def _create_console_handler(self, log_format: str, log_level: int) -> logging.Handler:
        """Create console handler"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        if log_format == "json":
            formatter = StructuredFormatter()
        else:
            formatter = ColoredFormatter()

        handler.setFormatter(formatter)
        return handler

    def _create_file_handler(self, log_file: str, max_size: str, backup_count: int,
                           log_format: str, log_level: int) -> logging.Handler:
        """Create file handler with rotation"""
        # Parse max size
        size_bytes = self._parse_size(max_size)

        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=size_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setLevel(log_level)

        if log_format == "json":
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        handler.setFormatter(formatter)
        return handler

    def _create_error_handler(self, log_file: str, max_size: str, backup_count: int,
                            log_format: str) -> logging.Handler:
        """Create error file handler for errors and above"""
        # Parse max size
        size_bytes = self._parse_size(max_size)

        # Create error log file path
        error_log_file = str(Path(log_file).with_suffix('.error.log'))

        handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=size_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setLevel(logging.ERROR)

        if log_format == "json":
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        handler.setFormatter(formatter)
        return handler

    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes"""
        size_str = size_str.upper()

        if size_str.endswith('KB'):
            return int(float(size_str[:-2]) * 1024)
        elif size_str.endswith('MB'):
            return int(float(size_str[:-2]) * 1024 * 1024)
        elif size_str.endswith('GB'):
            return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
        else:
            return int(size_str)

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the specified name"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger

        return self.loggers[name]

    def set_level(self, logger_name: str, level: str | int):
        """Set log level for a specific logger"""
        if isinstance(level, str):
            level = getattr(logging, level.upper())

        logger = self.get_logger(logger_name)
        logger.setLevel(level)

        logging.info(f"Log level set for {logger_name}: {level}")

    def add_context(self, logger_name: str, context: dict[str, Any]):
        """Add context information to a logger"""
        logger = self.get_logger(logger_name)

        # Create a custom log record with extra fields
        class ContextLogRecord(logging.LogRecord):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.extra_fields = context

        # Store context in logger
        logger.context = context

        logging.info(f"Context added to logger {logger_name}", extra={
            "extra_fields": context
        })

    def log_performance(self, operation: str, duration: float, metadata: dict[str, Any] = None):
        """Log performance metrics"""
        log_data = {
            "operation": operation,
            "duration_ms": duration * 1000,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat()
        }

        if metadata:
            log_data.update(metadata)

        logging.info("Performance metric", extra={
            "extra_fields": log_data
        })

    def log_security_event(self, event_type: str, user_id: str, resource: str,
                          action: str, result: str, ip_address: str = None,
                          metadata: dict[str, Any] = None):
        """Log security events"""
        log_data = {
            "event_type": event_type,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "result": result,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat()
        }

        if metadata:
            log_data.update(metadata)

        logging.warning("Security event", extra={
            "extra_fields": log_data
        })

    def log_system_health(self, health_score: float, metrics: dict[str, Any],
                          alerts: list = None):
        """Log system health information"""
        log_data = {
            "health_score": health_score,
            "metrics": metrics,
            "alerts": alerts or [],
            "timestamp": datetime.utcnow().isoformat()
        }

        if health_score < 0.5:
            level = logging.ERROR
        elif health_score < 0.8:
            level = logging.WARNING
        else:
            level = logging.INFO

        logging.log(level, "System health check", extra={
            "extra_fields": log_data
        })

    def log_task_execution(self, task_id: str, task_type: str, status: str,
                          duration: float, metadata: dict[str, Any] = None):
        """Log task execution information"""
        log_data = {
            "task_id": task_id,
            "task_type": task_type,
            "status": status,
            "duration_ms": duration * 1000,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat()
        }

        if metadata:
            log_data.update(metadata)

        logging.info("Task execution", extra={
            "extra_fields": log_data
        })

    def log_error_with_context(self, error: Exception, context: dict[str, Any] = None,
                              logger_name: str = None):
        """Log error with additional context"""
        log_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_traceback": self._get_traceback(error),
            "timestamp": datetime.utcnow().isoformat()
        }

        if context:
            log_data.update(context)

        logger = self.get_logger(logger_name) if logger_name else logging.getLogger()
        logger.error("Error occurred", extra={
            "extra_fields": log_data
        }, exc_info=True)

    def _get_traceback(self, error: Exception) -> str:
        """Get formatted traceback for an error"""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))

    def rotate_logs(self):
        """Manually trigger log rotation"""
        for handler_name, handler in self.handlers.items():
            if hasattr(handler, 'doRollover'):
                handler.doRollover()
                logging.info(f"Log rotation triggered for {handler_name}")

    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files"""
        log_config = self.config.get("monitoring", {}).get("logging", {})
        log_file = log_config.get("file", "/app/logs/autonomous_system.log")
        log_path = Path(log_file)

        if not log_path.exists():
            return

        log_dir = log_path.parent
        current_time = datetime.now()

        for log_file in log_dir.glob("*.log*"):
            if log_file.is_file():
                file_age = current_time - datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_age.days > days_to_keep:
                    try:
                        log_file.unlink()
                        logging.info(f"Cleaned up old log file: {log_file}")
                    except Exception as e:
                        logging.warning(f"Failed to clean up log file {log_file}: {e}")

    def get_log_stats(self) -> dict[str, Any]:
        """Get logging system statistics"""
        stats = {
            "active_loggers": len(self.loggers),
            "active_handlers": len(self.handlers),
            "handler_types": {name: type(handler).__name__ for name, handler in self.handlers.items()},
            "log_levels": {}
        }

        # Get log levels for all loggers
        for name, logger in self.loggers.items():
            stats["log_levels"][name] = logging.getLevelName(logger.level)

        return stats

# Global log manager instance
_log_manager: LogManager | None = None

def get_log_manager(config: dict[str, Any] = None) -> LogManager:
    """Get global log manager instance"""
    global _log_manager

    if _log_manager is None:
        if config is None:
            # Try to load config from environment
            try:
                from ..config.environment import get_config
                config = get_config().to_dict()
            except ImportError:
                config = {}

        _log_manager = LogManager(config)

    return _log_manager

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    log_manager = get_log_manager()
    return log_manager.get_logger(name)

# Convenience functions for common logging operations
def log_performance(operation: str, duration: float, metadata: dict[str, Any] = None):
    """Log performance metrics"""
    log_manager = get_log_manager()
    log_manager.log_performance(operation, duration, metadata)

def log_security_event(event_type: str, user_id: str, resource: str, action: str,
                      result: str, ip_address: str = None, metadata: dict[str, Any] = None):
    """Log security events"""
    log_manager = get_log_manager()
    log_manager.log_security_event(event_type, user_id, resource, action, result, ip_address, metadata)

def log_system_health(health_score: float, metrics: dict[str, Any], alerts: list = None):
    """Log system health information"""
    log_manager = get_log_manager()
    log_manager.log_system_health(health_score, metrics, alerts)

def log_task_execution(task_id: str, task_type: str, status: str, duration: float,
                      metadata: dict[str, Any] = None):
    """Log task execution information"""
    log_manager = get_log_manager()
    log_manager.log_task_execution(task_id, task_type, status, duration, metadata)

def log_error_with_context(error: Exception, context: dict[str, Any] = None, logger_name: str = None):
    """Log error with additional context"""
    log_manager = get_log_manager()
    log_manager.log_error_with_context(error, context, logger_name)

# Example usage
if __name__ == "__main__":
    # Test configuration
    test_config = {
        "monitoring": {
            "logging": {
                "level": "DEBUG",
                "format": "json",
                "file": "test_logs/autonomous_system.log",
                "max_size": "10MB",
                "backup_count": 3
            }
        }
    }

    # Initialize log manager
    log_manager = LogManager(test_config)

    # Get logger
    logger = log_manager.get_logger("test_module")

    # Test different log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    # Test structured logging
    log_manager.log_performance("test_operation", 0.5, {"iterations": 100})
    log_manager.log_security_event("login", "user123", "/auth/login", "POST", "success", "192.168.1.100")
    log_manager.log_system_health(0.95, {"cpu": 0.3, "memory": 0.6})

    # Test error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_manager.log_error_with_context(e, {"test_context": "value"})

    # Get stats
    stats = log_manager.get_log_stats()
    print(f"Log stats: {stats}")
