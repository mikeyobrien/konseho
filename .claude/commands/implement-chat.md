# Implement Terminal Chat Interface

Create an interactive terminal interface for council interactions.

## TDD Approach:

### 1. Write Tests First
```python
# tests/unit/test_chat.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from io import StringIO

@pytest.mark.asyncio
async def test_chat_initialization():
    """Chat initializes with council and context"""
    council = Mock()
    chat = CouncilChat(council)
    
    assert chat.council == council
    assert isinstance(chat.context, CouncilContext)
    assert chat.verbose == True
    assert chat.history == []

@pytest.mark.asyncio
async def test_command_parsing():
    """Chat correctly parses commands"""
    chat = CouncilChat(Mock())
    
    assert chat.parse_command("exit") == ("exit", None)
    assert chat.parse_command("help") == ("help", None)
    assert chat.parse_command("verbose off") == ("verbose", "off")
    assert chat.parse_command("Hello world") == ("query", "Hello world")

@pytest.mark.asyncio
async def test_event_display_formatting():
    """Events are formatted correctly for display"""
    chat = CouncilChat(Mock())
    output = StringIO()
    
    with patch('sys.stdout', output):
        event = CouncilEvent(
            type=EventType.STEP_STARTED,
            timestamp=time.time(),
            step_name="analyze"
        )
        chat.display_event(event)
    
    output_str = output.getvalue()
    assert "📍" in output_str
    assert "Starting analyze step" in output_str

@pytest.mark.asyncio
async def test_human_input_timeout():
    """Human input times out gracefully"""
    interface = HumanInterface()
    
    with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
        result = await interface.get_input("Test prompt", timeout=0.1)
        assert "No human input provided" in result
```

### 2. Research Terminal Best Practices
Explore how to handle async input in terminals:

- Look for Python async input handling patterns
- Research libraries like:
  - `asyncio` for async I/O
  - `rich` for enhanced terminal output
  - `prompt_toolkit` for advanced input handling
- Consider cross-platform compatibility

### 3. Run Tests (Should Fail)
```bash
pytest tests/unit/test_chat.py -v
```

### 4. Implement Chat Interface
Build features incrementally to pass tests.

## CouncilChat Class:
```python
class CouncilChat:
    def __init__(self, council: Council, verbose: bool = True):
        self.council = council
        self.context = CouncilContext()
        self.verbose = verbose
        self.history = []
```

## Core Features:

### 1. Main Chat Loop
- Async input handling
- Command parsing (exit, help, history, verbose)
- Stream execution with live updates
- Display final results with explanation

### 2. Event Display
Format events for terminal output:
```
📍 Starting analyze step...
   🤖 [SecurityScanner] working on: Scanning...
   💡 [Analyzer] proposed: Use parameterized queries...
   ⚔️  Debate round 1 in progress...
   ✓ Decision made via vote
✅ Council Decision: [final result]
```

### 3. Human Interaction
Special handling for human input:
- Clear visual indicators (🟡 borders)
- Context display before input
- Timeout countdown
- Input validation

### 4. Progress Indicators
- Step progress bars
- Parallel execution tracking
- Time elapsed per step
- Overall progress

## Commands:
- `exit` - Quit the chat
- `help` - Show available commands
- `history` - View past interactions
- `verbose` - Toggle detailed output
- `save` - Save conversation
- `load` - Load previous session

## Display Formatting:
- Use emojis for visual clarity
- Indent agent activities
- Color coding (if rich available)
- Truncate long outputs
- Show timestamps in verbose mode

## Error Display:
- Clear error messages
- Suggestions for fixes
- Option to retry
- Stack traces in debug mode

## Integration:
- Works with any Council instance
- Preserves context between queries
- Supports custom event handlers
- Exports conversation logs

## Commit Your Work
```bash
# Quality checks
uv run black src tests
uv run ruff check src tests
uv run mypy src
uv run pytest tests/unit/test_chat.py

# Commit chat interface
git add konseho/interface/chat.py tests/unit/test_chat.py
git commit -m "feat(interface): implement terminal chat interface

- Add CouncilChat with async input handling
- Implement real-time event display with formatting
- Support command parsing (exit, help, history, verbose)
- Include progress indicators for parallel execution
- Add human interaction with visual indicators
- Ensure cross-platform terminal compatibility"
```

**UX Note**: Test the interface manually to ensure it feels responsive and provides clear feedback during long operations.