# Debug Council Issues

Debugging guide for common council problems.

## Debug Mode:
```python
# Enable debug mode
council = Council(steps=[...], debug=True)

# Or via environment
export KONSEHO_DEBUG=1
```

## Common Issues:

### 1. Agents Not Responding
**Symptoms**: Execution hangs, no output
**Debug Steps**:
- Check event stream for agent_working events
- Verify agent initialization
- Add timeout to agent calls
- Check for infinite loops in agent logic

### 2. Context Not Sharing
**Symptoms**: Agents don't see previous results
**Debug Steps**:
- Print context at each step
- Verify context injection in prompts
- Check AgentContext permissions
- Ensure context isn't being overwritten

### 3. Parallel Execution Issues
**Symptoms**: Sequential execution, race conditions
**Debug Steps**:
- Log asyncio task creation
- Check for blocking I/O
- Verify gather() usage
- Monitor event ordering

### 4. Memory Growth
**Symptoms**: Increasing memory usage
**Debug Steps**:
- Profile with memory_profiler
- Check context.max_history
- Look for circular references
- Monitor message accumulation

### 5. Event Stream Problems
**Symptoms**: Missing events, wrong order
**Debug Steps**:
- Add event sequence numbers
- Log event emission points
- Check event buffer implementation
- Verify async event handlers

## Debug Tools:

### Event Logger:
```python
class DebugEventLogger:
    def __init__(self, log_file: str):
        self.log_file = log_file
    
    async def log_event(self, event: CouncilEvent):
        with open(self.log_file, 'a') as f:
            f.write(f"{event.timestamp}: {event.type} - {event.data}\n")
```

### Context Inspector:
```python
def inspect_context(context: CouncilContext):
    print(f"Shared Memory Keys: {context.shared_memory.keys()}")
    print(f"Step Results: {len(context.step_results)}")
    print(f"Message Count: {len(context.messages)}")
    print(f"Current Proposals: {context.proposals}")
```

### Execution Tracer:
```python
class ExecutionTracer:
    def trace_step(self, step: Step, phase: str):
        print(f"[TRACE] {step.name} - {phase} at {time.time()}")
```

## Debug Output:
When debug=True, expect:
- Step execution timing
- Agent call details
- Context snapshots
- Event emission logs
- Error stack traces
- Memory usage stats

## Interactive Debugging:
```python
# Add breakpoint in council execution
import pdb; pdb.set_trace()

# Or use async debugger
import aiodebug; aiodebug.trace()
```