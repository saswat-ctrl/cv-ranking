import logging
import sys
import structlog
from typing import Any, Dict

def configure_logging(log_level: str = "INFO", json_format: bool = False) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to output logs in JSON format (True) or colored text (False)
    """
    
    # Shared processors for both structlog and standard logging
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Processors specific to structlog
    if json_format:
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer()
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(log_level)),
        cache_logger_on_first_use=True,
    )

    # Configure standard Python logging to use structlog
    # This captures logs from libraries that use standard logging (like uvicorn, sqlalchemy)
    
    # Define a formatter that uses structlog processors
    class StructlogFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            # Add standard log record attributes to event dict
            event_dict = {
                "logger": record.name,
                "level": record.levelname.lower(),
                "event": record.getMessage(),
            }
            
            # Add exception info if present
            if record.exc_info:
                event_dict["exc_info"] = record.exc_info

            # Add extra attributes from the record
            # (This allows passing extra={"foo": "bar"} to standard logging calls)
            for key, value in record.__dict__.items():
                if key not in [
                    "args", "asctime", "created", "exc_info", "exc_text", "filename",
                    "funcName", "levelname", "levelno", "lineno", "module",
                    "msecs", "message", "msg", "name", "pathname", "process",
                    "processName", "relativeCreated", "stack_info", "thread",
                    "threadName",
                ]:
                    event_dict[key] = value

            # Process using structlog
            # We need to manually apply processors here because we are bypassing structlog.configure() wrapper
            # for standard logging interception.
            # However, a simpler way is to use structlog.stdlib.ProcessorFormatter if we used structlog.stdlib.LoggerFactory
            # But we are using PrintLoggerFactory for simplicity in this setup.
            
            # Let's keep it simple: Just use JSONRenderer or ConsoleRenderer directly here
            # or rely on the fact that we want to redirect stdlib logging to stdout/stderr
            
            return super().format(record)

    # Actually, the recommended way to intercept stdlib logs is to use structlog.stdlib.LoggerFactory
    # But for this MVP, let's just configure the root logger to output to stderr
    # and let the application use structlog directly where possible.
    
    # For a robust setup that unifies everything:
    
    if json_format:
        # Use JSON formatter for standard logging
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
    else:
        # Use Console formatter for standard logging
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(),
            foreign_pre_chain=shared_processors,
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    
    # Remove existing handlers (like uvicorn's default) to avoid duplication
    # But be careful not to silence uvicorn startup messages if we do this too early
    # Uvicorn configures its own logging. We might need to override it.
    
    # For now, let's just configure structlog for OUR app usage.
    # And set basic config for root logger.
    
    # Re-configuring structlog to use stdlib for better integration
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
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
