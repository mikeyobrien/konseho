"""Moderator assignment component for the Council system."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from konseho.protocols import IAgent, IStep
from konseho.agents.base import AgentWrapper
if TYPE_CHECKING:
    from konseho.core.steps import DebateStep
logger = logging.getLogger(__name__)


class ModeratorAssigner:
    """Handles assignment of moderators to debate steps."""

    def __init__(self, default_moderator: (IAgent | None)=None):
        """Initialize the ModeratorAssigner.

        Args:
            default_moderator: Default moderator to use if none specified
        """
        self.default_moderator = default_moderator
        self._moderator_pool: list[IAgent] = []
        self._current_index = 0

    def set_moderator_pool(self, agents: list[IAgent]) ->None:
        """Set the pool of agents that can act as moderators.

        Args:
            agents: List of agents to use as moderators
        """
        self._moderator_pool = agents
        self._current_index = 0

    def assign_moderators(self, steps: list[IStep]) ->None:
        """Assign moderators to all debate steps.

        Args:
            steps: List of steps to process
        """
        # Import here to avoid circular imports
        from konseho.core.steps import DebateStep
        # Filter and cast debate steps
        debate_steps: list[object] = []
        for step in steps:
            # Check if it's actually a DebateStep (not just IStep)
            if step.__class__.__name__ == 'DebateStep':
                debate_steps.append(step)
        if not debate_steps:
            logger.debug('No debate steps found, skipping moderator assignment'
                )
            return
        logger.info(f'Assigning moderators to {len(debate_steps)} debate steps'
            )
        for step_obj in debate_steps:
            # Cast to access moderator attribute
            debate_step = step_obj
            if not hasattr(debate_step, 'moderator'):
                continue
            if debate_step.moderator is None:
                if moderator := self._get_next_moderator():
                    # Convert IAgent to AgentWrapper if needed
                    from konseho.agents.base import AgentWrapper
                    if isinstance(moderator, AgentWrapper):
                        debate_step.moderator = moderator
                    else:
                        # Wrap IAgent in AgentWrapper
                        debate_step.moderator = AgentWrapper(agent=moderator, name=moderator.name)  # type: ignore[arg-type]
                    logger.debug(
                        f'Assigned {moderator.name} as moderator'
                        )
                else:
                    logger.warning('No moderator available')

    def _get_next_moderator(self) ->(IAgent | None):
        """Get the next available moderator.

        Returns:
            Next moderator from the pool, or default moderator
        """
        if self._moderator_pool:
            moderator = self._moderator_pool[self._current_index]
            self._current_index = (self._current_index + 1) % len(self.
                _moderator_pool)
            return moderator
        return self.default_moderator

    def assign_specific_moderator(self, step: 'DebateStep', moderator: IAgent
        ) ->None:
        """Assign a specific moderator to a debate step.

        Args:
            step: The debate step
            moderator: The moderator to assign
        """
        # Convert IAgent to AgentWrapper if needed
        if isinstance(moderator, AgentWrapper):
            step.moderator = moderator
        else:
            # Wrap IAgent in AgentWrapper
            step.moderator = AgentWrapper(agent=moderator, name=moderator.name)  # type: ignore[arg-type]
        logger.debug(f'Assigned {moderator.name} as moderator for {step.name}')
