"""Mock agents and test utilities for Konseho tests."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class MockStrandsAgent:
    """Mock Strands agent for testing."""
    
    def __init__(self, name: str, response: str = "Mock response", delay: float = 0.0):
        self.name = name
        self.response = response
        self.delay = delay
        self.call_count = 0
        self.call_history: list[str] = []
    
    def __call__(self, prompt: str) -> 'MockResult':
        """Simulate Strands agent call."""
        self.call_count += 1
        self.call_history.append(prompt)
        
        if self.delay > 0:
            import time
            time.sleep(self.delay)
        
        return MockResult(message=f"{self.response} (call {self.call_count})")


@dataclass
class MockResult:
    """Mock result object that mimics Strands agent response."""
    message: str


class MockAgent:
    """Async mock agent for testing."""
    
    def __init__(
        self,
        name: str,
        response: str = "Mock response",
        delay: float = 0.0,
        fail_after: int | None = None,
        error_message: str = "Mock error"
    ):
        self.name = name
        self.response = response
        self.delay = delay
        self.fail_after = fail_after
        self.error_message = error_message
        self.call_count = 0
        self.call_history: list[str] = []
    
    async def __call__(self, prompt: str) -> str:
        """Async mock agent call."""
        self.call_count += 1
        self.call_history.append(prompt)
        
        if self.fail_after and self.call_count >= self.fail_after:
            raise Exception(self.error_message)
        
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        
        return f"{self.response} (call {self.call_count})"


@dataclass
class CouncilEvent:
    """Event data structure for testing."""
    event_type: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class EventCollector:
    """Collects events for testing."""
    
    def __init__(self):
        self.events: list[CouncilEvent] = []
        self.event_counts: dict[str, int] = {}
    
    def collect(self, event_type: str, data: dict[str, Any]) -> None:
        """Collect an event."""
        self.events.append(CouncilEvent(event_type, data))
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
    
    async def async_collect(self, event_type: str, data: dict[str, Any]) -> None:
        """Async event collection."""
        self.collect(event_type, data)
    
    def get_events_by_type(self, event_type: str) -> list[CouncilEvent]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.event_type == event_type]
    
    def clear(self) -> None:
        """Clear all collected events."""
        self.events.clear()
        self.event_counts.clear()
    
    def has_event(self, event_type: str) -> bool:
        """Check if an event type was emitted."""
        return event_type in self.event_counts
    
    def get_event_sequence(self) -> list[str]:
        """Get the sequence of event types."""
        return [e.event_type for e in self.events]