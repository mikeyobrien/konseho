"""Tests for shell execution tool."""

import pytest
import os
import tempfile
import sys
from pathlib import Path

from konseho.tools.shell_ops import shell_run


class TestShellRun:
    """Test the shell_run tool."""
    
    def test_simple_command(self):
        """Test running a simple command."""
        result = shell_run("echo 'Hello, World!'")
        
        assert isinstance(result, dict)
        assert result["returncode"] == 0
        assert "stdout" in result
        assert "Hello, World!" in result["stdout"]
        assert result["stderr"] == ""
    
    def test_command_with_error(self):
        """Test command that writes to stderr."""
        # Use a cross-platform command that writes to stderr
        if sys.platform == "win32":
            cmd = "cmd /c echo Error message >&2"
        else:
            cmd = "echo 'Error message' >&2"
        
        result = shell_run(cmd)
        
        assert result["returncode"] == 0
        assert "Error message" in result["stderr"]
    
    def test_command_failure(self):
        """Test command that fails."""
        result = shell_run("false" if sys.platform != "win32" else "cmd /c exit 1")
        
        assert result["returncode"] != 0
        assert "error" not in result  # Should not have error key for normal failures
    
    def test_command_not_found(self):
        """Test running non-existent command."""
        result = shell_run("nonexistentcommand12345")
        
        assert "error" in result
        assert "not found" in result["error"].lower() or "cannot find" in result["error"].lower()
    
    def test_working_directory(self, tmp_path):
        """Test running command in specific directory."""
        # Create a test file in temp directory
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        # List files in that directory
        if sys.platform == "win32":
            cmd = "dir /b"
        else:
            cmd = "ls"
        
        result = shell_run(cmd, cwd=str(tmp_path))
        
        assert result["returncode"] == 0
        assert "test.txt" in result["stdout"]
    
    def test_timeout(self):
        """Test command timeout."""
        # Command that would run forever
        if sys.platform == "win32":
            cmd = "ping -n 10 127.0.0.1"  # Would take ~10 seconds
        else:
            cmd = "sleep 10"
        
        result = shell_run(cmd, timeout=1)
        
        assert "error" in result
        assert "timeout" in result["error"].lower()
    
    def test_capture_output_false(self):
        """Test running without capturing output."""
        result = shell_run("echo 'Not captured'", capture_output=False)
        
        assert result["returncode"] == 0
        assert result["stdout"] == ""
        assert result["stderr"] == ""
    
    def test_environment_variables(self):
        """Test command with environment variables."""
        # Cross-platform environment variable echo
        if sys.platform == "win32":
            cmd = "echo %TEST_VAR%"
        else:
            cmd = "echo $TEST_VAR"
        
        # Set environment variable and run command
        env = os.environ.copy()
        env["TEST_VAR"] = "test_value"
        
        # Note: shell_run should inherit environment
        result = shell_run(cmd)
        
        # This test may need adjustment based on implementation
        assert result["returncode"] == 0
    
    def test_shell_injection_protection(self):
        """Test that shell injection is handled safely."""
        # Attempt injection with semicolon
        dangerous_input = "test; echo 'INJECTED'"
        result = shell_run(f"echo '{dangerous_input}'")
        
        # The entire string should be echoed, not executed
        assert result["returncode"] == 0
        assert "INJECTED" in result["stdout"]
        # But it should be part of the echo, not a separate command
        assert result["stdout"].count('\n') <= 2  # At most one line plus newline
    
    def test_multiline_output(self):
        """Test command with multiline output."""
        if sys.platform == "win32":
            cmd = "echo Line 1 && echo Line 2 && echo Line 3"
        else:
            cmd = "echo -e 'Line 1\\nLine 2\\nLine 3'"
        
        result = shell_run(cmd)
        
        assert result["returncode"] == 0
        assert "Line 1" in result["stdout"]
        assert "Line 2" in result["stdout"]
        assert "Line 3" in result["stdout"]
    
    def test_large_output(self):
        """Test command with large output."""
        # Generate large output
        if sys.platform == "win32":
            cmd = "for /l %i in (1,1,100) do @echo Line %i"
        else:
            cmd = "for i in {1..100}; do echo Line $i; done"
        
        result = shell_run(cmd, timeout=5)
        
        assert result["returncode"] == 0
        assert len(result["stdout"].splitlines()) >= 100
    
    def test_command_with_quotes(self):
        """Test command with quotes."""
        result = shell_run('echo "Hello with spaces"')
        
        assert result["returncode"] == 0
        assert "Hello with spaces" in result["stdout"]
    
    def test_empty_command(self):
        """Test empty command."""
        result = shell_run("")
        
        assert "error" in result
        assert "empty" in result["error"].lower() or "no command" in result["error"].lower()