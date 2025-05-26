# Council Output Saving

Konseho provides built-in functionality to save council execution outputs for auditing, debugging, and analysis purposes.

## Features

- **Automatic saving** of all council execution results
- **Dual format** output: JSON (structured) and TXT (human-readable)
- **Timestamped filenames** with task hash for uniqueness
- **Metadata inclusion** for context and configuration
- **Directory organization** by council name
- **Output management** utilities for listing and cleanup

## Usage

### 1. CLI Usage

Save outputs when running from command line:

```bash
# Save to default directory (council_outputs/)
python -m konseho --save -p "your query"

# Save to custom directory
python -m konseho --save --output-dir results -p "your query"

# With dynamic council
python -m konseho --dynamic --save --output-dir my_outputs
```

### 2. Programmatic Usage

Enable output saving when creating councils:

```python
from konseho import Council, DebateStep
from konseho.agents.base import AgentWrapper, create_agent

# Create council with output saving
council = Council(
    name="MyCouncil",
    agents=[agent1, agent2],
    save_outputs=True,           # Enable saving
    output_dir="council_outputs" # Optional custom directory
)

# Execute - outputs will be saved automatically
result = await council.execute("Your task here")
```

### 3. Dynamic Council with Output Saving

```python
from konseho.dynamic.builder import create_dynamic_council

# Create dynamic council with output saving
council = await create_dynamic_council(
    "Analyze this complex problem",
    save_outputs=True,
    output_dir="analysis_results"
)

result = await council.execute(query)
```

## Output Structure

### Directory Layout

```
output_dir/
├── council_name/
│   ├── 20240526_123456_a1b2c3d4.json  # Full structured data
│   ├── 20240526_123456_a1b2c3d4.txt   # Human-readable report
│   └── ...
└── another_council/
    └── ...
```

### JSON Output Format

```json
{
  "task": "The original task/query",
  "council_name": "CouncilName",
  "timestamp": "2024-05-26T12:34:56",
  "result": {
    "data": {...},
    "results": {
      "step_0": {...},
      "step_1": {...}
    },
    "metadata": {...}
  },
  "metadata": {
    "error_strategy": "halt",
    "workflow": "sequential",
    "num_steps": 2,
    "agents": ["Agent1", "Agent2"]
  }
}
```

### Text Output Format

```
COUNCIL EXECUTION REPORT
================================================================================
Council: CouncilName
Task: The original task/query
Timestamp: 2024-05-26 12:34:56
================================================================================

METADATA:
  error_strategy: halt
  workflow: sequential
  num_steps: 2
  agents: ['Agent1', 'Agent2']

STEP_0
----------------------------------------
[Agent1]:
Agent response content...

[Agent2]:
Agent response content...

Winner: Agent1
```

## Output Management

### Using OutputManager

```python
from konseho.core.output_manager import OutputManager

# Create manager
manager = OutputManager("council_outputs")

# List all outputs
outputs = manager.list_outputs()
for output in outputs:
    print(f"{output['council_name']} - {output['timestamp']}")
    print(f"Task: {output['task']}")
    print(f"File: {output['file']}")

# List outputs for specific council
outputs = manager.list_outputs(council_name="MyCouncil")

# Load a specific output
data = manager.load_output("path/to/output.json")

# Cleanup old outputs (older than 30 days)
manager.cleanup_old_outputs(days=30)
```

### Manual Output Saving

```python
# Save output manually after execution
if result:
    output_path = council.output_manager.save_formatted_output(
        task="Custom task description",
        result=result,
        council_name=council.name,
        metadata={"custom_field": "value"}
    )
    print(f"Output saved to: {output_path}")
```

## Best Practices

1. **Enable for Important Tasks**: Turn on output saving for critical operations, debugging, or when you need an audit trail.

2. **Custom Directories**: Use meaningful directory names for different projects or experiments.

3. **Regular Cleanup**: Implement a cleanup schedule to remove old outputs and save disk space.

4. **Metadata Enhancement**: Add custom metadata to provide additional context for future analysis.

5. **Review Text Outputs**: The human-readable `.txt` files are great for quick review without parsing JSON.

## Example: Complete Workflow

```python
import asyncio
from konseho import Council, Context
from konseho.agents.base import AgentWrapper, create_agent
from konseho.core.output_manager import OutputManager

async def main():
    # Create agents
    analyst = AgentWrapper(
        create_agent(name="Analyst", system_prompt="You analyze data."),
        name="Analyst"
    )
    
    reviewer = AgentWrapper(
        create_agent(name="Reviewer", system_prompt="You review analyses."),
        name="Reviewer"
    )
    
    # Create council with output saving
    council = Council(
        name="AnalysisCouncil",
        agents=[analyst, reviewer],
        save_outputs=True,
        output_dir="analysis_outputs"
    )
    
    # Execute task
    result = await council.execute("Analyze the impact of climate change")
    
    # Later, review outputs
    manager = OutputManager("analysis_outputs")
    outputs = manager.list_outputs("AnalysisCouncil")
    
    print(f"Found {len(outputs)} saved analyses")
    
    # Load and display most recent
    if outputs:
        latest = outputs[0]  # Already sorted by timestamp
        data = manager.load_output(latest['file'])
        print(f"Latest analysis: {data['task']}")
        print(f"Completed at: {data['timestamp']}")

asyncio.run(main())
```

## Configuration

The output saving system respects these environment variables:

- `KONSEHO_OUTPUT_DIR`: Default output directory (if not specified)
- `KONSEHO_OUTPUT_FORMAT`: Default format preference (json, txt, or both)
- `KONSEHO_OUTPUT_RETENTION_DAYS`: Auto-cleanup after N days

## Troubleshooting

1. **Permission Errors**: Ensure the output directory is writable by your user.

2. **Large Outputs**: Very long responses may be truncated in the text format but are always complete in JSON.

3. **Missing Outputs**: Check that `save_outputs=True` is set and the council execution completed successfully.

4. **Disk Space**: Monitor output directory size, especially for high-volume usage. Use the cleanup feature regularly.