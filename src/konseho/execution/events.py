"""Event system for observability."""

from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events emitted during council execution."""
    COUNCIL_STARTED = "council:start"
    COUNCIL_COMPLETED = "council:complete"
    COUNCIL_ERROR = "council:error"
    
    STEP_STARTED = "step:start"
    STEP_COMPLETED = "step:complete"
    STEP_ERROR = "step:error"
    
    PARALLEL_STARTED = "parallel:start"
    PARALLEL_COMPLETED = "parallel:complete"
    
    AGENT_STARTED = "agent:start"
    AGENT_COMPLETED = "agent:complete"
    AGENT_ERROR = "agent:error"
    
    DEBATE_STARTED = "debate:start"
    DEBATE_ROUND = "debate:round"
    PROPOSAL_MADE = "proposal:made"
    VOTING_STARTED = "voting:start"
    DECISION_MADE = "decision:made"
    DEBATE_COMPLETED = "debate:complete"
    
    SPLIT_STARTED = "split:start"
    SPLIT_ANALYSIS = "split:analysis"
    SPLIT_DISTRIBUTED = "split:distributed"
    SPLIT_COMPLETED = "split:complete"


@dataclass
class CouncilEvent:
    """Event data structure for council execution events."""
    type: EventType
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventEmitter:
    """Simple event emitter for council execution events."""
    
    def __init__(self):
        """Initialize event emitter."""
        self._listeners: Dict[str, List[Callable]] = {}
        self._async_listeners: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, handler: Callable) -> None:
        """Register an event handler."""
        if asyncio.iscoroutinefunction(handler):
            if event not in self._async_listeners:
                self._async_listeners[event] = []
            self._async_listeners[event].append(handler)
        else:
            if event not in self._listeners:
                self._listeners[event] = []
            self._listeners[event].append(handler)
    
    def off(self, event: str, handler: Callable) -> None:
        """Remove an event handler."""
        if event in self._listeners and handler in self._listeners[event]:
            self._listeners[event].remove(handler)
        if event in self._async_listeners and handler in self._async_listeners[event]:
            self._async_listeners[event].remove(handler)
    
    def emit(self, event: str, data: Any = None) -> None:
        """Emit an event to all listeners."""
        logger.debug(f"Event emitted: {event}", extra={"data": data})
        
        # Handle sync listeners
        if event in self._listeners:
            for handler in self._listeners[event]:
                try:
                    handler(event, data)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
        
        # Handle async listeners
        if event in self._async_listeners:
            # Create tasks for async handlers
            loop = asyncio.get_event_loop()
            for handler in self._async_listeners[event]:
                loop.create_task(self._call_async_handler(handler, event, data))
    
    async def _call_async_handler(self, handler: Callable, event: str, data: Any) -> None:
        """Call an async event handler."""
        try:
            await handler(event, data)
        except Exception as e:
            logger.error(f"Error in async event handler: {e}")