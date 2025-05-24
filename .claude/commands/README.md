# Konseho Development Commands

This directory contains slash commands to guide the implementation of Konseho. Use these commands with Claude Code to systematically build the SDK.

## Available Commands

### Setup & Initialization
- `/init-phase` - Initialize project structure and dependencies

### Core Implementation
- `/implement-council` - Build the base Council class
- `/implement-steps` - Create Step classes (Debate, Parallel, Split)
- `/implement-context` - Build context management system
- `/implement-agents` - Create agent wrappers and human integration
- `/implement-execution` - Build async execution engine
- `/implement-chat` - Create terminal chat interface

### Examples & Testing
- `/create-examples` - Build example councils and agents
- `/write-tests` - Create comprehensive test suite

### Optimization & Debugging
- `/optimize-performance` - Performance optimization guide
- `/debug-council` - Debugging common issues

### Release
- `/release-checklist` - Pre-release verification steps

### Development Practices
- `/commit-guidelines` - Git commit best practices and conventions

## Suggested Workflow

1. Start with `/init-phase` to set up the project
2. Implement core classes in order:
   - `/implement-council`
   - `/implement-steps`
   - `/implement-context`
3. Add Strands integration:
   - `/implement-agents`
   - `/implement-execution`
4. Build the interface:
   - `/implement-chat`
5. Create examples and tests:
   - `/create-examples`
   - `/write-tests`
6. Optimize and debug:
   - `/optimize-performance`
   - `/debug-council`
7. Prepare for release:
   - `/release-checklist`

## Tips

- Each command contains detailed implementation guidance
- Follow the suggested workflow for best results
- Test continuously as you implement
- Refer to `docs/idea-honing.md` for design decisions
- Keep the <10 lines goal in mind for API design

## Quick Start Example

After implementation, users should be able to create a council like this:

```python
from konseho import Council, DebateStep
from my_agents import Agent1, Agent2, Agent3

council = Council([
    DebateStep("solve", [Agent1(), Agent2(), Agent3()])
])
result = council.execute("Solve this problem")
print(result.final_answer)
```