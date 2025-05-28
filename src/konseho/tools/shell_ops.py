"""Shell execution tool for agents."""

import logging
import os
import shlex
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

# Whitelist of allowed commands for basic operations
# This can be extended based on requirements
ALLOWED_COMMANDS = {
    # Basic file operations
    "ls", "dir", "pwd", "cd", "cat", "type", "echo", "grep", "find",
    # Python and package managers
    "python", "python3", "pip", "pip3", "uv", "poetry", "pipenv",
    # Version control
    "git", "hg", "svn",
    # Development tools
    "npm", "yarn", "node", "make", "cargo", "go", "java", "javac",
    # Testing and linting
    "pytest", "unittest", "mypy", "ruff", "black", "flake8", "pylint",
    # System info (safe read-only commands)
    "whoami", "hostname", "date", "which", "where"
}


def validate_command(command: str) -> tuple[bool, str]:
    """Validate command for safety.
    
    Args:
        command: The command to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not command or not command.strip():
        return False, "Empty command provided"
    
    # Extract the base command and parse arguments properly
    try:
        parts = shlex.split(command)
        if not parts:
            return False, "Invalid command format"
        base_command = os.path.basename(parts[0])
    except ValueError as e:
        return False, f"Failed to parse command: {str(e)}"
    
    # Check against whitelist
    if base_command not in ALLOWED_COMMANDS:
        return False, f"Command '{base_command}' is not in the allowed command list"
    
    # For the dangerous pattern check, we need to be smarter about quoted strings
    # shlex.split already handles quotes, so we check the parsed parts
    # and the raw command for patterns that could be dangerous outside quotes
    
    # Check parsed arguments for dangerous patterns
    dangerous_arg_patterns = [
        "../", "..\\",  # Path traversal
    ]
    
    for part in parts[1:]:  # Skip the command itself
        for pattern in dangerous_arg_patterns:
            if pattern in part:
                return False, f"Dangerous pattern '{pattern}' detected in arguments"
    
    # Check for dangerous shell constructs that would require shell=True
    # These should not appear outside of quoted strings
    # We'll use a simple state machine to track if we're in quotes
    dangerous_shell_patterns = [
        "$(", "`",  # Command substitution
        "${",  # Variable expansion
        ";", "|", "&&", "||",  # Shell operators
        ">", "<", ">>", "<<",  # Redirection
        "&",  # Background execution (at end or followed by space)
    ]
    
    # Simple quote tracking - if shlex.split succeeded, the quotes are balanced
    # Now check if dangerous patterns appear outside quotes in the original command
    in_single_quote = False
    in_double_quote = False
    escaped = False
    
    for i, char in enumerate(command):
        if escaped:
            escaped = False
            continue
            
        if char == '\\':
            escaped = True
            continue
            
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            continue
            
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            continue
        
        # If we're not in quotes, check for dangerous patterns
        if not in_single_quote and not in_double_quote:
            for pattern in dangerous_shell_patterns:
                if command[i:i+len(pattern)] == pattern:
                    # Special case: & is OK if it's part of && 
                    if pattern == "&" and i + 1 < len(command) and command[i+1] == "&":
                        continue
                    return False, (
                        f"Dangerous pattern '{pattern}' detected outside quotes"
                    )
    
    # Special check for home directory expansion - only at start of paths
    # Check in parsed arguments
    for part in parts[1:]:
        if part.startswith("~") or part.startswith("~/"):
            return False, "Home directory expansion '~' detected in arguments"
    
    return True, ""


def shell_run(
    command: str,
    cwd: str | None = None,
    timeout: int = 30,
    capture_output: bool = True,
    allow_unsafe: bool = False
) -> dict[str, Any]:
    """Execute shell commands with timeout and output capture.
    
    SECURITY NOTE: This function validates commands against a whitelist
    to prevent command injection. Use allow_unsafe=True only when
    executing trusted, internally-generated commands.
    
    Args:
        command: The command to execute
        cwd: Working directory for the command (default: current directory)
        timeout: Maximum execution time in seconds (default: 30)
        capture_output: Whether to capture stdout/stderr (default: True)
        allow_unsafe: Skip command validation (DANGEROUS - use with caution)
        
    Returns:
        Dictionary with:
            - returncode: Exit code of the command
            - stdout: Standard output (if captured)
            - stderr: Standard error (if captured)
            - error: Error message if command failed to execute
    """
    # Validate command unless explicitly allowed
    if not allow_unsafe:
        is_valid, error_msg = validate_command(command)
        if not is_valid:
            logger.warning(f"Command validation failed: {error_msg}")
            return {"error": error_msg, "returncode": -1, "stdout": "", "stderr": ""}
    
    # Prepare result
    result = {
        "returncode": -1,
        "stdout": "",
        "stderr": ""
    }
    
    try:
        # Always use subprocess with array arguments for safety
        # Parse the command into parts
        try:
            cmd_parts = shlex.split(command)
        except ValueError as e:
            return {
                "error": f"Failed to parse command: {str(e)}", 
                "returncode": -1, 
                "stdout": "", 
                "stderr": ""
            }
        
        # Never use shell=True to prevent injection attacks
        # Run the command with explicit arguments
        completed = subprocess.run(
            cmd_parts,
            cwd=cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=True,  # Return strings instead of bytes
            shell=False  # ALWAYS False for security
        )
        
        # Populate result
        result["returncode"] = completed.returncode
        if capture_output:
            result["stdout"] = completed.stdout if completed.stdout else ""
            result["stderr"] = completed.stderr if completed.stderr else ""
        
    except subprocess.TimeoutExpired:
        result["error"] = f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        result["error"] = f"Command not found: {cmd_parts[0]}"
    except PermissionError:
        result["error"] = "Permission denied executing command"
    except subprocess.SubprocessError as e:
        result["error"] = f"Subprocess error: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
    
    return result


def execute_piped_commands(
    commands: list[str],
    cwd: str | None = None,
    timeout: int = 30
) -> dict[str, Any]:
    """Execute a pipeline of commands safely.
    
    This function allows executing piped commands without using shell=True
    by creating proper subprocess pipelines.
    
    Args:
        commands: List of commands to pipe together
        cwd: Working directory
        timeout: Maximum execution time
        
    Returns:
        Dictionary with execution results
    """
    if not commands:
        return {
            "error": "No commands provided", 
            "returncode": -1, 
            "stdout": "", 
            "stderr": ""
        }
    
    # Validate each command
    for cmd in commands:
        is_valid, error_msg = validate_command(cmd)
        if not is_valid:
            return {
                "error": f"Command validation failed: {error_msg}", 
                "returncode": -1, 
                "stdout": "", 
                "stderr": ""
            }
    
    result = {
        "returncode": -1,
        "stdout": "",
        "stderr": ""
    }
    
    try:
        processes: list[subprocess.Popen[str]] = []
        
        # Create pipeline
        for i, cmd in enumerate(commands):
            cmd_parts = shlex.split(cmd)
            
            if i == 0:
                # First command - no stdin
                proc = subprocess.Popen(
                    cmd_parts,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=cwd
                )
            else:
                # Subsequent commands - pipe from previous
                proc = subprocess.Popen(
                    cmd_parts,
                    stdin=processes[-1].stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=cwd
                )
                # Close the previous process's stdout to allow it to receive SIGPIPE
                if processes[-1].stdout:
                    processes[-1].stdout.close()
            
            processes.append(proc)
        
        # Get output from last process
        stdout, stderr = processes[-1].communicate(timeout=timeout)
        
        # Wait for all processes to complete
        for proc in processes[:-1]:
            proc.wait(timeout=timeout)
        
        result["returncode"] = processes[-1].returncode
        result["stdout"] = stdout if stdout else ""
        result["stderr"] = stderr if stderr else ""
        
    except subprocess.TimeoutExpired:
        # Kill all processes on timeout
        for proc in processes:
            if proc.poll() is None:
                proc.kill()
        result["error"] = f"Pipeline timed out after {timeout} seconds"
    except Exception as e:
        result["error"] = f"Pipeline error: {str(e)}"
    
    return result