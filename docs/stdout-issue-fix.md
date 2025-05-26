# Stdout Display Issue - Diagnosis and Fix

## Issue Description

After adding the OutputManager feature, agent outputs were no longer being displayed in the terminal during council execution. The agents were working correctly, but their responses weren't visible to users.

## Root Cause Analysis

### 1. Strands Default Callback Handler

The issue was caused by how Strands agents handle output by default:

- When creating a Strands `Agent` without specifying `callback_handler`, it defaults to `PrintingCallbackHandler`
- `PrintingCallbackHandler` prints directly to stdout as the agent generates responses
- This conflicts with our `AgentWrapper.work_on()` method which buffers stdout to prevent interleaved output

### 2. Callback Handler Behavior

```python
# Default behavior (causes double printing):
agent = Agent(model="...", system_prompt="...")
# callback_handler = PrintingCallbackHandler() # Default

# Fixed behavior (no default printing):
agent = Agent(model="...", system_prompt="...", callback_handler=None)
# callback_handler = null_callback_handler # No printing
```

### 3. The Conflict

Our `AgentWrapper` class:
1. Captures stdout to a buffer
2. Runs the agent (which by default prints to stdout)
3. Restores stdout
4. Prints the buffered output with agent name prefix

When Strands' `PrintingCallbackHandler` is active, it prints to our buffer, but since we're already handling the printing, this creates issues.

## Solution

The fix ensures all agents are created with `callback_handler=None` to disable Strands' default printing:

```python
# In create_agent() function:
agent_args = {
    'model': model,
    'tools': tools,
    # Always set callback_handler to prevent default PrintingCallbackHandler
    # which conflicts with our buffering in AgentWrapper
    'callback_handler': config.get('callback_handler', None)
}
```

This way:
- Strands doesn't print anything by default
- Our `AgentWrapper` handles all output display
- Agent names are properly prefixed
- Output is buffered to prevent interleaving in parallel execution

## Additional Improvements

We also added `sys.stdout.flush()` after printing to ensure output appears immediately:

```python
# In AgentWrapper.work_on():
if captured_output:
    print(f"\n[{self.name}]:")
    print(captured_output, end='')
    sys.stdout.flush()  # Ensure output is displayed immediately
```

## MCP Tools Consideration

MCP tools don't directly affect stdout handling, but agents with MCP tools still need the same callback handler fix to ensure proper output display.

## Testing

To verify the fix works:

1. Create agents without specifying callback_handler
2. Run them individually and in councils
3. Confirm output appears with proper agent name prefixes
4. Test with and without output saving enabled
5. Test with MCP tools

## Summary

The issue was a conflict between Strands' default output handling and our custom buffering system. By explicitly setting `callback_handler=None` for all agents, we ensure our output management system has full control over what gets displayed and when.