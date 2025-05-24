# Konseho MVP Development Prompt Plan

## Overview
This document provides a structured set of prompts to guide the implementation of Konseho from concept to MVP. Each prompt builds on the previous work to ensure systematic progress.

## Phase 1: Project Setup & Core Infrastructure

### Prompt 1.1: Initialize Project
```
Create the initial Python project structure for Konseho. Set up:
1. Project directory with the structure defined in implementation-plan.md
2. pyproject.toml with dependencies (strands-agents, asyncio, pytest, etc.)
3. Basic README.md with project description
4. .gitignore for Python projects
5. Pre-commit hooks for code quality (ruff, black)
```

### Prompt 1.2: Implement Core Council Class
```
Implement the base Council class in konseho/core/council.py following the design in idea-honing.md:
1. Constructor accepting steps and/or agents
2. execute() method that orchestrates step execution
3. Error handling with configurable strategies (halt/continue/retry)
4. Basic event emission hooks
Include comprehensive docstrings and type hints.
```

### Prompt 1.3: Implement Step Classes
```
Implement the step class hierarchy in konseho/core/steps.py:
1. Step base class with abstract execute method
2. DebateStep with proposal gathering, debate rounds, and voting
3. ParallelStep with domain-based agent mapping
4. SplitStep with dynamic work distribution
Ensure each step type can emit events and handle errors gracefully.
```

### Prompt 1.4: Implement Context Management
```
Implement the context system in konseho/core/context.py:
1. CouncilContext with shared memory, step results, and message history
2. Automatic summarization when context grows large
3. AgentContext with permission-based access control
4. Context serialization/deserialization for persistence
Include helper methods for common context operations.
```

## Phase 2: Strands Integration

### Prompt 2.1: Create Agent Wrapper
```
Implement the Strands agent wrapper in konseho/agents/base.py:
1. CouncilAgent class that wraps a Strands Agent
2. Context injection into agent prompts
3. Message history synchronization with Strands
4. Agent cloning for dynamic creation in SplitStep
Test with a mock Strands agent to ensure compatibility.
```

### Prompt 2.2: Build Execution Engine
```
Implement the execution engine in konseho/execution/executor.py:
1. StepExecutor with async parallel execution support
2. Work distribution strategies (by_domain, by_files, by_subtask)
3. Debate orchestration with critique and refinement rounds
4. Voting/consensus decision protocols
Include proper error handling and event emission throughout.
```

### Prompt 2.3: Implement Event System
```
Create the event system in konseho/execution/events.py:
1. EventType enum with all event types
2. CouncilEvent dataclass with timestamp and metadata
3. ParallelEventBuffer for ordering events from concurrent agents
4. Event filtering and routing mechanisms
5. Debug event recorder for troubleshooting
```

## Phase 3: Terminal Interface

### Prompt 3.1: Build Chat Interface
```
Implement the terminal chat interface in konseho/interface/chat.py:
1. CouncilChat class with async input handling
2. Real-time event display with formatted output
3. Command parsing (exit, help, history, verbose)
4. Progress indicators for parallel execution
5. Chat history management
Use basic print statements first, rich/colorama can be added later.
```

### Prompt 3.2: Add Human Agent Support
```
Implement human-in-the-loop functionality in konseho/agents/human.py:
1. HumanAgent class implementing the agent interface
2. HumanInterface with context display and input collection
3. Async input with configurable timeouts
4. Different human roles (reviewer, expert, tiebreaker)
5. Clear visual indicators when human input is needed
```

## Phase 4: Examples & Testing

### Prompt 4.1: Create Example Agents
```
Create example agents in examples/agents/:
1. SimpleAnalyzer - basic text analysis agent
2. CodeExplorer - searches and understands codebases
3. TaskPlanner - breaks down complex tasks
4. Coder - generates code solutions
5. Reviewer - critiques and improves proposals
Each should demonstrate different agent capabilities.
```

### Prompt 4.2: Build Example Councils
```
Create example councils in examples/councils/:
1. simple_debate.py - 3 agents debate a solution
2. code_council.py - multi-step code generation workflow
3. research_council.py - parallel research with synthesis
4. human_review.py - human-in-the-loop approval workflow
Each example should be runnable and demonstrate different patterns.
```

### Prompt 4.3: Implement Test Suite
```
Create comprehensive tests in tests/:
1. test_council.py - Council class unit tests
2. test_steps.py - All step types with mocked agents  
3. test_context.py - Context management and persistence
4. test_execution.py - Async execution and error handling
5. test_integration.py - End-to-end council execution
Aim for >90% code coverage with meaningful tests.
```

## Phase 5: Documentation & Polish

### Prompt 5.1: Write Documentation
```
Create user-facing documentation:
1. Update README.md with:
   - Clear value proposition
   - Installation instructions
   - Quick start example (<10 lines)
   - Link to full documentation
2. docs/tutorial.md - Step-by-step guide building a council
3. docs/api.md - Complete API reference
4. docs/examples.md - Explanation of all examples
```

### Prompt 5.2: Add Developer Experience
```
Implement developer-friendly features:
1. Helpful error messages with suggestions
2. Validation for common mistakes
3. Type stubs for better IDE support  
4. Debug mode with detailed logging
5. Performance profiling helpers
```

### Prompt 5.3: Create CLI Tool
```
Build a CLI tool for council interaction:
1. konseho run <council_file> - Run a council from file
2. konseho chat - Start interactive chat with default council
3. konseho create - Interactive council builder
4. konseho validate <council_file> - Validate council configuration
Include --verbose and --debug flags.
```

## Validation Prompts

### Prompt V.1: Verify Core Requirements
```
Create a validation script that confirms:
1. A functional council can be created in <10 lines
2. Context is preserved across agent handoffs
3. Terminal chat interface works properly
4. Parallel execution actually runs in parallel
5. Error handling works as designed
Document any issues found and fixes applied.
```

### Prompt V.2: Performance Testing
```
Create performance benchmarks:
1. Measure overhead of council vs direct Strands agent
2. Test scaling with 10, 20, 50 agents
3. Measure context growth over long conversations
4. Profile memory usage during parallel execution
5. Identify and optimize any bottlenecks
```

### Prompt V.3: User Experience Testing
```
Test the user experience:
1. Have someone unfamiliar with the project try the quick start
2. Run all examples and ensure they work as expected
3. Test error messages are helpful when things go wrong
4. Verify the terminal interface is responsive
5. Check that human-in-the-loop actually waits for input
Document feedback and improvements made.
```

## MVP Release Checklist

### Final Prompt: Prepare for Release
```
Prepare Konseho for initial release:
1. Ensure all tests pass
2. Update version in pyproject.toml
3. Write CHANGELOG.md with initial release notes
4. Create GitHub repository with proper structure
5. Set up GitHub Actions for CI/CD
6. Create initial GitHub release with installation instructions
7. Test pip install from GitHub
8. Create demo video/gif for README
```

## Tips for Using These Prompts

1. **Sequential Execution**: Follow prompts in order as they build on each other
2. **Test Continuously**: Run tests after each major prompt
3. **Iterate on Feedback**: Refine implementations based on test results
4. **Keep Design Docs Updated**: Update idea-honing.md if design changes
5. **Commit Frequently**: Make atomic commits for easy rollback

## Estimated Timeline

- Phase 1: 2-3 days (Core Infrastructure)
- Phase 2: 2-3 days (Strands Integration)  
- Phase 3: 1-2 days (Terminal Interface)
- Phase 4: 2-3 days (Examples & Testing)
- Phase 5: 1-2 days (Documentation & Polish)

**Total: 8-13 days of focused development**