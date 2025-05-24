# Create Example Councils

Build example councils demonstrating different patterns and use cases.

## 1. Simple Debate Example
`examples/councils/simple_debate.py`:
```python
from konseho import Council, DebateStep
from examples.agents import Optimist, Pessimist, Realist

# Three agents debate a solution
council = Council([
    DebateStep("analyze", [Optimist(), Pessimist(), Realist()], rounds=2)
])

result = council.execute("Should we rewrite the system in Rust?")
print(result.explain())
```

## 2. Code Generation Council
`examples/councils/code_council.py`:
```python
from konseho import Council, ParallelStep, DebateStep, SplitStep

council = Council([
    # Parallel exploration
    ParallelStep("explore", {
        "code": CodeExplorer(),
        "tests": TestAnalyzer(),
        "docs": DocReader()
    }),
    
    # Design debate
    DebateStep("design", [Architect(), SecurityExpert(), Pragmatist()]),
    
    # Split implementation by files
    SplitStep("implement", Coder(), split_by="files"),
    
    # Review
    Step("review", Reviewer())
])
```

## 3. Research Council
`examples/councils/research_council.py`:
```python
# Parallel research with synthesis
council = Council([
    ParallelStep("research", {
        "academic": AcademicResearcher(),
        "industry": IndustryAnalyst(),
        "trends": TrendScout()
    }),
    DebateStep("synthesize", [Synthesizer(), Critic()]),
    Step("report", ReportWriter())
])
```

## 4. Human Review Council
`examples/councils/human_review.py`:
```python
# Human-in-the-loop approval
council = Council([
    DebateStep("propose", [IdeaGenerator(), Innovator()]),
    Step("human_review", HumanAgent(role="reviewer")),
    SplitStep("implement", Builder(), split_by="approved_items"),
    Step("human_validate", HumanAgent(role="validator"))
])
```

## 5. Debug Council
`examples/councils/debug_council.py`:
```python
# Collaborative debugging
council = Council([
    ParallelStep("analyze", {
        "logs": LogAnalyzer(),
        "code": CodeTracer(),
        "state": StateInspector()
    }),
    DebateStep("diagnose", [BugHunter(), RootCauser()]),
    Step("fix", Fixer()),
    Step("verify", Tester())
])
```

## Example Agents to Create:
Each example needs simple mock agents that demonstrate the pattern without requiring real Strands agents:
- Return canned responses
- Show coordination flow
- Demonstrate context passing
- Emit appropriate events

## Commit Examples
```bash
# After creating all examples
uv run black examples/
uv run ruff check examples/

# Test that examples run
python examples/councils/simple_debate.py
python examples/councils/code_council.py

# Commit examples
git add examples/
git commit -m "docs: add example councils demonstrating usage patterns

- Add simple debate example (3 agents, 1 step)
- Add code generation council (multi-step workflow)
- Add research council (parallel execution)
- Add human review council (human-in-the-loop)
- Add debug council (collaborative debugging)
- Include mock agents for demonstration
- Each example is runnable and self-contained"
```

**Important**: Examples should be the simplest possible code that demonstrates each pattern. They serve as both documentation and integration tests.