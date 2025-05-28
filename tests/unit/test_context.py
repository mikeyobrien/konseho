"""Unit tests for Context management."""

import json
from datetime import datetime

from konseho import Context


class TestContext:
    """Tests for Context class."""
    
    def test_context_initialization_empty(self):
        """Test empty context initialization."""
        ctx = Context()
        assert ctx.get_results() == []
        assert ctx.get("nonexistent") is None
        assert isinstance(ctx._metadata, dict)
        assert "created_at" in ctx._metadata
        assert "version" in ctx._metadata
    
    def test_context_initialization_with_data(self):
        """Test context initialization with initial data."""
        initial = {"key1": "value1", "key2": 42}
        ctx = Context(initial)
        
        assert ctx.get("key1") == "value1"
        assert ctx.get("key2") == 42
        assert ctx._data == initial
    
    def test_context_add_and_get(self):
        """Test adding and retrieving values."""
        ctx = Context()
        
        # Add various types
        ctx.add("string", "hello")
        ctx.add("number", 123)
        ctx.add("list", [1, 2, 3])
        ctx.add("dict", {"nested": "value"})
        
        assert ctx.get("string") == "hello"
        assert ctx.get("number") == 123
        assert ctx.get("list") == [1, 2, 3]
        assert ctx.get("dict") == {"nested": "value"}
    
    def test_context_get_with_default(self):
        """Test getting values with default."""
        ctx = Context()
        
        assert ctx.get("missing") is None
        assert ctx.get("missing", "default") == "default"
        assert ctx.get("missing", []) == []
    
    def test_context_update_existing(self):
        """Test updating existing values."""
        ctx = Context({"key": "old"})
        
        assert ctx.get("key") == "old"
        ctx.add("key", "new")
        assert ctx.get("key") == "new"
    
    def test_context_history_tracking(self):
        """Test context tracks history of operations."""
        ctx = Context()
        
        assert len(ctx._history) == 0
        
        ctx.add("key1", "value1")
        ctx.add("key2", "value2")
        
        assert len(ctx._history) == 2
        assert ctx._history[0]["action"] == "add"
        assert ctx._history[0]["key"] == "key1"
        assert ctx._history[0]["value"] == "value1"
        assert "timestamp" in ctx._history[0]
    
    def test_context_add_result(self):
        """Test storing step results."""
        ctx = Context()
        
        ctx.add_result({"output": "result1", "status": "success"})
        ctx.add_result({"output": "result2", "status": "success"})
        
        results = ctx.get_results()
        assert len(results) == 2
        assert results[0]["output"] == "result1"
        assert results[1]["output"] == "result2"
        
        # Check history
        assert any(h["action"] == "result" for h in ctx._history)
    
    def test_context_get_summary(self):
        """Test getting context summary."""
        ctx = Context({"initial": "data"})
        ctx.add("runtime", "value")
        ctx.add_result("result1")
        
        summary = ctx.get_summary()
        
        assert "data" in summary
        assert "results" in summary
        assert "metadata" in summary
        assert "history_length" in summary
        
        assert summary["data"]["initial"] == "data"
        assert summary["data"]["runtime"] == "value"
        assert summary["results"][0] == "result1"
        assert summary["history_length"] == 2  # add + add_result
    
    def test_context_to_prompt_basic(self):
        """Test basic prompt context generation."""
        ctx = Context()
        ctx.add("task", "Analyze data")
        ctx.add("config", {"model": "gpt-4"})
        
        prompt = ctx.to_prompt_context()
        
        assert "Current Context:" in prompt
        assert "task" in prompt
        assert "Analyze data" in prompt
        assert "config" in prompt
        assert "model" in prompt
    
    def test_context_to_prompt_with_results(self):
        """Test prompt context includes recent results."""
        ctx = Context()
        
        # Add multiple results
        for i in range(5):
            ctx.add_result(f"result_{i}")
        
        prompt = ctx.to_prompt_context()
        
        # Should include last 3 results
        assert "result_2" in prompt
        assert "result_3" in prompt
        assert "result_4" in prompt
        
        # Should not include older results
        assert "result_0" not in prompt
        assert "result_1" not in prompt
    
    def test_context_to_prompt_truncation(self):
        """Test prompt context truncates if too long."""
        ctx = Context()
        
        # Add very large data
        large_data = {"key": "x" * 5000}
        ctx.add("large", large_data)
        
        prompt = ctx.to_prompt_context(max_length=1000)
        
        assert len(prompt) <= 1020  # 1000 + "Current Context:\n"
        assert "..." in prompt
    
    def test_context_clear(self):
        """Test clearing context."""
        ctx = Context({"initial": "data"})
        ctx.add("key", "value")
        ctx.add_result("result")
        
        # Verify data exists
        assert len(ctx._data) > 0
        assert len(ctx._results) > 0
        
        ctx.clear()
        
        # Verify cleared
        assert len(ctx._data) == 0
        assert len(ctx._results) == 0
        assert ctx.get("initial") is None
        assert ctx.get_results() == []
        
        # History should record clear
        assert ctx._history[-1]["action"] == "clear"
    
    def test_context_immutable_results(self):
        """Test get_results returns copy not reference."""
        ctx = Context()
        ctx.add_result({"data": "original"})
        
        results = ctx.get_results()
        results[0]["data"] = "modified"
        
        # Original should be unchanged
        assert ctx._results[0]["data"] == "original"
    
    def test_context_metadata(self):
        """Test context metadata."""
        ctx = Context()
        
        assert "created_at" in ctx._metadata
        assert "version" in ctx._metadata
        
        # Verify created_at is valid ISO format
        created_at = ctx._metadata["created_at"]
        parsed = datetime.fromisoformat(created_at)
        assert isinstance(parsed, datetime)
    
    def test_context_serialization(self):
        """Test context data can be serialized to JSON."""
        ctx = Context()
        ctx.add("string", "value")
        ctx.add("number", 42)
        ctx.add("list", [1, 2, 3])
        ctx.add_result({"output": "result"})
        
        summary = ctx.get_summary()
        
        # Should be JSON serializable
        json_str = json.dumps(summary)
        loaded = json.loads(json_str)
        
        assert loaded["data"]["string"] == "value"
        assert loaded["results"][0]["output"] == "result"