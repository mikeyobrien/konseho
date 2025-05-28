"""Shell execution tool for agents."""

import shlex
import subprocess
import sys
from typing import Any


def shell_run(
    command: str, cwd: str | None = None, timeout: int = 30, capture_output: bool = True
) -> dict[str, Any]:
    """Execute shell commands with timeout and output capture.

    Args:
        command: The command to execute
        cwd: Working directory for the command (default: current directory)
        timeout: Maximum execution time in seconds (default: 30)
        capture_output: Whether to capture stdout/stderr (default: True)

    Returns:
        Dictionary with:
            - returncode: Exit code of the command
            - stdout: Standard output (if captured)
            - stderr: Standard error (if captured)
            - error: Error message if command failed to execute
    """
    # Validate command
    if not command or not command.strip():
        return {"error": "Empty command provided"}

    # Prepare result
    result = {"returncode": -1, "stdout": "", "stderr": ""}

    try:
        # Determine if we should use shell mode
        # On Windows, we typically need shell=True for built-in commands
        use_shell = sys.platform == "win32"

        # For non-Windows, we can split the command for safer execution
        # unless it contains shell operators
        if not use_shell and any(
            op in command for op in ["|", ">", "<", "&&", "||", ";"]
        ):
            use_shell = True

        # Prepare subprocess arguments
        subprocess_args = {
            "cwd": cwd,
            "timeout": timeout,
            "capture_output": capture_output,
            "text": True,  # Return strings instead of bytes
            "shell": use_shell,
        }

        # If not using shell on Unix, split the command
        if not use_shell:
            try:
                cmd = shlex.split(command)
            except ValueError as e:
                return {"error": f"Failed to parse command: {str(e)}"}
        else:
            cmd = command

        # Run the command
        completed = subprocess.run(cmd, **subprocess_args)

        # Populate result
        result["returncode"] = completed.returncode
        if capture_output:
            result["stdout"] = completed.stdout if completed.stdout else ""
            result["stderr"] = completed.stderr if completed.stderr else ""

    except subprocess.TimeoutExpired:
        result["error"] = f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        result["error"] = (
            f"Command not found: {command.split()[0] if not use_shell else command}"
        )
    except PermissionError:
        result["error"] = "Permission denied executing command"
    except subprocess.SubprocessError as e:
        result["error"] = f"Subprocess error: {str(e)}"
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"

    return result
