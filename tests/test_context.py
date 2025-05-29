"""Tests for context management."""

import pytest
from konseho import Context


def test_context_initialization():
    """Test context can be initialized with and without data."""
    # Empty context
    ctx = Context()
    assert ctx.get_results() == {}
    
    # Context with initial data
    ctx = Context({"key": "value"})
    assert ctx.get("key") == "value"


def test_context_add_and_get():
    """Test adding and retrieving values."""
    ctx = Context()
    ctx.add("test_key", "test_value")
    assert ctx.get("test_key") == "test_value"
    assert ctx.get("missing_key", "default") == "default"


def test_context_results():
    """Test storing and retrieving step results."""
    ctx = Context()
    ctx.add_result("step_1", {"output": "result1"})
    ctx.add_result("step_2", {"output": "result2"})
    
    results = ctx.get_results()
    assert len(results) == 2
    assert results["step_1"]["output"] == "result1"


def test_context_to_prompt():
    """Test context conversion to prompt string."""
    ctx = Context()
    ctx.add("task", "Test task")
    ctx.add_result("step_1", "First result")
    
    prompt = ctx.to_prompt_context()
    assert "Current Context:" in prompt
    assert "task" in prompt
    assert "Test task" in prompt