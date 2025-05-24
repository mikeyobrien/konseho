"""Event system for observability."""

from typing import Dict, Any, Callable, List
import asyncio
import logging

logger = logging.getLogger(__name__)


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