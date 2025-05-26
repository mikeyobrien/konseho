"""File operation tools for agents."""

import os
from pathlib import Path
from typing import Optional
from konseho.tools.diff_utils import generate_inline_diff, summarize_changes


def file_read(path: str, encoding: str = "utf-8") -> str:
    """Read contents of a file.
    
    Args:
        path: Path to the file to read
        encoding: Text encoding to use (default: utf-8)
        
    Returns:
        File contents as string, or error message if failed
    """
    try:
        # Check if file exists
        if not os.path.exists(path):
            return f"Error: File not found: {path}"
        
        # Try to read the file
        with open(path, 'r', encoding=encoding) as f:
            content = f.read()
            
        # Check for null bytes which indicate binary content
        if '\x00' in content:
            return f"Error: File appears to be binary. Cannot read as text."
            
        return content
            
    except UnicodeDecodeError:
        return f"Error: Unable to decode file with {encoding} encoding. File may be binary."
    except PermissionError:
        return f"Error: Permission denied reading file: {path}"
    except Exception as e:
        return f"Error: Failed to read file: {str(e)}"


def file_write(path: str, content: str, encoding: str = "utf-8", show_diff: bool = True) -> str:
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
        # Read original content if file exists (for diff)
        original_content = ""
        file_exists = os.path.exists(path)
        if file_exists and show_diff:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    original_content = f.read()
            except:
                # If we can't read it, just skip the diff
                show_diff = False
        
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        
        # Write the file
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        
        # Get file size for confirmation
        size = os.path.getsize(path)
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
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        
        # Check if file exists for appropriate message
        file_exists = os.path.exists(path)
        
        # Append to the file
        with open(path, 'a', encoding=encoding) as f:
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