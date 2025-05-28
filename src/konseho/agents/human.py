"""Human-in-the-loop agent implementation."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from .base import AgentWrapper


class HumanAgent(AgentWrapper):
    """Agent that prompts for human input."""

    def __init__(self, name: str='human', input_handler: (Callable[[str],
        str] | None)=None):
        """Initialize human agent.

        Args:
            name: Name for the human agent
            input_handler: Optional custom input handler
        """
        self.name = name
        self.input_handler = input_handler or self._default_input_handler
        self._history = []

    async def work_on(self, task: str) ->str:
        """Prompt human for input."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self.input_handler, task)
        self._history.append({'task': task, 'response': response})
        return response

    def _default_input_handler(self, task: str) ->str:
        """Default console input handler."""
        print(f'\n[Human Input Required]\nTask: {task}\n')
        return input('Your response: ')
