# Konseho Implementation Plan

## Project Overview
**Goal**: Build a Python SDK for creating multi-agent councils on top of Strands Agent SDK
**Target**: <10 lines of code to create a functional council
**Core Features**: Council creation, context sharing, terminal chat interface

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

#### 1.1 Project Setup
- [ ] Initialize Python project structure
- [ ] Set up pyproject.toml with dependencies (strands-agents, asyncio, etc.)
- [ ] Configure testing framework (pytest, pytest-asyncio)
- [ ] Set up linting and formatting (ruff, black)
- [ ] Create initial package structure:
  ```
  konseho/
  ├── __init__.py
  ├── core/
  │   ├── __init__.py
  │   ├── council.py
  │   ├── steps.py
  │   └── context.py
  ├── agents/
  │   ├── __init__.py
  │   ├── base.py
  │   └── human.py
  ├── execution/
  │   ├── __init__.py
  │   ├── executor.py
  │   └── events.py
  └── interface/
      ├── __init__.py
      └── chat.py
  ```

#### 1.2 Core Classes Implementation
**File**: `konseho/core/council.py`
- [ ] Implement base `Council` class
- [ ] Add step management and workflow control
- [ ] Implement error handling strategies
- [ ] Add event emission hooks

**File**: `konseho/core/steps.py`
- [ ] Implement `Step` base class
- [ ] Implement `DebateStep` with voting mechanisms
- [ ] Implement `ParallelStep` with domain mapping
- [ ] Implement `SplitStep` with dynamic work distribution
- [ ] Add step-specific event emission

**File**: `konseho/core/context.py`
- [ ] Implement `CouncilContext` with memory stores
- [ ] Add context windowing and summarization
- [ ] Implement `AgentContext` with access control
- [ ] Add context serialization/deserialization

### Phase 2: Strands Integration (Week 1-2)

#### 2.1 Agent Wrapper Implementation
**File**: `konseho/agents/base.py`
- [ ] Create `CouncilAgent` wrapper for Strands agents
- [ ] Implement context injection into agent prompts
- [ ] Add tool conversion/compatibility layer
- [ ] Implement agent cloning for SplitStep

#### 2.2 Execution Engine
**File**: `konseho/execution/executor.py`
- [ ] Implement `StepExecutor` with parallel execution
- [ ] Add `CouncilModerator` for workflow orchestration
- [ ] Implement debate rounds and voting protocols
- [ ] Add work distribution strategies

**File**: `konseho/execution/events.py`
- [ ] Define event types and `CouncilEvent` dataclass
- [ ] Implement event buffering for parallel execution
- [ ] Add event filtering and routing
- [ ] Create debug event recording

### Phase 3: Terminal Interface (Week 2)

#### 3.1 Chat Interface
**File**: `konseho/interface/chat.py`
- [ ] Implement `CouncilChat` base class
- [ ] Add real-time event display formatting
- [ ] Implement command parsing (help, history, etc.)
- [ ] Add progress bars for parallel execution

#### 3.2 Human Integration
**File**: `konseho/agents/human.py`
- [ ] Implement `HumanAgent` class
- [ ] Create `HumanInterface` with async input
- [ ] Add timeout handling and default responses
- [ ] Implement context display for human agents

### Phase 4: Examples & Testing (Week 2-3)

#### 4.1 Example Agents
**Directory**: `examples/agents/`
- [ ] Create basic example agents (Explorer, Planner, Coder)
- [ ] Implement domain-specific agents for demos
- [ ] Add configurable agent templates

#### 4.2 Example Councils
**Directory**: `examples/councils/`
- [ ] Simple debate council example
- [ ] Multi-step code council example
- [ ] Research council with parallel execution
- [ ] Human-in-the-loop council example

#### 4.3 Test Suite
**Directory**: `tests/`
- [ ] Unit tests for core classes
- [ ] Integration tests with mock Strands agents
- [ ] Async execution tests
- [ ] Context management tests
- [ ] Error handling tests

### Phase 5: Documentation & Polish (Week 3)

#### 5.1 Documentation
- [ ] README.md with quick start guide
- [ ] API documentation with examples
- [ ] Architecture decision records
- [ ] Contributing guidelines

#### 5.2 Developer Experience
- [ ] CLI tool for council creation
- [ ] Config file support (YAML/JSON)
- [ ] Better error messages and debugging
- [ ] Performance optimization

## Technical Decisions

### Dependencies
- **Required**: strands-agents, asyncio, typing-extensions
- **Development**: pytest, pytest-asyncio, ruff, black
- **Optional**: rich (for better terminal output), pydantic (for config)

### Python Version
- Target Python 3.10+ (for modern async features and type hints)

### Async Strategy
- Use async/await throughout for parallel execution
- Provide sync wrappers for simple use cases
- Handle event loops properly in terminal interface

### Testing Strategy
- Mock Strands agents for unit tests
- Real integration tests with simple agents
- Property-based testing for voting algorithms
- Benchmarks for parallel execution

## MVP Validation Checklist

### Core Requirements
- [ ] Council creation in <10 lines of code
- [ ] Context preserved across agent handoffs
- [ ] Terminal chat interface functional
- [ ] Measurable improvement over single agents

### P0 Features
- [ ] Basic error handling (halt strategy)
- [ ] Simple voting (majority)
- [ ] Sequential workflow
- [ ] Text-based terminal interface

### P1 Features (Post-MVP)
- [ ] Advanced error strategies (retry, fallback)
- [ ] Weighted voting and consensus
- [ ] Iterative workflows
- [ ] Rich terminal interface with colors
- [ ] Config file support
- [ ] Performance optimizations

## Success Metrics

### Technical
- [ ] All tests passing (>90% coverage)
- [ ] <10 lines for basic council
- [ ] <100ms overhead per step
- [ ] Handles 10+ agents gracefully

### User Experience  
- [ ] Clear documentation with examples
- [ ] Intuitive API design
- [ ] Helpful error messages
- [ ] Responsive terminal interface

## Risk Mitigation

### Technical Risks
1. **Strands API changes**: Abstract integration layer
2. **Async complexity**: Provide sync wrappers
3. **Context explosion**: Implement summarization
4. **Performance**: Profile and optimize hot paths

### Design Risks
1. **API complexity**: Start simple, extend gradually
2. **Debugging difficulty**: Rich event system
3. **Terminal UX**: Test with real users early

## Next Steps

1. Set up project repository and structure
2. Implement Phase 1 core classes
3. Create simple integration test
4. Iterate based on early testing

## Timeline

- **Week 1**: Core infrastructure + basic Strands integration
- **Week 2**: Terminal interface + human integration  
- **Week 3**: Examples, testing, documentation
- **Week 4**: Polish, optimization, release prep

Total estimated time: 4 weeks for MVP