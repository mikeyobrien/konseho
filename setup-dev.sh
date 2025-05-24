#!/bin/bash
# Setup development environment for konseho

echo "Installing development dependencies..."
uv pip install -e ".[dev]"

echo "Development environment setup complete!"
echo "Run tests with: uv run pytest"
echo "Format code with: uv run black src tests"
echo "Lint code with: uv run ruff check src tests"