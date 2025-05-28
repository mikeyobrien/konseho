"""Moderator assignment component for the Council system."""

import logging
from typing import TYPE_CHECKING

from konseho.protocols import IAgent, IStep

if TYPE_CHECKING:
    from konseho.core.steps import DebateStep

logger = logging.getLogger(__name__)


class ModeratorAssigner:
    """Handles assignment of moderators to debate steps."""

    def __init__(self, default_moderator: IAgent | None = None):
        """Initialize the ModeratorAssigner.

        Args:
            default_moderator: Default moderator to use if none specified
        """
        self.default_moderator = default_moderator
        self._moderator_pool: list[IAgent] = []
        self._current_index = 0

    def set_moderator_pool(self, agents: list[IAgent]) -> None:
        """Set the pool of agents that can act as moderators.

        Args:
            agents: List of agents to use as moderators
        """
        self._moderator_pool = agents
        self._current_index = 0

    def assign_moderators(self, steps: list[IStep]) -> None:
        """Assign moderators to all debate steps.

        Args:
            steps: List of steps to process
        """
        # Import here to avoid circular dependency
        from konseho.core.steps import DebateStep

        debate_steps = [step for step in steps if isinstance(step, DebateStep)]

        if not debate_steps:
            logger.debug("No debate steps found, skipping moderator assignment")
            return

        logger.info(f"Assigning moderators to {len(debate_steps)} debate steps")

        for step in debate_steps:
            if step.moderator is None:
                moderator = self._get_next_moderator()
                if moderator:
                    step.moderator = moderator
                    logger.debug(
                        f"Assigned {moderator.name} as moderator for {step.name}"
                    )
                else:
                    logger.warning(f"No moderator available for {step.name}")

    def _get_next_moderator(self) -> IAgent | None:
        """Get the next available moderator.

        Returns:
            Next moderator from the pool, or default moderator
        """
        if self._moderator_pool:
            # Round-robin through the moderator pool
            moderator = self._moderator_pool[self._current_index]
            self._current_index = (self._current_index + 1) % len(self._moderator_pool)
            return moderator

        return self.default_moderator

    def assign_specific_moderator(self, step: "DebateStep", moderator: IAgent) -> None:
        """Assign a specific moderator to a debate step.

        Args:
            step: The debate step
            moderator: The moderator to assign
        """
        step.moderator = moderator
        logger.debug(f"Assigned {moderator.name} as moderator for {step.name}")
