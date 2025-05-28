"""Context management for sharing state between agents and steps."""

import json
from datetime import datetime
from typing import Any


class Context:
    """Manages shared state and context flowing between agents and steps."""
    
    def __init__(self, initial_data: dict[str, Any] | None = None):
        """Initialize context with optional initial data."""
        self._data: dict[str, Any] = initial_data or {}
        self._history: list[dict[str, Any]] = []
        self._results: list[Any] = []  # Changed from dict to list
        self._metadata: dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    
    def add(self, key: str, value: Any) -> None:
        """Add or update a value in the context."""
        self._data[key] = value
        self._history.append({
            "action": "add",
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context."""
        return self._data.get(key, default)
    
    @property
    def results(self) -> list[Any]:
        """Get the results list (read-only property)."""
        return self._results
    
    def add_result(self, result: Any) -> None:
        """Store a result from a step execution."""
        self._results.append(result)
        self._history.append({
            "action": "result",
            "step_index": len(self._results) - 1,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_results(self) -> list[Any]:
        """Get all stored results."""
        import copy
        return copy.deepcopy(self._results)
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of the context state."""
        return {
            "data": self._data,
            "results": self._results,
            "metadata": self._metadata,
            "history_length": len(self._history)
        }
    
    def to_prompt_context(self, max_length: int = 2000) -> str:
        """Convert context to a string suitable for LLM prompts."""
        summary = {
            "current_data": self._serialize_data(self._data),
            "recent_results": self._serialize_data(self._results[-3:])  # Last 3 results
        }
        
        context_str = json.dumps(summary, indent=2)
        if len(context_str) > max_length:
            # Truncate if too long
            context_str = context_str[:max_length] + "..."
        
        return f"Current Context:\n{context_str}"
    
    def _serialize_data(self, data: Any) -> Any:
        """Recursively serialize data, converting non-serializable objects."""
        if isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        elif isinstance(data, list) or isinstance(data, tuple):
            return [self._serialize_data(item) for item in data]
        elif hasattr(data, '__dict__'):
            # Handle objects with __dict__
            return str(data)
        elif hasattr(data, 'value'):
            # Handle enums
            return data.value
        else:
            # Try to serialize, fall back to string representation
            try:
                json.dumps(data)
                return data
            except (TypeError, ValueError):
                return str(data)
    
    def clear(self) -> None:
        """Clear all context data."""
        self._data.clear()
        self._results.clear()
        self._history.append({
            "action": "clear",
            "timestamp": datetime.now().isoformat()
        })
    
    def update(self, data: dict[str, Any]) -> None:
        """Update context with multiple key-value pairs."""
        self._data.update(data)
        self._history.append({
            "action": "update",
            "keys": list(data.keys()),
            "timestamp": datetime.now().isoformat()
        })
    
    def to_dict(self) -> dict[str, Any]:
        """Export context as dictionary."""
        return self._data.copy()
    
    def get_size(self) -> int:
        """Get context size in bytes."""
        import sys
        # Calculate approximate size of all data
        total_size = sys.getsizeof(self._data)
        total_size += sys.getsizeof(self._results)
        total_size += sys.getsizeof(self._history)
        total_size += sys.getsizeof(self._metadata)
        return total_size
    
