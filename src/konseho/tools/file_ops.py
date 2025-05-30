"""File operation tools for agents."""

import os
from pathlib import Path

from konseho.tools.diff_utils import generate_inline_diff, summarize_changes

# Default allowed directories - can be configured via environment or at runtime
_ALLOWED_DIRS: list[str] = []


def configure_allowed_directories(directories: list[str]) -> None:
    """Configure allowed directories for file operations.
    
    Args:
        directories: List of directory paths that are allowed for file operations.
                    These will be resolved to absolute paths.
    """
    global _ALLOWED_DIRS
    _ALLOWED_DIRS = [os.path.abspath(d) for d in directories if d]


def get_allowed_directories() -> list[str]:
    """Get the current list of allowed directories.
    
    Returns:
        List of allowed directory paths
    """
    # If no directories configured, default to current working directory
    if not _ALLOWED_DIRS:
        return [os.getcwd()]
    return _ALLOWED_DIRS.copy()


def validate_file_path(file_path: str) -> tuple[bool, str, str]:
    """Validate that a file path is within allowed directories.
    
    Args:
        file_path: The file path to validate
        
    Returns:
        Tuple of (is_valid, resolved_path, error_message)
        - is_valid: True if path is allowed, False otherwise
        - resolved_path: The absolute resolved path (empty string if invalid)
        - error_message: Error description (empty string if valid)
    """
    try:
        # Resolve to absolute path, following symlinks
        abs_path = os.path.abspath(os.path.realpath(file_path))
        
        # Get allowed directories
        allowed_dirs = get_allowed_directories()
        
        # Check if path is within any allowed directory
        for allowed_dir in allowed_dirs:
            allowed_abs = os.path.abspath(os.path.realpath(allowed_dir))
            # Use Path for reliable path comparison
            if Path(abs_path).is_relative_to(Path(allowed_abs)):
                return True, abs_path, ""
        
        # Path is outside allowed directories
        return False, "", (
            f"Path '{file_path}' is outside allowed directories. "
            f"Allowed: {', '.join(allowed_dirs)}"
        )
        
    except Exception as e:
        return False, "", f"Invalid path '{file_path}': {str(e)}"


def file_read(path: str, encoding: str = "utf-8") -> str:
    """Read contents of a file.

    Args:
        path: Path to the file to read
        encoding: Text encoding to use (default: utf-8)

    Returns:
        File contents as string, or error message if failed
    """
    try:
        # Validate the path first
        is_valid, resolved_path, error_msg = validate_file_path(path)
        if not is_valid:
            return f"Error: {error_msg}"
        
        # Check if file exists
        if not os.path.exists(resolved_path):
            return f"Error: File not found: {path}"

        # Try to read the file
        with open(resolved_path, encoding=encoding) as f:
            content = f.read()

        # Check for null bytes which indicate binary content
        if "\x00" in content:
            return "Error: File appears to be binary. Cannot read as text."

        return content

    except UnicodeDecodeError:
        return (
            f"Error: Unable to decode file with {encoding} encoding. "
            "File may be binary."
        )
    except PermissionError:
        return f"Error: Permission denied reading file: {path}"
    except Exception as e:
        return f"Error: Failed to read file: {str(e)}"


def file_write(
    path: str, content: str, encoding: str = "utf-8", show_diff: bool = True
) -> str:
    """Write content to a file, creating directories if needed.

    Args:
        path: Path to the file to write
        content: Content to write to the file
        encoding: Text encoding to use (default: utf-8)
        show_diff: Whether to show a diff of changes (default: True)

    Returns:
        Success message with optional diff, or error message if failed
    """
    try:
        # Validate the path first
        is_valid, resolved_path, error_msg = validate_file_path(path)
        if not is_valid:
            return f"Error: {error_msg}"
        
        # Read original content if file exists (for diff)
        original_content = ""
        file_exists = os.path.exists(resolved_path)
        if file_exists and show_diff:
            try:
                with open(resolved_path, encoding=encoding) as f:
                    original_content = f.read()
            except Exception:
                # If we can't read it, just skip the diff
                show_diff = False

        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(resolved_path)
        if parent_dir:
            # Validate parent directory is also within allowed paths
            parent_valid, _, parent_error = validate_file_path(parent_dir)
            if not parent_valid:
                return (
                    f"Error: Parent directory is outside allowed paths: "
                    f"{parent_error}"
                )
            os.makedirs(parent_dir, exist_ok=True)

        # Write the file
        with open(resolved_path, "w", encoding=encoding) as f:
            f.write(content)

        # Get file size for confirmation
        size = os.path.getsize(resolved_path)
        result = f"Success: Written {size} bytes to {path}"

        # Add diff if requested and file existed
        if show_diff and file_exists and original_content != content:
            diff = generate_inline_diff(original_content, content, path)
            summary = summarize_changes(original_content, content)
            result += f"\n\n{summary}\n\n{diff}"
        elif file_exists and original_content == content:
            result += "\n\nNo changes made - file content is identical."

        return result

    except PermissionError:
        return f"Error: Permission denied writing to: {path}"
    except OSError as e:
        if "read-only" in str(e).lower() or "permission" in str(e).lower():
            return f"Error: Permission denied - {str(e)}"
        return f"Error: OS error writing file: {str(e)}"
    except Exception as e:
        return f"Error: Failed to write file: {str(e)}"


def file_append(path: str, content: str, encoding: str = "utf-8") -> str:
    """Append content to an existing file.

    Args:
        path: Path to the file to append to
        content: Content to append to the file
        encoding: Text encoding to use (default: utf-8)

    Returns:
        Success message or error message if failed
    """
    try:
        # Validate the path first
        is_valid, resolved_path, error_msg = validate_file_path(path)
        if not is_valid:
            return f"Error: {error_msg}"
        
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(resolved_path)
        if parent_dir:
            # Validate parent directory is also within allowed paths
            parent_valid, _, parent_error = validate_file_path(parent_dir)
            if not parent_valid:
                return (
                    f"Error: Parent directory is outside allowed paths: "
                    f"{parent_error}"
                )
            os.makedirs(parent_dir, exist_ok=True)

        # Check if file exists for appropriate message
        file_exists = os.path.exists(resolved_path)

        # Append to the file
        with open(resolved_path, "a", encoding=encoding) as f:
            f.write(content)

        # Provide appropriate success message
        if not file_exists:
            return f"Success: Created and appended to {path}"
        else:
            return f"Success: Appended {len(content)} characters to {path}"

    except PermissionError:
        return f"Error: Permission denied appending to: {path}"
    except Exception as e:
        return f"Error: Failed to append to file: {str(e)}"
