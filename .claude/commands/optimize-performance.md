# Optimize Performance

Performance optimization checklist for Konseho.

## Profiling First:
1. Profile council execution with cProfile
2. Identify bottlenecks:
   - Context serialization
   - Event emission overhead
   - Parallel execution coordination
   - Message history management

## Optimization Areas:

### 1. Context Management
- Lazy loading of context data
- Compress large shared memory entries
- Use msgpack instead of JSON for speed
- Implement context diffing for updates
- Cache summarizations

### 2. Parallel Execution
- Use asyncio.create_task for true parallelism
- Batch event emissions
- Optimize work distribution algorithms
- Pool agent instances for SplitStep
- Minimize context copying

### 3. Event System
- Make event emission optional
- Batch events from parallel agents
- Use async queues for event handling
- Filter events at source
- Compress event data

### 4. Memory Usage
- Implement context windowing
- Garbage collect completed step data
- Use weakrefs where appropriate
- Stream large results
- Limit message history size

### 5. Startup Time
- Lazy import heavy dependencies
- Cache agent initialization
- Precompile regex patterns
- Use __slots__ for data classes

## Benchmarks to Run:
```python
# Benchmark council creation
start = time.time()
council = Council([...])
print(f"Creation: {time.time() - start}s")

# Benchmark execution
start = time.time()
result = await council.execute(task)
print(f"Execution: {time.time() - start}s")

# Measure overhead
direct_time = measure_direct_agent_call()
council_time = measure_council_call()
print(f"Overhead: {council_time - direct_time}s")
```

## Performance Targets:
- Council creation: <10ms
- Execution overhead: <100ms per step
- Memory per agent: <10MB
- Event emission: <1ms per event
- Context serialization: <50ms

## Optimization Flags:
```python
Council(
    steps=[...],
    optimize=True,  # Enable optimizations
    emit_events=False,  # Disable events
    compress_context=True,  # Compress large data
    cache_size=1000  # LRU cache size
)
```