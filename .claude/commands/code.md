Analyze and implement the requested changes: $ARGUMENTS.

Follow the explore-plan-code-commit workflow:

## 1. EXPLORE
- Use `gh issue view` to get the issue details if working on an issue
- Read relevant files, documentation, and existing code patterns
- Search the codebase thoroughly using grep/glob tools
- For complex problems, use subagents to explore specific areas
- Understand the full context before making changes

## 2. PLAN
- Think through the approach carefully before implementing
- Create a clear plan of what changes need to be made
- Consider edge cases and potential impacts
- Use the TodoWrite tool to break down complex tasks
- Optional: Document the plan in an issue or comment

## 3. CODE
- Implement the solution following the plan
- Follow existing code patterns and conventions
- Write tests alongside the implementation
- Iterate and refine based on test results
- Ensure code passes all quality checks:
  - Run tests: `uv run pytest`
  - Lint: `uv run ruff check src tests`
  - Type check: `uv run mypy src`
  - Format: `uv run black src tests`

## 4. COMMIT
- Create descriptive commit messages
- Reference issue numbers if applicable
- Update documentation if relevant
- Push and create a PR using `gh pr create`

Key principles:
- Be thorough in exploration before coding
- Have a clear plan before implementation
- Iterate against tests and quality checks
- Use subagents for complex explorations when needed
