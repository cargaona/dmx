"""Comprehensive error handling and validation for dmx."""

import logging
import traceback
import sys
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from functools import wraps
from pathlib import Path
import re
from dataclasses import dataclass
from enum import Enum

# Type variable for decorators
F = TypeVar('F', bound=Callable[..., Any])

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for errors."""
    operation: str
    user_input: Optional[str] = None
    file_path: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class ValidationError(Exception):
    """Input validation error."""
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message)
        self.field = field
        self.value = value


class ConfigurationError(Exception):
    """Configuration-related error."""
    pass


class NetworkError(Exception):
    """Network-related error."""
    pass


class DownloadError(Exception):
    """Download-related error."""
    pass


class ErrorHandler:
    """Centralized error handling and logging."""
    
    def __init__(self, debug_mode: bool = False, log_file: Optional[Path] = None):
        self.debug_mode = debug_mode
        self.log_file = log_file
        self.error_counts = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create logger
        self.logger = logging.getLogger('dmx')
        self.logger.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Format for console (user-friendly)
        console_format = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Detailed format for file
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def handle_error(self, 
                    error: Exception, 
                    context: ErrorContext, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    user_message: Optional[str] = None) -> bool:
        """
        Handle an error with appropriate logging and user feedback.
        
        Returns:
            bool: True if the error can be recovered from, False otherwise
        """
        error_type = type(error).__name__
        
        # Count errors for analysis
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log the error
        log_message = f"{context.operation}: {str(error)}"
        
        if self.debug_mode:
            log_message += f"\nTraceback: {traceback.format_exc()}"
        
        if context.user_input:
            log_message += f"\nUser input: {context.user_input}"
        
        if context.additional_info:
            log_message += f"\nAdditional info: {context.additional_info}"
        
        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Provide user feedback
        if user_message:
            print(f"Error: {user_message}")
        elif isinstance(error, ValidationError):
            print(f"Invalid input: {str(error)}")
        elif isinstance(error, NetworkError):
            print("Network error: Please check your internet connection and try again.")
        elif isinstance(error, ConfigurationError):
            print(f"Configuration error: {str(error)}")
        elif isinstance(error, DownloadError):
            print(f"Download failed: {str(error)}")
        else:
            print(f"An error occurred: {str(error)}")
        
        # Determine if recoverable
        recoverable_errors = (ValidationError, NetworkError)
        return isinstance(error, recoverable_errors) and severity != ErrorSeverity.CRITICAL
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics."""
        return self.error_counts.copy()


def handle_errors(operation: str, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 user_message: Optional[str] = None,
                 reraise: bool = False) -> Callable[[F], F]:
    """
    Decorator for automatic error handling.
    
    Args:
        operation: Description of the operation being performed
        severity: Error severity level
        user_message: Custom message to show to user
        reraise: Whether to reraise the exception after handling
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Try to get error handler from instance
                error_handler = None
                if args and hasattr(args[0], 'error_handler'):
                    error_handler = args[0].error_handler
                else:
                    # Create default error handler
                    error_handler = ErrorHandler()
                
                context = ErrorContext(
                    operation=operation,
                    additional_info={'function': func.__name__, 'args': str(args[:3])}
                )
                
                recoverable = error_handler.handle_error(e, context, severity, user_message)
                
                if reraise or not recoverable:
                    raise
                
                return None
        
        return wrapper
    return decorator


class InputValidator:
    """Input validation utilities."""
    
    @staticmethod
    def validate_search_query(query: str) -> str:
        """Validate and sanitize search query."""
        if not query or not query.strip():
            raise ValidationError("Search query cannot be empty", "query", query)
        
        # Clean the query
        query = query.strip()
        
        # Check length
        if len(query) > 500:
            raise ValidationError("Search query too long (max 500 characters)", "query", query)
        
        # Remove potentially harmful characters
        query = re.sub(r'[<>"\']', '', query)
        
        return query
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate music service URL."""
        if not url or not url.strip():
            raise ValidationError("URL cannot be empty", "url", url)
        
        url = url.strip()
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(url):
            raise ValidationError("Invalid URL format", "url", url)
        
        # Check for supported domains
        supported_domains = ['deezer.com', 'spotify.com', 'musicbrainz.org']
        if not any(domain in url.lower() for domain in supported_domains):
            raise ValidationError(f"Unsupported URL. Supported domains: {', '.join(supported_domains)}", "url", url)
        
        return url
    
    @staticmethod
    def validate_quality(quality: str) -> str:
        """Validate audio quality setting."""
        if not quality:
            raise ValidationError("Quality cannot be empty", "quality", quality)
        
        valid_qualities = ["128", "320", "FLAC"]
        if quality not in valid_qualities:
            raise ValidationError(f"Invalid quality. Supported: {', '.join(valid_qualities)}", "quality", quality)
        
        return quality
    
    @staticmethod
    def validate_path(path: str, must_exist: bool = False, must_be_dir: bool = False) -> Path:
        """Validate file/directory path."""
        if not path or not path.strip():
            raise ValidationError("Path cannot be empty", "path", path)
        
        try:
            path_obj = Path(path).expanduser().resolve()
        except (OSError, ValueError) as e:
            raise ValidationError(f"Invalid path: {e}", "path", path)
        
        if must_exist and not path_obj.exists():
            raise ValidationError("Path does not exist", "path", path)
        
        if must_be_dir and path_obj.exists() and not path_obj.is_dir():
            raise ValidationError("Path must be a directory", "path", path)
        
        return path_obj
    
    @staticmethod
    def validate_limit(limit: Union[str, int], min_val: int = 1, max_val: int = 100) -> int:
        """Validate search result limit."""
        try:
            limit_int = int(limit)
        except (ValueError, TypeError):
            raise ValidationError("Limit must be a number", "limit", limit)
        
        if limit_int < min_val or limit_int > max_val:
            raise ValidationError(f"Limit must be between {min_val} and {max_val}", "limit", limit)
        
        return limit_int


class SafetyChecker:
    """Safety checks for operations."""
    
    @staticmethod
    def check_disk_space(path: Path, required_mb: int = 100) -> bool:
        """Check if enough disk space is available."""
        try:
            import shutil
            free_bytes = shutil.disk_usage(path).free
            free_mb = free_bytes / (1024 * 1024)
            return free_mb >= required_mb
        except Exception:
            # If we can't check, assume it's okay
            return True
    
    @staticmethod
    def check_network_connectivity() -> bool:
        """Basic network connectivity check."""
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file operations."""
        # Remove/replace dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250 - len(ext)] + ('.' + ext if ext else '')
        
        return filename or 'untitled'