# Commit Guidelines for Konseho

Follow these guidelines for all commits to maintain a clean, understandable git history.

## Commit Message Format

Use Conventional Commits format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to build process or auxiliary tools

## Scopes
- `core`: Council, Steps, Context classes
- `agents`: Agent wrappers and human integration
- `execution`: Execution engine and events
- `interface`: Terminal chat interface
- `examples`: Example code
- `tests`: Test suite

## Best Practices

### 1. Atomic Commits
Each commit should represent one logical change:
```bash
# GOOD: One feature, one commit
git commit -m "feat(core): add retry logic to error handling"

# BAD: Multiple unrelated changes
git commit -m "add retry logic and fix typos and update docs"
```

### 2. Test with Implementation
Always commit tests WITH the code they test:
```bash
git add src/konseho/core/council.py tests/unit/test_council.py
git commit -m "feat(core): implement Council class with tests"
```

### 3. Run Quality Checks Before Committing
```bash
# Create a pre-commit alias
alias precommit='uv run black src tests && uv run ruff check src tests && uv run mypy src && uv run pytest'

# Use before every commit
precommit && git commit
```

### 4. Write Meaningful Messages
```bash
# GOOD: Explains what and why
git commit -m "feat(agents): add timeout handling to HumanAgent

- Implement configurable timeout for human input
- Fall back to default response on timeout
- Prevent blocking when human is unavailable"

# BAD: Vague and uninformative
git commit -m "update human agent"
```

### 5. Reference Issues
When fixing bugs or implementing features from issues:
```bash
git commit -m "fix(execution): prevent race condition in parallel steps

Fixes #123

- Add lock around shared context updates
- Ensure event ordering is preserved
- Include regression test"
```

## Commit Workflow

1. **Make changes following TDD**
   - Write test
   - Run test (fails)
   - Implement feature
   - Run test (passes)

2. **Check code quality**
   ```bash
   uv run black src tests
   uv run ruff check src tests
   uv run mypy src
   uv run pytest
   ```

3. **Stage related files**
   ```bash
   git add -p  # Review changes
   git status  # Verify staged files
   ```

4. **Commit with descriptive message**
   ```bash
   git commit  # Opens editor for detailed message
   ```

5. **Verify commit**
   ```bash
   git log --oneline -5  # Review recent commits
   git show  # Inspect last commit
   ```

## Common Commit Scenarios

### Feature Implementation
```bash
git commit -m "feat(core): implement ParallelStep for concurrent agent execution

- Support domain-based agent mapping
- Execute agents truly in parallel using asyncio.gather
- Merge results maintaining domain structure
- Include timing tests to verify parallelism

Implements design from docs/idea-honing.md"
```

### Bug Fix
```bash
git commit -m "fix(context): prevent message history overflow

- Implement sliding window with proper bounds checking
- Add summarization before truncating old messages
- Preserve context continuity across truncation

Fixes #45"
```

### Performance Improvement
```bash
git commit -m "perf(execution): optimize event emission for parallel steps

- Batch events from concurrent agents
- Reduce lock contention with thread-local buffers
- Improve performance by 40% in benchmarks"
```

### Documentation
```bash
git commit -m "docs: add architecture diagrams for council execution flow

- Illustrate step execution patterns
- Show context flow between agents
- Include examples for each step type"
```

## What NOT to Commit

- Commented-out code
- Debug print statements
- Personal TODO comments
- Large binary files
- Sensitive information (keys, passwords)
- Generated files (except when necessary)

## Fixing Mistakes

### Amend last commit
```bash
# Add forgotten file
git add forgotten_file.py
git commit --amend --no-edit

# Change commit message
git commit --amend -m "new message"
```

### Undo last commit (keep changes)
```bash
git reset --soft HEAD~1
```

### Split a commit
```bash
git reset HEAD~1
git add -p  # Stage selectively
git commit -m "first logical change"
git add .
git commit -m "second logical change"
```

Remember: Good commit history makes debugging, reviewing, and understanding the codebase much easier!