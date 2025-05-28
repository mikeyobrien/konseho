# Async Shell Execution

This document describes the async-compatible shell execution features added to prevent blocking during shell command approval prompts.

## Problem

The original `shell_run` function used a blocking `input()` call in the `terminal_approval_callback`, which would block the entire async event loop when agents tried to execute commands requiring approval. This caused steps to hang indefinitely.

## Solution

We've added async-compatible versions of the shell execution functions:

### 1. `async_shell_run()`

An async version of `shell_run` that properly handles both sync and async approval callbacks:

```python
from konseho.tools.shell_ops import async_shell_run

# With async approval callback
async def my_async_approval(command: str, error_msg: str) -> bool:
    # Can do async operations without blocking
    await asyncio.sleep(0.1)
    return True

result = await async_shell_run(
    "curl http://example.com",
    approval_callback=my_async_approval
)

# Also works with sync callbacks (runs in executor)
def my_sync_approval(command: str, error_msg: str) -> bool:
    return True

result = await async_shell_run(
    "curl http://example.com", 
    approval_callback=my_sync_approval
)
```

### 2. `async_terminal_approval_callback()`

An async version of the terminal approval callback that doesn't block:

```python
from konseho.tools.shell_ops import async_terminal_approval_callback

# Use in async context
result = await async_shell_run(
    "dangerous command",
    approval_callback=async_terminal_approval_callback
)
```

## Usage in Agents

When agents need to execute shell commands in an async context, they should use `async_shell_run`:

```python
class MyAgent:
    async def work_on(self, task: str) -> str:
        # Use async_shell_run to avoid blocking
        result = await async_shell_run(
            "git status",
            approval_callback=async_terminal_approval_callback
        )
        
        if result["returncode"] == 0:
            return f"Git status: {result['stdout']}"
        else:
            return f"Error: {result['error']}"
```

## Backward Compatibility

The original `shell_run` function remains unchanged for backward compatibility. However, it should not be used in async contexts with approval callbacks that might block.

## Security Considerations

All the same security features apply:
- Command allowlisting
- Pattern detection for dangerous commands
- Path traversal prevention
- User approval for dangerous commands

The async versions maintain the same security model while ensuring non-blocking execution.

## Testing

The implementation includes comprehensive tests demonstrating:
- Basic async execution
- Sync and async approval callbacks
- Rejection handling
- Non-blocking concurrent execution

See `tests/unit/test_shell_ops.py::TestAsyncShellOps` for examples.