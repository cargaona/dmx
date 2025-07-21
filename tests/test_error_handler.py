"""Tests for error handling functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from dmx.error_handler import (
    ErrorHandler, 
    ErrorContext, 
    ErrorSeverity,
    ValidationError,
    InputValidator,
    SafetyChecker,
    handle_errors
)


class TestErrorHandler:
    """Test error handler functionality."""
    
    def test_error_handler_initialization(self, temp_config_dir):
        """Test error handler initialization."""
        log_file = temp_config_dir / "test.log"
        handler = ErrorHandler(debug_mode=True, log_file=log_file)
        
        assert handler.debug_mode is True
        assert handler.log_file == log_file
        assert handler.error_counts == {}
    
    def test_handle_error(self, temp_config_dir):
        """Test error handling."""
        handler = ErrorHandler(debug_mode=True)
        context = ErrorContext("test_operation", "test_input")
        
        error = ValueError("Test error")
        recoverable = handler.handle_error(error, context, ErrorSeverity.MEDIUM)
        
        assert recoverable is False  # ValueError is not in recoverable_errors
        assert handler.error_counts['ValueError'] == 1
    
    def test_error_stats(self, temp_config_dir):
        """Test error statistics."""
        handler = ErrorHandler()
        context = ErrorContext("test")
        
        # Generate some errors
        handler.handle_error(ValueError("error1"), context)
        handler.handle_error(ValueError("error2"), context)
        handler.handle_error(TypeError("error3"), context)
        
        stats = handler.get_error_stats()
        assert stats['ValueError'] == 2
        assert stats['TypeError'] == 1
    
    def test_handle_errors_decorator(self, temp_config_dir):
        """Test error handling decorator."""
        handler = ErrorHandler()
        
        @handle_errors("test_operation")
        def failing_function():
            raise ValueError("Test error")
        
        # Should not raise due to decorator
        result = failing_function()
        assert result is None
    
    def test_handle_errors_decorator_with_reraise(self, temp_config_dir):
        """Test error handling decorator with reraise."""
        @handle_errors("test_operation", reraise=True)
        def failing_function():
            raise ValueError("Test error")
        
        # Should raise due to reraise=True
        with pytest.raises(ValueError):
            failing_function()


class TestInputValidator:
    """Test input validation functionality."""
    
    def test_validate_search_query(self):
        """Test search query validation."""
        validator = InputValidator()
        
        # Valid queries
        assert validator.validate_search_query("test query") == "test query"
        assert validator.validate_search_query("  test  ") == "test"
        
        # Invalid queries
        with pytest.raises(ValidationError):
            validator.validate_search_query("")
        
        with pytest.raises(ValidationError):
            validator.validate_search_query("   ")
        
        with pytest.raises(ValidationError):
            validator.validate_search_query("x" * 501)  # Too long
        
        # Test sanitization
        result = validator.validate_search_query('test "query" <script>')
        assert '"' not in result
        assert '<' not in result
        assert '>' not in result
    
    def test_validate_url(self):
        """Test URL validation."""
        validator = InputValidator()
        
        # Valid URLs
        valid_urls = [
            "https://deezer.com/track/123",
            "https://www.spotify.com/album/456",
            "https://musicbrainz.org/recording/789"
        ]
        
        for url in valid_urls:
            assert validator.validate_url(url) == url
        
        # Invalid URLs
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com",
            "https://unsupported-domain.com/track/123"
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError):
                validator.validate_url(url)
    
    def test_validate_quality(self):
        """Test quality validation."""
        validator = InputValidator()
        
        # Valid qualities
        for quality in ["128", "320", "FLAC"]:
            assert validator.validate_quality(quality) == quality
        
        # Invalid qualities
        invalid_qualities = ["", "256", "MP3", "invalid"]
        
        for quality in invalid_qualities:
            with pytest.raises(ValidationError):
                validator.validate_quality(quality)
    
    def test_validate_path(self, temp_config_dir):
        """Test path validation."""
        validator = InputValidator()
        
        # Valid path
        path_obj = validator.validate_path(str(temp_config_dir))
        assert isinstance(path_obj, Path)
        assert path_obj.exists()
        
        # Invalid paths
        with pytest.raises(ValidationError):
            validator.validate_path("")
        
        # Non-existent path with must_exist=True
        with pytest.raises(ValidationError):
            validator.validate_path("/nonexistent/path", must_exist=True)
    
    def test_validate_limit(self):
        """Test limit validation."""
        validator = InputValidator()
        
        # Valid limits
        assert validator.validate_limit("10") == 10
        assert validator.validate_limit(25) == 25
        
        # Invalid limits
        with pytest.raises(ValidationError):
            validator.validate_limit("not_a_number")
        
        with pytest.raises(ValidationError):
            validator.validate_limit("0")  # Below minimum
        
        with pytest.raises(ValidationError):
            validator.validate_limit("101")  # Above maximum


class TestSafetyChecker:
    """Test safety checker functionality."""
    
    def test_check_disk_space(self, temp_config_dir):
        """Test disk space checking."""
        # Should return True for reasonable requirement
        assert SafetyChecker.check_disk_space(temp_config_dir, 1) is True
        
        # Should return False for unreasonable requirement
        assert SafetyChecker.check_disk_space(temp_config_dir, 999999999) is False
    
    @patch('socket.create_connection')
    def test_check_network_connectivity(self, mock_socket):
        """Test network connectivity checking."""
        # Mock successful connection
        mock_socket.return_value = None
        assert SafetyChecker.check_network_connectivity() is True
        
        # Mock failed connection
        mock_socket.side_effect = OSError()
        assert SafetyChecker.check_network_connectivity() is False
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test dangerous characters
        result = SafetyChecker.sanitize_filename('test<>:"/\\|?*file.mp3')
        assert result == 'test_________file.mp3'
        
        # Test leading/trailing dots and spaces
        result = SafetyChecker.sanitize_filename('  ..test..  ')
        assert result == 'test'
        
        # Test long filename
        long_name = 'x' * 300 + '.mp3'
        result = SafetyChecker.sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith('.mp3')
        
        # Test empty filename
        result = SafetyChecker.sanitize_filename('')
        assert result == 'untitled'


class TestErrorTypes:
    """Test custom error types."""
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Test message", "test_field", "test_value")
        
        assert str(error) == "Test message"
        assert error.field == "test_field"
        assert error.value == "test_value"
    
    def test_error_context(self):
        """Test ErrorContext."""
        context = ErrorContext(
            operation="test_operation",
            user_input="test_input",
            file_path="/test/path",
            additional_info={"key": "value"}
        )
        
        assert context.operation == "test_operation"
        assert context.user_input == "test_input"
        assert context.file_path == "/test/path"
        assert context.additional_info == {"key": "value"}