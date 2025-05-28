# File Operations Security

## Overview

The file operation tools (`file_read`, `file_write`, `file_append`) in Konseho now include path validation to prevent path traversal attacks and unauthorized file system access.

## Security Features

1. **Path Validation**: All file paths are validated against a list of allowed directories
2. **Symlink Resolution**: Symlinks are resolved to prevent escaping allowed directories
3. **Path Traversal Protection**: Attempts to use `../` or absolute paths outside allowed directories are blocked
4. **Default Safety**: When no directories are configured, operations are restricted to the current working directory

## Configuration

### Setting Allowed Directories

```python
from konseho.tools.file_ops import configure_allowed_directories

# Configure allowed directories for file operations
configure_allowed_directories([
    "/path/to/project",
    "/tmp/safe_dir",
    "./relative/path"  # Will be resolved to absolute path
])
```

### Getting Current Configuration

```python
from konseho.tools.file_ops import get_allowed_directories

# Check which directories are currently allowed
allowed = get_allowed_directories()
print(f"Allowed directories: {allowed}")
```

## Usage with Agents

When creating agents that need file access, ensure you configure allowed directories first:

```python
from konseho.agents.base import create_agent
from konseho.tools.file_ops import configure_allowed_directories, file_read, file_write

# Configure safe directories
configure_allowed_directories(["/safe/project/dir"])

# Create agent with file tools
agent = create_agent(
    name="FileAgent",
    tools=[file_read, file_write],
    system_prompt="You can read and write files in the project directory."
)
```

## Security Best Practices

1. **Principle of Least Privilege**: Only allow access to directories that agents actually need
2. **Avoid Root Directories**: Never allow access to system directories like `/`, `/etc`, `/home`
3. **Project Isolation**: Configure different allowed directories for different projects
4. **Temporary Files**: Use a dedicated temporary directory for transient file operations

## Error Handling

When a file operation is blocked, you'll receive an error message:

```
Error: Path '/etc/passwd' is outside allowed directories. Allowed: /home/user/project
```

## Testing

The security features are thoroughly tested in `tests/unit/test_file_ops_security.py`, including:

- Path traversal attempts
- Symlink escape attempts
- Absolute path restrictions
- Multiple allowed directories
- Parent directory validation

## Migration Guide

If you have existing code using file operations, you need to:

1. Add `configure_allowed_directories()` before using file operations
2. Ensure your tests configure allowed directories appropriately
3. Review any hardcoded paths to ensure they'll be within allowed directories

Example migration:

```python
# Old code (vulnerable)
result = file_read("/etc/passwd")  # This would work!

# New code (secure)
configure_allowed_directories(["/my/project"])
result = file_read("/etc/passwd")  # Error: outside allowed directories
result = file_read("/my/project/config.txt")  # This works
```