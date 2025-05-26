"""Context management for sharing state between agents and steps."""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime


class Context:
    """Manages shared state and context flowing between agents and steps."""
    
    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """Initialize context with optional initial data."""
        self._data: Dict[str, Any] = initial_data or {}
        self._history: List[Dict[str, Any]] = []
        self._results: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {
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
    
    def add_result(self, step_name: str, result: Any) -> None:
        """Store a result from a step execution."""
        self._results[step_name] = result
        self._history.append({
            "action": "result",
            "step": step_name,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_results(self) -> Dict[str, Any]:
        """Get all stored results."""
        return self._results.copy()
    
    def get_summary(self) -> Dict[str, Any]:
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
            "recent_results": self._serialize_data(dict(list(self._results.items())[-3:]))  # Last 3 results
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
        elif isinstance(data, list):
            return [self._serialize_data(item) for item in data]
        elif isinstance(data, tuple):
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