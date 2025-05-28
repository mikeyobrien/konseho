"""Security tests for file operation tools."""

import os
import tempfile
from pathlib import Path

import pytest

from konseho.tools.file_ops import (
    configure_allowed_directories,
    file_append,
    file_read,
    file_write,
    get_allowed_directories,
    validate_file_path,
)


class TestPathValidation:
    """Test path validation security features."""

    def test_validate_simple_allowed_path(self, tmp_path):
        """Test validation of a simple allowed path."""
        configure_allowed_directories([str(tmp_path)])
        
        test_file = tmp_path / "test.txt"
        is_valid, resolved, error = validate_file_path(str(test_file))
        
        assert is_valid is True
        assert resolved == str(test_file.absolute())
        assert error == ""

    def test_validate_path_traversal_blocked(self, tmp_path):
        """Test that path traversal attempts are blocked."""
        configure_allowed_directories([str(tmp_path)])
        
        # Try to escape using ../
        evil_path = str(tmp_path / ".." / ".." / "etc" / "passwd")
        is_valid, resolved, error = validate_file_path(evil_path)
        
        assert is_valid is False
        assert "outside allowed directories" in error
        assert resolved == ""

    def test_validate_absolute_path_blocked(self, tmp_path):
        """Test that absolute paths outside allowed dirs are blocked."""
        configure_allowed_directories([str(tmp_path)])
        
        # Try to access system files directly
        is_valid, resolved, error = validate_file_path("/etc/passwd")
        
        assert is_valid is False
        assert "outside allowed directories" in error

    def test_validate_symlink_escape_blocked(self, tmp_path):
        """Test that symlinks cannot be used to escape allowed directories."""
        configure_allowed_directories([str(tmp_path)])
        
        # Create a symlink pointing outside allowed directory
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        outside_file = outside_dir / "secret.txt"
        outside_file.write_text("secret data")
        
        # Create symlink inside allowed directory pointing outside
        symlink = tmp_path / "escape_link"
        symlink.symlink_to(outside_file)
        
        # Try to validate the symlink - should fail
        is_valid, resolved, error = validate_file_path(str(symlink))
        
        assert is_valid is False
        assert "outside allowed directories" in error

    def test_validate_nested_paths_allowed(self, tmp_path):
        """Test that nested paths within allowed directories work."""
        configure_allowed_directories([str(tmp_path)])
        
        nested = tmp_path / "a" / "b" / "c" / "file.txt"
        is_valid, resolved, error = validate_file_path(str(nested))
        
        assert is_valid is True
        assert error == ""

    def test_validate_multiple_allowed_dirs(self, tmp_path):
        """Test validation with multiple allowed directories."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        
        configure_allowed_directories([str(dir1), str(dir2)])
        
        # Both directories should be allowed
        file1 = dir1 / "file1.txt"
        file2 = dir2 / "file2.txt"
        
        is_valid1, _, _ = validate_file_path(str(file1))
        is_valid2, _, _ = validate_file_path(str(file2))
        
        assert is_valid1 is True
        assert is_valid2 is True
        
        # Parent directory should not be allowed
        parent_file = tmp_path / "file.txt"
        is_valid3, _, error = validate_file_path(str(parent_file))
        
        assert is_valid3 is False
        assert "outside allowed directories" in error

    def test_default_to_cwd_when_no_dirs_configured(self):
        """Test that validation defaults to CWD when no dirs configured."""
        # Clear configured directories
        configure_allowed_directories([])
        
        # Should default to current working directory
        cwd_file = Path.cwd() / "test.txt"
        is_valid, _, _ = validate_file_path(str(cwd_file))
        
        assert is_valid is True
        assert get_allowed_directories() == [os.getcwd()]

    def test_validate_handles_invalid_paths(self):
        """Test validation handles completely invalid paths gracefully."""
        configure_allowed_directories(["/tmp"])
        
        # Test with null bytes
        is_valid, _, error = validate_file_path("/tmp/file\x00.txt")
        assert is_valid is False
        assert "Invalid path" in error
        
        # Test with empty path
        is_valid, _, error = validate_file_path("")
        assert is_valid is False


class TestFileOperationsSecurity:
    """Test that file operations properly enforce path validation."""

    def test_file_read_blocked_outside_allowed(self, tmp_path):
        """Test file_read blocks access outside allowed directories."""
        configure_allowed_directories([str(tmp_path)])
        
        # Try to read /etc/passwd
        result = file_read("/etc/passwd")
        assert "Error:" in result
        assert "outside allowed directories" in result

    def test_file_write_blocked_outside_allowed(self, tmp_path):
        """Test file_write blocks writing outside allowed directories."""
        configure_allowed_directories([str(tmp_path)])
        
        # Try to write to /tmp (outside allowed)
        result = file_write("/tmp/evil.txt", "malicious content")
        assert "Error:" in result
        assert "outside allowed directories" in result

    def test_file_append_blocked_outside_allowed(self, tmp_path):
        """Test file_append blocks appending outside allowed directories."""
        configure_allowed_directories([str(tmp_path)])
        
        # Try to append to /etc/hosts
        result = file_append("/etc/hosts", "127.0.0.1 evil.com")
        assert "Error:" in result
        assert "outside allowed directories" in result

    def test_file_operations_with_path_traversal(self, tmp_path):
        """Test that path traversal in file operations is blocked."""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()
        configure_allowed_directories([str(safe_dir)])
        
        # Create a file in the safe directory
        safe_file = safe_dir / "safe.txt"
        safe_file.write_text("safe content")
        
        # Try to escape using path traversal
        evil_path = str(safe_dir / ".." / ".." / "etc" / "passwd")
        
        # All operations should fail
        read_result = file_read(evil_path)
        assert "Error:" in read_result
        assert "outside allowed directories" in read_result
        
        write_result = file_write(evil_path, "evil")
        assert "Error:" in write_result
        assert "outside allowed directories" in write_result
        
        append_result = file_append(evil_path, "evil")
        assert "Error:" in append_result
        assert "outside allowed directories" in append_result

    def test_file_write_parent_dir_validation(self, tmp_path):
        """Test that file_write validates parent directory creation."""
        safe_dir = tmp_path / "safe"
        safe_dir.mkdir()
        configure_allowed_directories([str(safe_dir)])
        
        # Try to create a file that would create parent dirs outside allowed
        evil_path = str(safe_dir / ".." / "evil" / "file.txt")
        result = file_write(evil_path, "content")
        
        assert "Error:" in result
        assert "outside allowed directories" in result

    def test_allowed_operations_still_work(self, tmp_path):
        """Test that legitimate operations within allowed dirs still work."""
        configure_allowed_directories([str(tmp_path)])
        
        # Create test file
        test_file = tmp_path / "test.txt"
        
        # Write should work
        write_result = file_write(str(test_file), "Hello, World!")
        assert "Success" in write_result
        assert test_file.read_text() == "Hello, World!"
        
        # Read should work
        read_result = file_read(str(test_file))
        assert read_result == "Hello, World!"
        
        # Append should work
        append_result = file_append(str(test_file), " More text")
        assert "Success" in append_result
        assert test_file.read_text() == "Hello, World! More text"

    def test_configure_allowed_directories_resolves_paths(self, tmp_path):
        """Test that configure_allowed_directories resolves relative paths."""
        # Create a directory with a relative path
        rel_dir = tmp_path / "relative"
        rel_dir.mkdir()
        
        # Change to parent directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Configure with relative path
            configure_allowed_directories(["./relative"])
            
            # Should be resolved to absolute
            allowed = get_allowed_directories()
            assert len(allowed) == 1
            assert os.path.isabs(allowed[0])
            assert allowed[0] == str(rel_dir.absolute())
            
        finally:
            os.chdir(original_cwd)

    def test_empty_directory_list_ignored(self):
        """Test that empty strings in directory list are ignored."""
        configure_allowed_directories(["/tmp", "", "/var"])
        
        allowed = get_allowed_directories()
        assert "" not in allowed
        assert len(allowed) == 2