# Python Modernization Scripts

This directory contains automated tools for modernizing Python codebases to use the latest Python 3.12+ features, idioms, and type annotations.

## 🚀 Quick Start

Run the complete modernization process:

```bash
./scripts/run_modernization.py src/
```

## 📁 Available Scripts

### `run_modernization.py` - Main Orchestrator
Runs the complete modernization workflow in phases:

```bash
# Full modernization
./scripts/run_modernization.py src/

# Dry run to see what would change
./scripts/run_modernization.py src/ --dry-run

# Verbose output
./scripts/run_modernization.py src/ -v

# Skip certain phases
./scripts/run_modernization.py src/ --skip-analysis --skip-validation
```

### `modernize_types.py` - Type System Modernization
Automatically updates type annotations to modern Python syntax:

```bash
# Analyze only
./scripts/modernize_types.py src/ --analyze-only

# Dry run
./scripts/modernize_types.py src/ --dry-run

# Apply changes
./scripts/modernize_types.py src/
```

**Features:**
- Converts `Optional[X]` → `X | None`
- Converts `List[X]` → `list[X]`
- Converts `Union[X, Y]` → `X | Y`
- Adds `__slots__` to classes
- Converts to f-strings
- Uses walrus operator where appropriate

### `check_type_completeness.py` - Type Coverage Analysis
Analyzes type annotation coverage:

```bash
# Check entire project
./scripts/check_type_completeness.py src/

# Check specific file
./scripts/check_type_completeness.py src/konseho/core/council.py

# Check multiple paths
./scripts/check_type_completeness.py src/ tests/
```

**Reports:**
- Function type coverage percentage
- Parameter type coverage percentage
- Lists of missing annotations
- Usage of `Any` type

### `validate_docstrings.py` - Docstring Validation
Ensures docstrings match type annotations:

```bash
# Validate project
./scripts/validate_docstrings.py src/

# Validate specific module
./scripts/validate_docstrings.py src/konseho/agents/
```

**Checks:**
- Parameter types in docstrings match annotations
- Return types match
- All parameters are documented
- Supports Google, NumPy, and Sphinx docstring styles

## 🔧 Manual Workflow

If you prefer to run steps manually:

```bash
# 1. Analyze current state
./scripts/check_type_completeness.py src/
./scripts/modernize_types.py src/ --analyze-only

# 2. Modernize types (dry run first)
./scripts/modernize_types.py src/ --dry-run
./scripts/modernize_types.py src/

# 3. Format code
black src/
ruff check src/ --fix

# 4. Type check
mypy src/

# 5. Validate docstrings
./scripts/validate_docstrings.py src/

# 6. Final report
./scripts/check_type_completeness.py src/
```

## 📊 Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/type-check.yml
name: Type Checking

on: [push, pull_request]

jobs:
  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install astor
      
      - name: Check type completeness
        run: ./scripts/check_type_completeness.py src/
      
      - name: Validate docstrings
        run: ./scripts/validate_docstrings.py src/
      
      - name: Run mypy
        run: mypy src/ --strict
```

## 🛠️ Requirements

The scripts require these dependencies:
- Python 3.12+
- `astor` (for AST manipulation)
- `click` (for CLI)
- Development dependencies from `pyproject.toml`

Install with:
```bash
pip install -e ".[dev]"
pip install astor click
```

## ⚠️ Important Notes

1. **Always commit your code before running modernization**
2. **Review changes carefully** - automated tools may occasionally make incorrect transformations
3. **Run tests after modernization** to ensure functionality is preserved
4. **Update your documentation** to reflect new type annotations

## 🎯 Goals

These scripts help achieve:
- 100% type annotation coverage
- Zero uses of `Any` type
- Modern Python 3.12+ syntax throughout
- Consistent code style
- Performance optimizations (via `__slots__`, etc.)
- Better IDE support and autocomplete
- Reduced runtime errors through static typing

## 🐛 Troubleshooting

If modernization fails:

1. **Syntax Errors**: The AST parser requires valid Python. Fix syntax errors first.
2. **Import Errors**: Ensure all dependencies are installed.
3. **Mypy Errors**: Some generated types may need manual adjustment.
4. **Test Failures**: Some runtime behavior may change (e.g., with `__slots__`).

For issues, check the verbose output:
```bash
./scripts/run_modernization.py src/ -v
```