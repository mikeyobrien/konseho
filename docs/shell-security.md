# Shell Command Security

This document describes the security features implemented in `konseho.tools.shell_ops` to prevent command injection and other shell-based attacks.

## Security Features

### 1. Command Whitelisting

Only explicitly allowed commands can be executed. The default whitelist includes:
- Basic file operations: `ls`, `cat`, `echo`, `grep`, etc.
- Development tools: `python`, `git`, `npm`, `make`, etc.
- Testing tools: `pytest`, `mypy`, `ruff`, `black`, etc.

Commands not in the whitelist are rejected by default.

### 2. No Shell Execution

All commands are executed with `shell=False` to prevent shell injection attacks. Commands are parsed into argument arrays using `shlex.split()`.

### 3. Pattern Detection

Even for whitelisted commands, dangerous patterns are blocked:
- Command substitution: `$(...)`, `` `...` ``
- Shell operators: `;`, `|`, `&&`, `||`
- Redirection: `>`, `<`, `>>`, `<<`
- Path traversal: `../`, `..\\`
- Home directory expansion: `~/`

### 4. User Approval System

For cases where dangerous commands need to be executed, users can provide an approval callback:

```python
from konseho.tools.shell_ops import shell_run, terminal_approval_callback

# Use the built-in terminal approval
result = shell_run("rm -rf /tmp/test", approval_callback=terminal_approval_callback)

# Or provide a custom approval function
def my_approval(command: str, error_msg: str) -> bool:
    # Custom logic to approve/reject commands
    return user_confirms(command)

result = shell_run("dangerous command", approval_callback=my_approval)
```

When a dangerous command is approved:
- The user is warned about the risks
- The command is logged
- The result includes `"approved": True`

### 5. Extending the Whitelist

You can programmatically manage the whitelist:

```python
from konseho.tools.shell_ops import add_allowed_commands, remove_allowed_commands, get_allowed_commands

# Add new commands to whitelist
add_allowed_commands("docker", "kubectl", "terraform")

# Remove commands from whitelist
remove_allowed_commands("rm")  # Make rm unavailable

# Get current whitelist
allowed = get_allowed_commands()
```

## Safe Alternatives

### Pipeline Execution

Instead of using shell pipes, use the safe pipeline function:

```python
from konseho.tools.shell_ops import execute_piped_commands

# Instead of: "echo test | grep test"
result = execute_piped_commands(["echo test", "grep test"])
```

### Bypass for Trusted Code

For internally generated commands that you trust completely:

```python
# Only use this for programmatically generated commands!
result = shell_run(trusted_command, allow_unsafe=True)
```

⚠️ **WARNING**: Never use `allow_unsafe=True` with user input!

## Best Practices

1. **Never disable validation for user input** - Always validate commands from users
2. **Use the whitelist** - Add safe commands to the whitelist rather than bypassing validation
3. **Log dangerous operations** - The approval system logs all approved dangerous commands
4. **Prefer specific commands** - Use specific tools rather than shell built-ins when possible
5. **Avoid shell features** - Use Python's built-in functions instead of shell commands where possible

## Example Usage

```python
from konseho.tools.shell_ops import shell_run, terminal_approval_callback

# Safe command - executes immediately
result = shell_run("git status")

# Dangerous command - blocked
result = shell_run("rm -rf /")
# Returns: {"error": "Command 'rm' is not in the allowed command list", ...}

# Dangerous command with approval
result = shell_run("curl https://example.com", approval_callback=terminal_approval_callback)
# User sees warning and must approve

# Add curl to whitelist for future use
from konseho.tools.shell_ops import add_allowed_commands
add_allowed_commands("curl")

# Now curl works without approval
result = shell_run("curl https://example.com")
```

## Security Considerations

Even with these protections:
1. Be careful about which commands you add to the whitelist
2. Review approval callbacks to ensure they properly validate requests
3. Monitor logs for approved dangerous commands
4. Consider the principle of least privilege - only allow what's necessary
5. Regularly review and update the whitelist based on actual needs