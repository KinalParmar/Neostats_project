import pytest
from app.validation.file_validator import FileValidator
from unittest.mock import Mock
import io


class TestFileValidator:
    """Tests for file validation"""
    
    def test_empty_file_rejection(self):
        """Test that empty files are rejected"""
        mock_file = Mock()
        mock_file.filename = "test.pdf"
        mock_file.read = Mock(return_value=b"")
        mock_file.seek = Mock()
        
        is_valid, result = FileValidator.validate_file(mock_file)
        
        assert is_valid is False
        assert "File is empty" in result["errors"]
    
    def test_invalid_mime_type(self):
        """Test that invalid MIME types are rejected"""
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.read = Mock(return_value=b"some text content")
        mock_file.seek = Mock()
        
        is_valid, result = FileValidator.validate_file(mock_file)
        
        assert is_valid is False
        assert "Invalid file type" in result["errors"][0]
